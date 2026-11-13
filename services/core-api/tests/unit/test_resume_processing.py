import uuid

import pytest

from app.integrations.ai_client import AIServiceError
from app.modules.resumes import repository
from app.modules.resumes.models import ResumeJobStatus, ResumeParseJob
from app.modules.resumes.processing import JobRetryableError, process_job


class FakeAI:
    def __init__(self, result=None, error: Exception | None = None) -> None:
        self.result = result if result is not None else {"skills": ["Python"]}
        self.error = error
        self.calls: list[tuple[str, str | None]] = []

    def parse_resume(self, text: str, *, filename: str | None = None) -> dict:
        self.calls.append((text, filename))
        if self.error:
            raise self.error
        return self.result


def _make_job(db_session, storage, content: bytes = b"Jane Doe\nPython developer", ext=".txt"):
    job_id = uuid.uuid4()
    key = f"2026/11/{job_id}{ext}"
    storage.save(key, content)
    job = ResumeParseJob(
        id=job_id,
        original_filename=f"cv{ext}",
        content_type="text/plain",
        file_size=len(content),
        file_sha256="0" * 64,
        storage_key=key,
    )
    repository.add_job(db_session, job)
    db_session.commit()
    return job


def test_successful_job_stores_text_and_parsed_data(db_session, memory_storage) -> None:
    job = _make_job(db_session, memory_storage)
    ai = FakeAI()

    process_job(db_session, job.id, storage=memory_storage, ai_client=ai, max_attempts=4)

    db_session.refresh(job)
    assert job.status == ResumeJobStatus.COMPLETED
    assert job.parsed_data == {"skills": ["Python"]}
    assert job.extracted_text == "Jane Doe\nPython developer"
    assert job.attempts == 1
    assert job.completed_at is not None
    assert ai.calls == [("Jane Doe\nPython developer", "cv.txt")]


def test_extraction_failure_marks_job_failed_without_calling_ai(db_session, memory_storage) -> None:
    job = _make_job(db_session, memory_storage, content=b"   \n  ")
    ai = FakeAI()

    process_job(db_session, job.id, storage=memory_storage, ai_client=ai, max_attempts=4)

    db_session.refresh(job)
    assert job.status == ResumeJobStatus.FAILED
    assert "No extractable text" in job.error_message
    assert ai.calls == []


def test_missing_stored_file_marks_job_failed(db_session, memory_storage) -> None:
    job = _make_job(db_session, memory_storage)
    memory_storage.files.clear()

    process_job(db_session, job.id, storage=memory_storage, ai_client=FakeAI(), max_attempts=4)

    db_session.refresh(job)
    assert job.status == ResumeJobStatus.FAILED


def test_retryable_ai_error_requeues_job_and_raises(db_session, memory_storage) -> None:
    job = _make_job(db_session, memory_storage)
    ai = FakeAI(error=AIServiceError("down", retryable=True))

    with pytest.raises(JobRetryableError):
        process_job(db_session, job.id, storage=memory_storage, ai_client=ai, max_attempts=4)

    db_session.refresh(job)
    assert job.status == ResumeJobStatus.QUEUED
    assert job.error_message == "down"
    assert job.attempts == 1


def test_retryable_error_fails_job_once_attempts_are_exhausted(db_session, memory_storage) -> None:
    job = _make_job(db_session, memory_storage)
    ai = FakeAI(error=AIServiceError("down", retryable=True))

    process_job(db_session, job.id, storage=memory_storage, ai_client=ai, max_attempts=1)

    db_session.refresh(job)
    assert job.status == ResumeJobStatus.FAILED


def test_non_retryable_ai_error_fails_job_immediately(db_session, memory_storage) -> None:
    job = _make_job(db_session, memory_storage)
    ai = FakeAI(error=AIServiceError("bad request", retryable=False))

    process_job(db_session, job.id, storage=memory_storage, ai_client=ai, max_attempts=4)

    db_session.refresh(job)
    assert job.status == ResumeJobStatus.FAILED
    assert job.error_message == "bad request"


def test_unexpected_error_fails_job_with_generic_message(db_session, memory_storage) -> None:
    job = _make_job(db_session, memory_storage)
    ai = FakeAI(error=RuntimeError("secret internals"))

    process_job(db_session, job.id, storage=memory_storage, ai_client=ai, max_attempts=4)

    db_session.refresh(job)
    assert job.status == ResumeJobStatus.FAILED
    assert "secret internals" not in job.error_message


def test_job_that_is_not_queued_is_skipped(db_session, memory_storage) -> None:
    job = _make_job(db_session, memory_storage)
    ai = FakeAI()
    process_job(db_session, job.id, storage=memory_storage, ai_client=ai, max_attempts=4)

    process_job(db_session, job.id, storage=memory_storage, ai_client=ai, max_attempts=4)

    assert len(ai.calls) == 1
