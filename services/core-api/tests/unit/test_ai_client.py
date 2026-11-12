import httpx
import pytest

from app.integrations.ai_client import AIServiceClient, AIServiceError


def _client(handler, api_key: str | None = "secret") -> AIServiceClient:
    return AIServiceClient(
        base_url="http://ai.test",
        api_key=api_key,
        timeout_seconds=5,
        transport=httpx.MockTransport(handler),
    )


def test_parse_resume_sends_key_and_payload_and_returns_json() -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["key"] = request.headers["x-api-key"]
        seen["body"] = request.content
        return httpx.Response(200, json={"skills": ["Python"]})

    result = _client(handler).parse_resume("resume text", filename="cv.pdf")

    assert result == {"skills": ["Python"]}
    assert seen["url"] == "http://ai.test/api/v1/parse-resume"
    assert seen["key"] == "secret"
    assert b"resume text" in seen["body"] and b"cv.pdf" in seen["body"]


@pytest.mark.parametrize("status", [429, 500, 503])
def test_retryable_status_codes(status: int) -> None:
    with pytest.raises(AIServiceError) as exc_info:
        _client(lambda request: httpx.Response(status)).parse_resume("text")

    assert exc_info.value.retryable is True


@pytest.mark.parametrize("status", [400, 401, 422])
def test_client_errors_are_not_retryable(status: int) -> None:
    with pytest.raises(AIServiceError) as exc_info:
        _client(lambda request: httpx.Response(status)).parse_resume("text")

    assert exc_info.value.retryable is False


def test_connection_failure_is_retryable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    with pytest.raises(AIServiceError) as exc_info:
        _client(handler).parse_resume("text")

    assert exc_info.value.retryable is True


def test_timeout_is_retryable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow")

    with pytest.raises(AIServiceError) as exc_info:
        _client(handler).parse_resume("text")

    assert exc_info.value.retryable is True


def test_missing_api_key_is_not_retryable() -> None:
    with pytest.raises(AIServiceError) as exc_info:
        _client(lambda request: httpx.Response(200, json={}), api_key=None).parse_resume("text")

    assert exc_info.value.retryable is False


def test_non_object_json_is_rejected() -> None:
    with pytest.raises(AIServiceError):
        _client(lambda request: httpx.Response(200, json=["not", "an", "object"])).parse_resume("t")
