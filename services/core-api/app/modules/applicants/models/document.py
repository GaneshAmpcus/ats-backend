"""Applicant documents and resume download audit records (Tables 04 and 39)."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String, Uuid, false, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BigIntPrimaryKeyMixin, BigIntType


class ApplicantDocument(BigIntPrimaryKeyMixin, Base):
    """Metadata and parse-job link for an applicant file; file bytes stay in storage."""

    __tablename__ = "applicant_documents"

    applicant_id: Mapped[int] = mapped_column(
        BigIntType, ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False
    )
    resume_parse_job_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("resume_parse_jobs.id", ondelete="SET NULL"), nullable=True
    )
    document_type: Mapped[str] = mapped_column(String(30), nullable=False)
    file_name: Mapped[str] = mapped_column(String(300), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(600), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(100))
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    is_primary_resume: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    is_parsed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    comments: Mapped[str | None] = mapped_column(String(1000))
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_by: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("ix_applicant_documents_applicant_id_created_at", "applicant_id", "created_at"),
        Index("ix_applicant_documents_resume_parse_job_id", "resume_parse_job_id"),
    )


class ApplicantResumeDownloadLog(BigIntPrimaryKeyMixin, Base):
    """Audit trail for individual and bulk resume downloads."""

    __tablename__ = "applicant_resume_download_log"

    applicant_id: Mapped[int] = mapped_column(
        BigIntType, ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False
    )
    document_id: Mapped[int] = mapped_column(
        BigIntType, ForeignKey("applicant_documents.id", ondelete="RESTRICT"), nullable=False
    )
    download_mode: Mapped[str | None] = mapped_column(String(10))
    downloaded_by: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    downloaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index("ix_applicant_resume_download_log_applicant_downloaded_at", "applicant_id", "downloaded_at"),
        Index("ix_applicant_resume_download_log_document_id", "document_id"),
    )
