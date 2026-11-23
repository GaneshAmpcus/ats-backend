"""Applicant job pipeline - "Tag to Job" (Table 40)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BigIntPrimaryKeyMixin, BigIntType


class ApplicantPipeline(BigIntPrimaryKeyMixin, Base):
    """An applicant tagged to a job (``applicant_pipeline``).

    Moves to a submission when the applicant is submitted. This table is the
    target of ``applicant_notes.pipeline_id`` (held for a later delivery). An
    applicant can be tagged to a given job only once.
    """

    __tablename__ = "applicant_pipeline"

    applicant_id: Mapped[int] = mapped_column(
        BigIntType, ForeignKey("applicants.id"), nullable=False
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("jobs.id"), nullable=False
    )
    pipeline_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    tagged_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        nullable=True,
        comment="FK to users - to be added when master exists",
    )
    tagged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )

    __table_args__ = (
        UniqueConstraint(
            "applicant_id", "job_id", name="uq_applicant_pipeline_applicant_id_job_id"
        ),
        # Reverse lookup: applicants tagged to a job.
        Index("ix_applicant_pipeline_job_id", "job_id"),
    )
