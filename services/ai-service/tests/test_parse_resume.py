import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("AI_SERVICE_API_KEY", "test-key")
    get_settings.cache_clear()
    yield TestClient(app)
    get_settings.cache_clear()


def test_parse_resume_returns_static_json(client: TestClient) -> None:
    response = client.post(
        "/api/v1/parse-resume",
        json={"text": "Some resume text", "filename": "cv.pdf"},
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["personal_info"]["full_name"] == "Jane Doe"
    assert body["skills"]
    assert body["meta"] == {"is_stub": True, "received_characters": 16, "filename": "cv.pdf"}


def test_parse_resume_requires_api_key(client: TestClient) -> None:
    response = client.post("/api/v1/parse-resume", json={"text": "Some resume text"})

    assert response.status_code == 401


def test_parse_resume_rejects_blank_text(client: TestClient) -> None:
    response = client.post(
        "/api/v1/parse-resume",
        json={"text": "   "},
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 422
