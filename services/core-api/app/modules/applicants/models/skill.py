"""Skill master and applicant-skill link (Tables 03 and 02)."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    false,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BigIntPrimaryKeyMixin, BigIntType


class Skill(BigIntPrimaryKeyMixin, Base):
    """Skill master list (``skills``).

    Backs the auto-suggest tag input and resume-parser inserts.
    """

    __tablename__ = "skills"

    skill_name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )


class ApplicantSkill(BigIntPrimaryKeyMixin, Base):
    """Skills attached to an applicant (``applicant_skills``).

    Rows are removed with their applicant (``ON DELETE CASCADE``). An applicant
    can hold a given skill only once.
    """

    __tablename__ = "applicant_skills"

    applicant_id: Mapped[int] = mapped_column(
        BigIntType, ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False
    )
    skill_id: Mapped[int] = mapped_column(
        BigIntType, ForeignKey("skills.id"), nullable=False
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )

    __table_args__ = (
        UniqueConstraint(
            "applicant_id", "skill_id", name="uq_applicant_skills_applicant_id_skill_id"
        ),
        # Reverse lookup: applicants holding a skill. (applicant_id is covered by the
        # unique constraint above.)
        Index("ix_applicant_skills_skill_id", "skill_id"),
    )
