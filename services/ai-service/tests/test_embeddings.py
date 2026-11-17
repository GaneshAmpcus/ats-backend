import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import get_settings


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("AI_SERVICE_API_KEY", "test-key")
    get_settings.cache_clear()
    yield TestClient(app)
    get_settings.cache_clear()


def test_embeddings_preserve_order_and_return_model(client, monkeypatch):
    class Model:
        def embed_documents(self, texts):
            assert texts == ["Python", "Java"]
            return [[1.0, 0.0], [0.0, 1.0]]
    monkeypatch.setattr("app.api.v1.embed.get_embedding_model", lambda: Model())
    result = client.post("/api/v1/embeddings", json={"texts": ["Python", "Java"]}, headers={"X-API-Key": "test-key"})
    assert result.status_code == 200
    assert result.json() == {"model": get_settings().embedding_model_name, "dimensions": 2,
                             "embeddings": [[1.0, 0.0], [0.0, 1.0]]}


@pytest.mark.parametrize("texts", [[], [" "], ["x"] * 33, ["x" * 12001]])
def test_embedding_validation(client, texts):
    assert client.post("/api/v1/embeddings", json={"texts": texts}, headers={"X-API-Key": "test-key"}).status_code == 422


def test_embedding_requires_key(client):
    assert client.post("/api/v1/embeddings", json={"texts": ["Python"]}).status_code == 401


def test_model_unavailable_is_retryable_without_leaking_details(client, monkeypatch):
    def broken():
        raise RuntimeError("private download details")
    monkeypatch.setattr("app.api.v1.embed.get_embedding_model", broken)
    result = client.post("/api/v1/embeddings", json={"texts": ["Python"]}, headers={"X-API-Key": "test-key"})
    assert result.status_code == 503
    assert "private" not in result.text
