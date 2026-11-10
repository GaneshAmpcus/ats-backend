"""Sentence Transformers embeddings, loaded on first use."""

from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

from app.config import get_settings


@lru_cache(maxsize=1)
def get_embedding_model() -> HuggingFaceEmbeddings:
    """Build a reusable local embedding model from application settings."""
    settings = get_settings()
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model_name,
        model_kwargs={"device": settings.embedding_device},
        encode_kwargs={
            "normalize_embeddings": settings.embedding_normalize,
            "batch_size": settings.embedding_batch_size,
        },
    )
