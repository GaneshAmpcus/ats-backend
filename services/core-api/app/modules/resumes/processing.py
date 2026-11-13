import logging
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.integrations.ai_client import AIServiceClient, AIServiceError
from app.integrations.storage import FileStorage, StorageError
from app.modules.resumes import repository
from app.modules.resumes.extraction import ExtractionError, extract_text

logger = logging.getLogger(__name__)


class JobRetryableError(Exception):
    """The job was returned to the queued state and the task should be retried."""


def process_job(
    db: Session,
    job_id: UUID,
    *,
    storage: FileStorage,
    ai_client: AIServiceClient,
    max_attempts: int,
) -> None:
    """Run one resume through: read file -> extract text -> AI service -> save result.

    Terminal failures are recorded on the job and do not raise. Only a retryable AI
    service failure raises JobRetryableError, after the job is set back to queued.
    """
    if not repository.claim_job(db, job_id):
        logger.info("Resume job %s is not queued; skipping.", job_id)
        return

    job = repository.get_job(db, job_id)
    if job is None:
        logger.error("Resume job %s disappeared after being claimed.", job_id)
        return

    settings = get_settings()
    try:
        data = storage.read(job.storage_key)
        text = extract_text(
            data,
            Path(job.storage_key).suffix,
            max_pdf_pages=settings.resume_max_pdf_pages,
            max_chars=settings.resume_max_text_chars,
        )
        job.extracted_text = text
        parsed = ai_client.parse_resume(text, filename=job.original_filename)
    except ExtractionError as exc:
        repository.mark_failed(db, job, str(exc))
    except StorageError:
        logger.exception("Could not read stored file for resume job %s", job_id)
        repository.mark_failed(db, job, "The uploaded file could not be read from storage.")
    except AIServiceError as exc:
        if exc.retryable and job.attempts < max_attempts:
            logger.warning(
                "Resume job %s failed (attempt %s/%s): %s", job_id, job.attempts, max_attempts, exc
            )
            repository.requeue(db, job, str(exc))
            raise JobRetryableError(str(exc)) from exc
        logger.error("Resume job %s failed permanently: %s", job_id, exc)
        repository.mark_failed(db, job, str(exc))
    except Exception:
        logger.exception("Unexpected error while processing resume job %s", job_id)
        repository.mark_failed(db, job, "An unexpected error occurred while processing the resume.")
    else:
        repository.mark_completed(db, job, parsed)
