import uuid

import pytest
from fastapi.testclient import TestClient

pytest.importorskip("celery")
pytest.importorskip("multipart")

from app.db.session import get_db  # noqa: E402
from app.main import create_app  # noqa: E402
from app.modules.resumes import service, tasks  # noqa: E402
from app.modules.resumes.processing import process_job  # noqa: E402


class FakeAI:
    def parse_resume(self, text: str, *, filename: str | None = None) -> dict:
        return {"meta": {"received_characters": len(text), "filename": filename}}


@pytest.fixture
def client(session_factory, memory_storage, monkeypatch):
    def run_inline(job_id, *, high_priority: bool) -> None:
        with session_factory() as db:
            process_job(db, job_id, storage=memory_storage, ai_client=FakeAI(), max_attempts=1)

    monkeypatch.setattr(service, "get_resume_storage", lambda: memory_storage)
    monkeypatch.setattr(tasks, "enqueue_parse_job", run_inline)

    application = create_app()

    def override_get_db():
        with session_factory() as session:
            yield session

    application.dependency_overrides[get_db] = override_get_db
    return TestClient(application)


def _txt(name: str = "cv.txt", content: bytes = b"Jane Doe\nPython developer"):
    return ("file", (name, content, "text/plain"))


def test_single_upload_runs_pipeline_and_job_can_be_fetched(client, memory_storage) -> None:
    response = client.post("/api/v1/resumes/parse", files=[_txt()])

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "completed"
    assert body["original_filename"] == "cv.txt"
    assert body["parsed_data"]["meta"] == {"received_characters": 25, "filename": "cv.txt"}
    assert len(memory_storage.files) == 1

    fetched = client.get(f"/api/v1/resumes/jobs/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "completed"


def test_unsupported_extension_is_rejected(client) -> None:
    response = client.post("/api/v1/resumes/parse", files=[_txt("cv.exe")])

    assert response.status_code == 415


def test_content_not_matching_extension_is_rejected(client) -> None:
    response = client.post(
        "/api/v1/resumes/parse",
        files=[("file", ("cv.pdf", b"this is not a pdf", "application/pdf"))],
    )

    assert response.status_code == 415


def test_empty_file_is_rejected(client) -> None:
    assert client.post("/api/v1/resumes/parse", files=[_txt(content=b"")]).status_code == 400


def test_bulk_upload_accepts_valid_files_and_reports_rejected_ones(client) -> None:
    response = client.post(
        "/api/v1/resumes/parse/bulk",
        files=[
            ("files", ("a.txt", b"Alice resume", "text/plain")),
            ("files", ("b.txt", b"Bob resume", "text/plain")),
            ("files", ("c.exe", b"MZ", "application/octet-stream")),
        ],
    )

    assert response.status_code == 202
    body = response.json()
    assert body["total"] == 2
    assert body["completed"] == 2
    assert body["status"] == "completed"
    assert [job["original_filename"] for job in body["jobs"]] == ["a.txt", "b.txt"]
    assert [item["filename"] for item in body["rejected"]] == ["c.exe"]

    fetched = client.get(f"/api/v1/resumes/batches/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["completed"] == 2


def test_bulk_upload_with_no_valid_files_returns_400(client) -> None:
    response = client.post(
        "/api/v1/resumes/parse/bulk",
        files=[("files", ("c.exe", b"MZ", "application/octet-stream"))],
    )

    assert response.status_code == 400


def test_enqueue_failure_returns_503_and_marks_job_failed(
    client, session_factory, monkeypatch
) -> None:
    def broken(job_id, *, high_priority: bool) -> None:
        raise ConnectionError("broker down")

    monkeypatch.setattr(tasks, "enqueue_parse_job", broken)

    response = client.post("/api/v1/resumes/parse", files=[_txt()])

    assert response.status_code == 503


def test_unknown_job_and_batch_return_404(client) -> None:
    assert client.get(f"/api/v1/resumes/jobs/{uuid.uuid4()}").status_code == 404
    assert client.get(f"/api/v1/resumes/batches/{uuid.uuid4()}").status_code == 404
