"""Groq chat model factory."""

from functools import lru_cache

from langchain_groq import ChatGroq

from app.config import get_settings


@lru_cache(maxsize=1)
def get_llm() -> ChatGroq:
    """Return a reusable LangChain chat model configured for Groq."""
    settings = get_settings()
    if settings.groq_api_key is None or not settings.groq_api_key.get_secret_value():
        raise RuntimeError("GROQ_API_KEY must be set before using the LLM")
    return ChatGroq(
        api_key=settings.groq_api_key.get_secret_value(),
        model=settings.groq_model,
        temperature=settings.groq_temperature,
        max_tokens=settings.groq_max_tokens,
        timeout=settings.groq_timeout_seconds,
    )
