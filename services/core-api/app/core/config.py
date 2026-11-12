from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        extra="ignore",
    )

    app_name: str = "Core API"
    app_env: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    docs_enabled: bool | None = None
    cors_origins: list[str] = Field(default_factory=list)
    database_url: str = Field(
        default="postgresql+psycopg://localhost:5432/ats_platform",
        repr=False,
    )
    redis_url: str = Field(default="redis://localhost:6379/0", repr=False)
    celery_broker_url: str | None = Field(default=None, repr=False)
    celery_result_backend: str | None = Field(default=None, repr=False)
    celery_task_always_eager: bool | None = None

    # AI service integration.
    ai_service_url: str = "http://localhost:8001"
    ai_service_api_key: SecretStr | None = Field(default=None, repr=False)
    ai_service_timeout_seconds: float = Field(default=90.0, gt=0)

    # Resume upload and parsing pipeline.
    resume_storage_dir: Path = Path(__file__).resolve().parents[2] / "storage" / "resumes"
    resume_max_upload_mb: int = Field(default=10, ge=1)
    resume_max_batch_files: int = Field(default=50, ge=1)
    resume_max_pdf_pages: int = Field(default=50, ge=1)
    resume_max_text_chars: int = Field(default=100_000, ge=1000)
    resume_parse_max_retries: int = Field(default=3, ge=0)

    @property
    def task_broker_url(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def task_result_backend(self) -> str:
        if self.celery_result_backend:
            return self.celery_result_backend
        # Keep Celery results in a separate Redis database by default.
        return self.redis_url.rsplit("/", 1)[0] + "/1"

    @property
    def run_celery_tasks_eagerly(self) -> bool:
        if self.celery_task_always_eager is not None:
            return self.celery_task_always_eager
        return self.app_env != "production"

    @property
    def api_docs_enabled(self) -> bool:
        if self.docs_enabled is not None:
            return self.docs_enabled
        return self.app_env != "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
