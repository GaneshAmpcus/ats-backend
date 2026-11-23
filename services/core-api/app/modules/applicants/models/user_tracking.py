"""Per-user applicant tracking: favourites and last-viewed log (Tables 13 and 14)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BigIntType


class ApplicantFavorite(Base):
    """An applicant marked as a favourite by a user (``applicant_favorites``).

    Favourites are per user; the primary key is ``(user_id, applicant_id)``.
    """

    __tablename__ = "applicant_favorites"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        comment="FK to users - to be added when master exists",
    )
    applicant_id: Mapped[int] = mapped_column(
        BigIntType, ForeignKey("applicants.id"), primary_key=True
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )


class ApplicantViewLog(Base):
    """When a user last opened an applicant (``applicant_views_log``).

    Drives the "not yet opened by the current user" highlight in lists. The
    primary key is ``(user_id, applicant_id)``; write with an upsert.

    Note:
        The source schema declares no foreign key on ``applicant_id`` here, so
        none is created.
    """

    __tablename__ = "applicant_views_log"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        comment="FK to users - to be added when master exists",
    )
    applicant_id: Mapped[int] = mapped_column(BigIntType, primary_key=True)
    last_viewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
