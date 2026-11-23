"""Applicant ratings (Table 11)."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, Numeric, SmallInteger, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BigIntPrimaryKeyMixin, BigIntType


class ApplicantRating(BigIntPrimaryKeyMixin, Base):
    """Applicant or submission rating; submissions are owned by Jobs (BIGINT ids)."""

    __tablename__ = "applicant_ratings"

    applicant_id: Mapped[int] = mapped_column(BigIntType, ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False)
    submission_id: Mapped[int | None] = mapped_column(BigIntType, nullable=True)
    technical_skills: Mapped[int | None] = mapped_column(SmallInteger)
    communication_skills: Mapped[int | None] = mapped_column(SmallInteger)
    professionalism: Mapped[int | None] = mapped_column(SmallInteger)
    overall_rating: Mapped[Decimal | None] = mapped_column(Numeric(2, 1))
    rated_by: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    rated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("technical_skills IS NULL OR technical_skills BETWEEN 1 AND 5", name="ck_applicant_ratings_technical_range"),
        CheckConstraint("communication_skills IS NULL OR communication_skills BETWEEN 1 AND 5", name="ck_applicant_ratings_communication_range"),
        CheckConstraint("professionalism IS NULL OR professionalism BETWEEN 1 AND 5", name="ck_applicant_ratings_professionalism_range"),
        CheckConstraint("overall_rating IS NULL OR overall_rating BETWEEN 1 AND 5", name="ck_applicant_ratings_overall_range"),
        Index("ix_applicant_ratings_applicant_id_rated_at", "applicant_id", "rated_at"),
        Index("ix_applicant_ratings_submission_id", "submission_id"),
    )
