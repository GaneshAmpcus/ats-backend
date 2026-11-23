"""Shared pytest fixtures for the ai-service test suite."""
import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.llm.client import get_llm
from app.main import app


@pytest.fixture(autouse=True)
def _clear_lru_caches():
    """Clear all lru_cache-wrapped singletons before and after every test.

    This prevents a real ChatGroq instance (populated from the .env file)
    from persisting across tests that monkeypatch get_llm or get_settings.
    Without this, the first test to trigger `get_llm()` caches the real
    Groq client, and subsequent monkeypatches of `get_llm` are ignored
    because the endpoint calls `get_llm()` through the cached reference.
    """
    get_settings.cache_clear()
    get_llm.cache_clear()
    yield
    get_settings.cache_clear()
    get_llm.cache_clear()


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("AI_SERVICE_API_KEY", "test-key")
    # Ensure no real Groq key leaks into tests from the .env file.
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key-not-real")
    get_settings.cache_clear()
    yield TestClient(app)
    get_settings.cache_clear()
