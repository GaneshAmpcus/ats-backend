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


def test_parse_resume_returns_structured_model_result(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict = {}
    parsed = {
        "personal_info": {
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "phone": None,
            "location": None,
            "linkedin_url": None,
        },
        "summary": "Backend engineer.",
        "skills": ["Python", "FastAPI"],
        "total_experience_years": 6.0,
        "experience": [],
        "education": [],
    }

    class StructuredModel:
        def invoke(self, messages):
            captured["messages"] = messages
            return parsed

    class FakeLLM:
        def with_structured_output(self, schema):
            captured["schema"] = schema
            return StructuredModel()

    monkeypatch.setattr("app.api.v1.parse_resume.get_llm", lambda: FakeLLM())
    response = client.post(
        "/api/v1/parse-resume",
        json={"text": "Some resume text", "filename": "cv.pdf"},
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 200
    assert response.json() == parsed
    assert captured["schema"].__name__ == "ResumeParseResult"
    assert captured["messages"][-1].content.endswith("Some resume text\n</resume>")


def test_parse_resume_maps_model_failure_to_retryable_error(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    class BrokenLLM:
        def with_structured_output(self, schema):
            raise RuntimeError("provider detail")

    monkeypatch.setattr("app.api.v1.parse_resume.get_llm", lambda: BrokenLLM())
    response = client.post(
        "/api/v1/parse-resume",
        json={"text": "Some resume text"},
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "The AI service could not parse this resume. Please retry."
    }


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
