from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.resumes.models import ResumeBatch, ResumeJobStatus


class ResumeJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    batch_id: UUID | None
    status: ResumeJobStatus
    original_filename: str
    file_size: int
    attempts: int
    parsed_data: dict[str, Any] | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class RejectedFile(BaseModel):
    filename: str
    reason: str


class ResumeBatchResponse(BaseModel):
    id: UUID
    # processing | completed | completed_with_errors | failed
    status: str
    total: int
    queued: int
    processing: int
    completed: int
    failed: int
    created_at: datetime
    jobs: list[ResumeJobResponse]

    @classmethod
    def from_batch(cls, batch: ResumeBatch) -> "ResumeBatchResponse":
        counts = {status: 0 for status in ResumeJobStatus}
        for job in batch.jobs:
            counts[job.status] += 1

        if counts[ResumeJobStatus.QUEUED] or counts[ResumeJobStatus.PROCESSING]:
            status = "processing"
        elif counts[ResumeJobStatus.FAILED] == 0:
            status = "completed"
        elif counts[ResumeJobStatus.COMPLETED] == 0:
            status = "failed"
        else:
            status = "completed_with_errors"

        return cls(
            id=batch.id,
            status=status,
            total=batch.total_jobs,
            queued=counts[ResumeJobStatus.QUEUED],
            processing=counts[ResumeJobStatus.PROCESSING],
            completed=counts[ResumeJobStatus.COMPLETED],
            failed=counts[ResumeJobStatus.FAILED],
            created_at=batch.created_at,
            jobs=[ResumeJobResponse.model_validate(job) for job in batch.jobs],
        )


class ResumeBatchCreatedResponse(ResumeBatchResponse):
    """Bulk upload response. Files that failed validation are listed in `rejected`."""

    rejected: list[RejectedFile] = []
