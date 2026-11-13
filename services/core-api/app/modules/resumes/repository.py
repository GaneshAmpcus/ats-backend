from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.modules.resumes.models import ResumeBatch, ResumeJobStatus, ResumeParseJob


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_batch(db: Session, *, total_jobs: int) -> ResumeBatch:
    batch = ResumeBatch(total_jobs=total_jobs)
    db.add(batch)
    db.flush()
    return batch


def add_job(db: Session, job: ResumeParseJob) -> ResumeParseJob:
    db.add(job)
    db.flush()
    return job


def get_job(db: Session, job_id: UUID) -> ResumeParseJob | None:
    return db.get(ResumeParseJob, job_id)


def get_batch(db: Session, batch_id: UUID) -> ResumeBatch | None:
    statement = (
        select(ResumeBatch)
        .where(ResumeBatch.id == batch_id)
        .options(selectinload(ResumeBatch.jobs))
        .execution_options(populate_existing=True)
    )
    return db.scalars(statement).first()


def claim_job(db: Session, job_id: UUID) -> bool:
    """Atomically move a queued job to processing. Returns False if another worker owns it."""
    result = db.execute(
        update(ResumeParseJob)
        .where(
            ResumeParseJob.id == job_id,
            ResumeParseJob.status == ResumeJobStatus.QUEUED,
        )
        .values(
            status=ResumeJobStatus.PROCESSING,
            attempts=ResumeParseJob.attempts + 1,
            started_at=_now(),
            error_message=None,
        )
    )
    db.commit()
    return result.rowcount == 1


def mark_completed(db: Session, job: ResumeParseJob, parsed_data: dict) -> None:
    job.status = ResumeJobStatus.COMPLETED
    job.parsed_data = parsed_data
    job.error_message = None
    job.completed_at = _now()
    db.commit()


def mark_failed(db: Session, job: ResumeParseJob, message: str) -> None:
    job.status = ResumeJobStatus.FAILED
    job.error_message = message
    job.completed_at = _now()
    db.commit()


def requeue(db: Session, job: ResumeParseJob, message: str) -> None:
    job.status = ResumeJobStatus.QUEUED
    job.error_message = message
    db.commit()
