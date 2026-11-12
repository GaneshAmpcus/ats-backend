from uuid import UUID

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.integrations.ai_client import get_ai_client
from app.integrations.storage import get_resume_storage
from app.modules.resumes.processing import JobRetryableError, process_job
from app.workers.celery_app import celery_app

# Single uploads use the priority queue so a large bulk import cannot delay them.
# Run the worker with: celery -A app.workers.celery_app worker -Q resume_priority,resume_bulk
PRIORITY_QUEUE = "resume_priority"
BULK_QUEUE = "resume_bulk"
RETRY_BACKOFF_SECONDS = 10


@celery_app.task(bind=True, name="resumes.parse_resume_job")
def parse_resume_job(self, job_id: str) -> None:
    settings = get_settings()
    max_retries = settings.resume_parse_max_retries

    with SessionLocal() as db:
        try:
            process_job(
                db,
                UUID(job_id),
                storage=get_resume_storage(),
                ai_client=get_ai_client(),
                max_attempts=max_retries + 1,
            )
        except JobRetryableError as exc:
            countdown = RETRY_BACKOFF_SECONDS * (2**self.request.retries)
            raise self.retry(exc=exc, countdown=countdown, max_retries=max_retries)


def enqueue_parse_job(job_id: UUID, *, high_priority: bool) -> None:
    parse_resume_job.apply_async(
        args=[str(job_id)],
        queue=PRIORITY_QUEUE if high_priority else BULK_QUEUE,
    )
