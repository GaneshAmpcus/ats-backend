from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.modules.resumes import repository, service
from app.modules.resumes.schemas import (
    RejectedFile,
    ResumeBatchCreatedResponse,
    ResumeBatchResponse,
    ResumeJobResponse,
)
from app.modules.resumes.service import ResumeServiceError

router = APIRouter(prefix="/resumes", tags=["resumes"])

_CHUNK_SIZE = 1024 * 1024


def _read_limited(file: UploadFile, max_bytes: int) -> bytes:
    """Read an upload without ever buffering more than max_bytes + one chunk."""
    chunks: list[bytes] = []
    size = 0
    while chunk := file.file.read(_CHUNK_SIZE):
        size += len(chunk)
        if size > max_bytes:
            raise ResumeServiceError("The file exceeds the upload size limit.", 413)
        chunks.append(chunk)
    return b"".join(chunks)


def _validate(file: UploadFile, settings: Settings) -> service.ValidatedUpload:
    data = _read_limited(file, settings.resume_max_upload_mb * 1024 * 1024)
    return service.validate_upload(file.filename, data, settings)


@router.post("/parse", response_model=ResumeJobResponse, status_code=202)
def parse_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ResumeJobResponse:
    """Upload one resume. Returns a job; poll GET /resumes/jobs/{id} for the result."""
    try:
        upload = _validate(file, settings)
        job = service.submit_single(db, upload)
    except ResumeServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return ResumeJobResponse.model_validate(job)


@router.post("/parse/bulk", response_model=ResumeBatchCreatedResponse, status_code=202)
def parse_resumes_bulk(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ResumeBatchCreatedResponse:
    """Upload many resumes. Valid files are queued; invalid ones are listed in `rejected`."""
    if len(files) > settings.resume_max_batch_files:
        raise HTTPException(
            status_code=413,
            detail=f"A batch can contain at most {settings.resume_max_batch_files} files.",
        )

    uploads: list[service.ValidatedUpload] = []
    rejected: list[RejectedFile] = []
    for file in files:
        try:
            uploads.append(_validate(file, settings))
        except ResumeServiceError as exc:
            rejected.append(RejectedFile(filename=file.filename or "", reason=exc.message))

    try:
        batch, rejected = service.submit_batch(db, uploads, rejected)
    except ResumeServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    base = ResumeBatchResponse.from_batch(batch)
    return ResumeBatchCreatedResponse(**base.model_dump(), rejected=rejected)


@router.get("/jobs/{job_id}", response_model=ResumeJobResponse)
def get_resume_job(job_id: UUID, db: Session = Depends(get_db)) -> ResumeJobResponse:
    job = repository.get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Resume job not found.")
    return ResumeJobResponse.model_validate(job)


@router.get("/batches/{batch_id}", response_model=ResumeBatchResponse)
def get_resume_batch(batch_id: UUID, db: Session = Depends(get_db)) -> ResumeBatchResponse:
    batch = repository.get_batch(db, batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Resume batch not found.")
    return ResumeBatchResponse.from_batch(batch)
