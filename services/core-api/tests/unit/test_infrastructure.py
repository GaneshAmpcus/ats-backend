from uuid import UUID

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.core.config import Settings
from app.db.session import engine
from app.main import create_app


def test_settings_load_app_prefixed_environment(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("APP_LOG_LEVEL", "DEBUG")

    assert Settings().log_level == "DEBUG"


def test_database_engine_uses_postgresql_psycopg() -> None:
    assert engine.url.drivername == "postgresql+psycopg"


def test_request_id_is_returned_for_http_requests() -> None:
    client = TestClient(create_app())

    response = client.get("/not-configured")

    assert response.status_code == 404
    assert UUID(response.headers["x-request-id"])


def test_framework_docs_are_not_exposed_before_api_routes_exist() -> None:
    client = TestClient(create_app())

    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_unexpected_errors_return_a_generic_response() -> None:
    application = create_app()

    async def fail() -> None:
        raise RuntimeError("sensitive internal details")

    application.add_api_route("/_test/unhandled", fail, methods=["GET"])
    client = TestClient(application, raise_server_exceptions=False)

    response = client.get("/_test/unhandled")

    assert response.status_code == 500
    assert response.json() == {
        "error": "internal_server_error",
        "message": "An unexpected error occurred.",
    }
    assert "sensitive internal details" not in response.text
