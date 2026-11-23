"""Saved list views, their columns and filters (Tables 25, 26 and 27)."""

import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Uuid,
    false,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BigIntPrimaryKeyMixin, BigIntType, TimestampMixin


class ApplicantView(BigIntPrimaryKeyMixin, TimestampMixin, Base):
    """A saved applicant list view (``applicant_views``, "Add View -> Create View").

    "All Profiles" is the system default view and is not stored. A user can have
    at most one default view (enforced by a partial unique index).
    """

    __tablename__ = "applicant_views"

    business_unit_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        nullable=False,
        comment="FK to business_units - to be added when master exists",
    )
    view_name: Mapped[str] = mapped_column(String(150), nullable=False)
    is_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    filter_gdpr_consent: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
        comment="Maps to applicants.gdpr_consent_approved",
    )
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        nullable=False,
        comment="FK to users - to be added when master exists. Creator owns the view.",
    )

    __table_args__ = (
        Index(
            "uq_applicant_views_owner_user_id_default",
            "owner_user_id",
            unique=True,
            postgresql_where=text("is_default"),
            sqlite_where=text("is_default"),
        ),
        Index("ix_applicant_views_business_unit_id_owner_user_id", "business_unit_id", "owner_user_id"),
    )


class ApplicantViewColumn(BigIntPrimaryKeyMixin, Base):
    """A selected list column of a view or a folder (``applicant_view_columns``).

    Exactly one of ``view_id`` / ``folder_id`` must be set. ``column_key`` comes
    from the list-column master (76 selectable columns), which is not modelled yet.
    """

    __tablename__ = "applicant_view_columns"

    view_id: Mapped[int | None] = mapped_column(
        BigIntType, ForeignKey("applicant_views.id"), nullable=True
    )
    folder_id: Mapped[int | None] = mapped_column(
        BigIntType, ForeignKey("applicant_folders.id"), nullable=True
    )
    column_key: Mapped[str] = mapped_column(String(60), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "(view_id IS NOT NULL AND folder_id IS NULL) "
            "OR (view_id IS NULL AND folder_id IS NOT NULL)",
            name="ck_applicant_view_columns_view_or_folder",
        ),
        Index("ix_applicant_view_columns_view_id", "view_id"),
        Index("ix_applicant_view_columns_folder_id", "folder_id"),
    )


class ApplicantViewFilter(BigIntPrimaryKeyMixin, Base):
    """A field-level filter of a view (``applicant_view_filters``)."""

    __tablename__ = "applicant_view_filters"

    view_id: Mapped[int] = mapped_column(
        BigIntType, ForeignKey("applicant_views.id"), nullable=False
    )
    field_name: Mapped[str] = mapped_column(String(60), nullable=False)
    operator: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="e.g. equals / contains / in"
    )
    filter_value: Mapped[str | None] = mapped_column(String(500), nullable=True)
    display_order: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (Index("ix_applicant_view_filters_view_id", "view_id"),)
