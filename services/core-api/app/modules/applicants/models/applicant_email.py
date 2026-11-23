"""Emails sent to applicants (Table 33)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BigIntPrimaryKeyMixin, BigIntType
from app.modules.applicants.enums import EmailType


class ApplicantEmail(BigIntPrimaryKeyMixin, Base):
    """An email sent to an applicant (``applicant_emails``).

    Drives the count on the timeline Email tab. ``body`` is HTML and must be
    sanitised by the service layer before it is stored.
    """

    __tablename__ = "applicant_emails"

    applicant_id: Mapped[int] = mapped_column(
        BigIntType, ForeignKey("applicants.id"), nullable=False
    )
    email_type: Mapped[str] = mapped_column(
        String(15),
        nullable=False,
        default=EmailType.GENERAL.value,
        server_default=EmailType.GENERAL.value,
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("jobs.id"), nullable=True, comment="Set for Share Job emails"
    )
    from_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        nullable=False,
        comment="FK to users - to be added when master exists",
    )
    to_email: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cc_email: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bcc_email: Mapped[str | None] = mapped_column(String(500), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    delivery_status: Mapped[str | None] = mapped_column(String(15), nullable=True)

    __table_args__ = (
        Index("ix_applicant_emails_applicant_id_sent_at", "applicant_id", "sent_at"),
        Index("ix_applicant_emails_job_id", "job_id"),
    )
