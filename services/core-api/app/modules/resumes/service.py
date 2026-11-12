import hashlib
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.integrations.storage import FileStorage, StorageError, get_resume_storage
from app.modules.resumes import repository
from app.modules.resumes.models import ResumeBatch, ResumeParseJob
from app.modules.resumes.schemas import RejectedFile

logger = logging.getLogger(__name__)

ALLOWED_TYPES: dict[str, str] = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
}


class ResumeServiceError(Exception):
    """Business-rule failure carrying the HTTP status the router should return."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class ValidatedUpload:
    filename: str
    extension: str
    content_type: str
    data: bytes
    sha256: str


def validate_upload(filename: str | None, data: bytes, settings: Settings) -> ValidatedUpload:
    safe_name = os.path.basename((filename or "").replace("\\", "/")).strip()[:255]
    if not safe_name:
        raise ResumeServiceError("A filename is required.", 400)

    extension = Path(safe_name).suffix.lower()
    if extension not in ALLOWED_TYPES:
        raise ResumeServiceError("Unsupported file type. Upload a PDF, DOCX or TXT file.", 415)

    if not data:
        raise ResumeServiceError("The uploaded file is empty.", 400)
    if len(data) > settings.resume_max_upload_mb * 1024 * 1024:
        raise ResumeServiceError(
            f"The file exceeds the {settings.resume_max_upload_mb} MB limit.", 413
        )

    signature_ok = {
        ".pdf": b"%PDF-" in data[:1024],
        ".docx": data.startswith(b"PK\x03\x04"),
        ".txt": b"\x00" not in data[:8192],
    }[extension]
    if not signature_ok:
        raise ResumeServiceError("The file content does not match its extension.", 415)

    return ValidatedUpload(
        filename=safe_name,
        extension=extension,
        content_type=ALLOWED_TYPES[extension],
        data=data,
        sha256=hashlib.sha256(data).hexdigest(),
    )


def _new_job(
    upload: ValidatedUpload,
    storage: FileStorage,
    *,
    batch_id: uuid.UUID | None = None,
    position: int | None = None,
) -> ResumeParseJob:
    job_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    # The user's filename is only metadata; it is never used in the storage path.
    storage_key = f"{now:%Y/%m}/{job_id}{upload.extension}"
    storage.save(storage_key, upload.data)
    return ResumeParseJob(
        id=job_id,
        batch_id=batch_id,
        batch_position=position,
        original_filename=upload.filename,
        content_type=upload.content_type,
        file_size=len(upload.data),
        file_sha256=upload.sha256,
        storage_key=storage_key,
    )


def _discard_files(storage: FileStorage, jobs: list[ResumeParseJob]) -> None:
    for job in jobs:
        try:
            storage.delete(job.storage_key)
        except StorageError:
            logger.warning("Could not remove orphaned file %s", job.storage_key)


def _enqueue(db: Session, jobs: list[ResumeParseJob], *, high_priority: bool) -> list[ResumeParseJob]:
    # Imported here so the API process only needs Celery when a job is actually queued.
    from app.modules.resumes.tasks import enqueue_parse_job

    failed: list[ResumeParseJob] = []
    for job in jobs:
        try:
            enqueue_parse_job(job.id, high_priority=high_priority)
        except Exception:
            logger.exception("Could not enqueue resume job %s", job.id)
            repository.mark_failed(db, job, "The parsing job could not be queued.")
            failed.append(job)
        else:
            # In eager mode the task has already run; elsewhere this is a cheap no-op read.
            db.refresh(job)
    return failed


def submit_single(db: Session, upload: ValidatedUpload) -> ResumeParseJob:
    storage = get_resume_storage()
    job = _new_job(upload, storage)
    try:
        repository.add_job(db, job)
        db.commit()
    except Exception:
        db.rollback()
        _discard_files(storage, [job])
        raise

    if _enqueue(db, [job], high_priority=True):
        raise ResumeServiceError("The parsing service is unavailable. Please try again.", 503)
    return job


def submit_batch(
    db: Session,
    uploads: list[ValidatedUpload],
    rejected: list[RejectedFile],
) -> tuple[ResumeBatch, list[RejectedFile]]:
    if not uploads:
        raise ResumeServiceError("None of the uploaded files could be accepted.", 400)

    storage = get_resume_storage()
    jobs: list[ResumeParseJob] = []
    try:
        batch = repository.create_batch(db, total_jobs=len(uploads))
        for position, upload in enumerate(uploads):
            job = _new_job(upload, storage, batch_id=batch.id, position=position)
            jobs.append(job)
            repository.add_job(db, job)
        db.commit()
    except Exception:
        db.rollback()
        _discard_files(storage, jobs)
        raise

    _enqueue(db, jobs, high_priority=False)
    refreshed = repository.get_batch(db, batch.id)
    return (refreshed or batch), rejected
