"""Applicant folders and their members (Tables 28 and 29)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BigIntPrimaryKeyMixin, BigIntType


class ApplicantFolder(BigIntPrimaryKeyMixin, Base):
    """A user-created folder of applicants (``applicant_folders``).

    Created via "Add View -> Create Folder". The creator owns the folder.
    """

    __tablename__ = "applicant_folders"

    business_unit_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        nullable=False,
        comment="FK to business_units - to be added when master exists",
    )
    folder_name: Mapped[str] = mapped_column(String(150), nullable=False)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        nullable=False,
        comment="FK to users - to be added when master exists",
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )

    __table_args__ = (
        Index("ix_applicant_folders_business_unit_id_owner_user_id", "business_unit_id", "owner_user_id"),
    )


class ApplicantFolderMember(Base):
    """An applicant placed inside a folder (``applicant_folder_members``).

    Primary key is ``(folder_id, applicant_id)``.
    """

    __tablename__ = "applicant_folder_members"

    folder_id: Mapped[int] = mapped_column(
        BigIntType, ForeignKey("applicant_folders.id"), primary_key=True
    )
    applicant_id: Mapped[int] = mapped_column(
        BigIntType, ForeignKey("applicants.id"), primary_key=True
    )
    added_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        nullable=True,
        comment="FK to users - to be added when master exists",
    )
    added_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )

    __table_args__ = (
        # Reverse lookup: folders containing an applicant.
        Index("ix_applicant_folder_members_applicant_id", "applicant_id"),
    )
