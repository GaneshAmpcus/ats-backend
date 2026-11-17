import uuid

import pytest
from sqlalchemy import select

from app.integrations.ai_client import AIServiceError
from app.modules.resumes import repository
from app.modules.resumes.embedding import EmbeddingRetryableError, embedding_chunks, process_embeddings
from app.modules.resumes.models import ResumeChunkEmbedding, ResumeParseJob

MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class FakeAI:
    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def embed_texts(self, texts):
        self.calls.append(texts)
        if self.error:
            raise self.error
        return {"model": MODEL, "dimensions": 384, "embeddings": [[1.0] + [0.0] * 383 for _ in texts]}


@pytest.fixture
def job(db_session):
    result = ResumeParseJob(id=uuid.uuid4(), original_filename="cv.txt", content_type="text/plain",
                            file_size=10, file_sha256="0" * 64, storage_key="test.txt")
    repository.add_job(db_session, result)
    db_session.commit()
    repository.mark_completed(db_session, result, {
        "personal_info": {"full_name": "Jane", "email": "jane@example.com", "phone": "+91 9876543210"},
        "summary": "Python engineer. Contact jane@example.com +91 9876543210",
        "skills": ["Python", "SQL"], "experience": [{"company": "A", "description": "Built APIs"}],
    })
    return result


def run(db, job, ai, attempts=4):
    process_embeddings(db, job.id, ai_client=ai, expected_model=MODEL, max_attempts=attempts)


def test_embeddings_persist_without_contacts_and_duplicate_delivery_is_noop(db_session, job):
    original = job.parsed_data.copy()
    ai = FakeAI()
    run(db_session, job, ai)
    rows = db_session.scalars(select(ResumeChunkEmbedding)).all()
    assert len(rows) == job.embedding_count == 3
    assert job.embedding_status == "completed" and job.status == "completed"
    assert job.embedding_completed_at is not None
    assert job.parsed_data == original
    assert all(len(row.embedding) == 384 and row.embedding_model == MODEL for row in rows)
    assert all("jane@example.com" not in row.chunk_text and "9876543210" not in row.chunk_text for row in rows)
    run(db_session, job, ai)
    assert len(ai.calls) == 1
    # Explicit regeneration upserts the stable IDs rather than duplicating rows.
    ids = {row.chunk_id for row in rows}
    job.embedding_status = "pending"
    db_session.commit()
    run(db_session, job, ai)
    assert {r.chunk_id for r in db_session.scalars(select(ResumeChunkEmbedding))} == ids


def test_retry_and_exhaustion_preserve_parsed_result(db_session, job):
    ai = FakeAI(AIServiceError("unavailable", retryable=True))
    with pytest.raises(EmbeddingRetryableError):
        run(db_session, job, ai, attempts=2)
    assert job.embedding_status == "pending" and job.embedding_attempts == 1
    assert job.status == "completed" and job.parsed_data["skills"] == ["Python", "SQL"]
    run(db_session, job, ai, attempts=2)
    assert job.embedding_status == "failed" and job.embedding_attempts == 2
    assert db_session.scalars(select(ResumeChunkEmbedding)).all() == []


def test_retry_then_success(db_session, job):
    with pytest.raises(EmbeddingRetryableError):
        run(db_session, job, FakeAI(AIServiceError("timeout", retryable=True)))
    run(db_session, job, FakeAI())
    assert job.embedding_status == "completed" and job.embedding_attempts == 2
    assert job.embedding_error is None


@pytest.mark.parametrize("kind", ["model", "dimension", "nan", "count", "zero"])
def test_invalid_ai_vectors_never_persist(db_session, job, kind):
    class InvalidAI(FakeAI):
        def embed_texts(self, texts):
            result = super().embed_texts(texts)
            if kind == "model": result["model"] = "different-model"
            if kind == "dimension": result["dimensions"] = 12
            if kind == "nan": result["embeddings"][0][0] = float("nan")
            if kind == "count": result["embeddings"].pop()
            if kind == "zero": result["embeddings"][0] = [0.0] * 384
            return result
    run(db_session, job, InvalidAI())
    assert job.embedding_status == "failed" and job.status == "completed"
    assert db_session.scalars(select(ResumeChunkEmbedding)).all() == []


