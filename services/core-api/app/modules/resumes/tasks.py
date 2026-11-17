from uuid import UUID

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.integrations.ai_client import get_ai_client
from app.integrations.storage import get_resume_storage
from app.modules.resumes.processing import JobRetryableError, process_job
from app.modules.resumes.embedding import EmbeddingRetryableError, process_embeddings
from app.modules.resumes.models import ResumeParseJob
from app.workers.celery_app import celery_app

# Single uploads use the priority queue so a large bulk import cannot delay them.
# Run the worker with: celery -A app.workers.celery_app worker -Q resume_priority,resume_bulk,resume_embeddings
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
        job = db.get(ResumeParseJob, UUID(job_id))
        if job and job.status == "completed" and job.embedding_status == "pending":
            try:
                enqueue_embedding_job(job.id)
            except Exception:
                # A broker outage must not turn a successful parse into a failure.
                db.refresh(job)
                if job.embedding_status == "pending":
                    job.embedding_status = "failed"
                    job.embedding_error = "The embedding job could not be queued."
                    db.commit()


def enqueue_parse_job(job_id: UUID, *, high_priority: bool) -> None:
    parse_resume_job.apply_async(
        args=[str(job_id)],
        queue=PRIORITY_QUEUE if high_priority else BULK_QUEUE,
    )


@celery_app.task(bind=True, name="resumes.embed_resume_job")
def embed_resume_job(self, job_id: str) -> None:
    settings = get_settings()
    with SessionLocal() as db:
        try:
            process_embeddings(db, UUID(job_id), ai_client=get_ai_client(),
                               expected_model=settings.resume_embedding_model,
                               max_attempts=settings.resume_embedding_max_retries + 1)
        except EmbeddingRetryableError as exc:
            raise self.retry(exc=exc, countdown=10 * (2**self.request.retries),
                             max_retries=settings.resume_embedding_max_retries)


def enqueue_embedding_job(job_id: UUID) -> None:
    embed_resume_job.apply_async(args=[str(job_id)], queue="resume_embeddings")
