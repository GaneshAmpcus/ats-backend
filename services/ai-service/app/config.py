"""Application settings loaded from environment variables or a local .env file."""

from functools import lru_cache
import re

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "ATS AI Service"
    environment: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/ats"
    database_echo: bool = False
    ai_database_schema: str = "ai_service"

    ai_service_api_key: SecretStr | None = None

    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_device: str = "cpu"
    embedding_normalize: bool = True
    embedding_batch_size: int = Field(default=32, ge=1)

    groq_api_key: SecretStr | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    groq_temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    groq_max_tokens: int = Field(default=2048, ge=1)
    groq_timeout_seconds: float = Field(default=60.0, gt=0)

    @field_validator("ai_database_schema")
    @classmethod
    def validate_schema_name(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
            raise ValueError("AI_DATABASE_SCHEMA must be a valid PostgreSQL identifier")
        return value


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()
