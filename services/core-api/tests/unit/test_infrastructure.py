from uuid import UUID

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.core.config import Settings
from app.db.session import engine
from app.main import create_app


def test_settings_load_app_prefixed_environment(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("APP_LOG_LEVEL", "DEBUG")

    assert Settings(_env_file=None).log_level == "DEBUG"


def test_database_engine_uses_postgresql_psycopg() -> None:
    assert engine.url.drivername == "postgresql+psycopg"


def test_docs_are_enabled_by_default_outside_production() -> None:
    settings = Settings(_env_file=None, app_env="development")

    assert settings.api_docs_enabled is True
    assert TestClient(create_app(settings)).get("/docs").status_code == 200


def test_docs_are_disabled_by_default_in_production() -> None:
    settings = Settings(_env_file=None, app_env="production")

    assert settings.api_docs_enabled is False
    assert TestClient(create_app(settings)).get("/docs").status_code == 404


def test_docs_can_be_overridden_by_environment_setting() -> None:
    settings = Settings(_env_file=None, app_env="production", docs_enabled=True)

    assert settings.api_docs_enabled is True


def test_cors_is_configured_from_settings() -> None:
    settings = Settings(
        _env_file=None,
        cors_origins=["https://frontend.example"],
    )
    client = TestClient(create_app(settings))

    response = client.options(
        "/",
        headers={
            "Origin": "https://frontend.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://frontend.example"
    assert UUID(response.headers["x-request-id"])


def test_request_id_is_returned_for_http_requests() -> None:
    client = TestClient(create_app())

    response = client.get("/not-configured")

    assert response.status_code == 404
    assert UUID(response.headers["x-request-id"])


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
