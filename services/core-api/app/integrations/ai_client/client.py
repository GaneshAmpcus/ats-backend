from typing import Any

import httpx

from app.core.config import get_settings

PARSE_RESUME_PATH = "/api/v1/parse-resume"


class AIServiceError(Exception):
    """Raised when the AI service call fails. `retryable` tells the worker whether to retry."""

    def __init__(self, message: str, *, retryable: bool) -> None:
        super().__init__(message)
        self.retryable = retryable


class AIServiceClient:
    def __init__(
        self,
        base_url: str,
        api_key: str | None,
        timeout_seconds: float,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._transport = transport

    def parse_resume(self, text: str, *, filename: str | None = None) -> dict[str, Any]:
        if not self._api_key:
            raise AIServiceError("AI service API key is not configured.", retryable=False)

        payload: dict[str, Any] = {"text": text}
        if filename:
            payload["filename"] = filename

        try:
            with httpx.Client(
                base_url=self._base_url,
                timeout=self._timeout,
                transport=self._transport,
            ) as client:
                response = client.post(
                    PARSE_RESUME_PATH,
                    json=payload,
                    headers={"X-API-Key": self._api_key},
                )
        except httpx.TimeoutException as exc:
            raise AIServiceError("AI service request timed out.", retryable=True) from exc
        except httpx.TransportError as exc:
            raise AIServiceError("AI service is unreachable.", retryable=True) from exc

        if response.status_code == 429 or response.status_code >= 500:
            raise AIServiceError(
                f"AI service returned status {response.status_code}.",
                retryable=True,
            )
        if response.status_code >= 400:
            raise AIServiceError(
                f"AI service rejected the request with status {response.status_code}.",
                retryable=False,
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise AIServiceError("AI service returned invalid JSON.", retryable=False) from exc
        if not isinstance(data, dict):
            raise AIServiceError("AI service returned an unexpected payload.", retryable=False)
        return data


def get_ai_client() -> AIServiceClient:
    settings = get_settings()
    api_key = settings.ai_service_api_key.get_secret_value() if settings.ai_service_api_key else None
    return AIServiceClient(
        base_url=settings.ai_service_url,
        api_key=api_key,
        timeout_seconds=settings.ai_service_timeout_seconds,
    )