def test_long_chunks_are_stable_and_batched_atomically(db_session, job):
    repository.mark_completed(db_session, job, {"summary": "Software engineering " * 1600})
    chunks = embedding_chunks(job)
    assert len(chunks) > 32 and max(len(c["chunk_text"]) for c in chunks) <= 800
    assert chunks == embedding_chunks(job)
    class FailSecondBatch(FakeAI):
        def embed_texts(self, texts):
            if self.calls:
                raise AIServiceError("down", retryable=True)
            return super().embed_texts(texts)
    with pytest.raises(EmbeddingRetryableError):
        run(db_session, job, FailSecondBatch())
    assert db_session.scalars(select(ResumeChunkEmbedding)).all() == []
    run(db_session, job, FakeAI())
    assert job.embedding_count == len(chunks)


def test_no_meaningful_data_completes_with_zero_vectors(db_session, job):
    repository.mark_completed(db_session, job, {"personal_info": {"email": "jane@example.com"}})
    ai = FakeAI()
    run(db_session, job, ai)
    assert job.embedding_status == "completed" and job.embedding_count == 0
    assert not ai.calls


def test_parse_task_queues_embedding_and_broker_failure_preserves_parse(db_session, job, session_factory, monkeypatch):
    from app.modules.resumes import tasks
    monkeypatch.setattr(tasks, "SessionLocal", session_factory)
    monkeypatch.setattr(tasks, "process_job", lambda *a, **kw: None)
    called = []
    monkeypatch.setattr(tasks, "enqueue_embedding_job", lambda job_id: called.append(job_id))
    tasks.parse_resume_job.run(str(job.id))
    assert called == [job.id]
    def unavailable(job_id):
        raise ConnectionError("broker unavailable")
    monkeypatch.setattr(tasks, "enqueue_embedding_job", unavailable)
    tasks.parse_resume_job.run(str(job.id))
    db_session.refresh(job)
    assert job.status == "completed" and job.embedding_status == "failed"


def test_embedding_task_schedules_retry(db_session, job, session_factory, monkeypatch):
    from app.modules.resumes import tasks
    monkeypatch.setattr(tasks, "SessionLocal", session_factory)
    monkeypatch.setattr(tasks, "get_ai_client", lambda: FakeAI(AIServiceError("timeout", retryable=True)))
    captured = {}
    class Retried(Exception):
        pass
    def retry(**kwargs):
        captured.update(kwargs)
        return Retried()
    monkeypatch.setattr(tasks.embed_resume_job, "retry", retry)
    with pytest.raises(Retried):
        tasks.embed_resume_job.run(str(job.id))
    assert captured["countdown"] == 10
    db_session.refresh(job)
    assert job.embedding_status == "pending" and job.status == "completed"


@pytest.mark.parametrize("bulk", [False, True])
def test_upload_through_both_tasks_and_poll(session_factory, memory_storage, monkeypatch, bulk):
    from fastapi.testclient import TestClient
    from app.main import create_app
    from app.db.session import get_db
    from app.modules.resumes import service, tasks
    class PipelineAI(FakeAI):
        def parse_resume(self, text, *, filename=None):
            return {"skills": ["Python", "SQL"], "summary": text}
    monkeypatch.setattr(tasks, "SessionLocal", session_factory)
    monkeypatch.setattr(tasks, "get_ai_client", PipelineAI)
    monkeypatch.setattr(tasks, "get_resume_storage", lambda: memory_storage)
    monkeypatch.setattr(service, "get_resume_storage", lambda: memory_storage)
    monkeypatch.setattr(tasks, "enqueue_parse_job", lambda job_id, **kw: tasks.parse_resume_job.run(str(job_id)))
    monkeypatch.setattr(tasks, "enqueue_embedding_job", lambda job_id: tasks.embed_resume_job.run(str(job_id)))
    app = create_app()
    def database():
        with session_factory() as db:
            yield db
    app.dependency_overrides[get_db] = database
    with TestClient(app) as client:
        path = "/api/v1/resumes/parse" + ("/bulk" if bulk else "")
        field = "files" if bulk else "file"
        response = client.post(path, files=[(field, ("cv.txt", b"Python engineer", "text/plain"))])
        assert response.status_code == 202
        data = response.json()
        result = data["jobs"][0] if bulk else data
        polled = client.get(f"/api/v1/resumes/jobs/{result['id']}").json()
        assert polled["status"] == polled["embedding_status"] == "completed"
        assert polled["embedding_count"] == 2 and polled["embedding_attempts"] == 1
        assert polled["embedding_error"] is None
        with session_factory() as db:
            rows = db.scalars(select(ResumeChunkEmbedding)).all()
            assert len(rows) == polled["embedding_count"]
