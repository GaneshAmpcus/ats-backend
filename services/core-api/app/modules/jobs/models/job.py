import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.jobs.enums import JobStatus

if TYPE_CHECKING:
    from app.modules.jobs.models.assignment import JobAssignment
    from app.modules.jobs.models.location import JobLocation
    from app.modules.jobs.models.status_history import JobStatusHistory


class Job(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "jobs"

    job_code: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    client_job_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    job_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=JobStatus.ACTIVE.value
    )
    job_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    job_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    respond_by: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    experience_min: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 1), nullable=True
    )
    experience_max: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 1), nullable=True
    )
    min_salary: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    max_salary: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    currency_code: Mapped[str | None] = mapped_column(String(3), nullable=True)
    client_bill_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2), nullable=True
    )
    client_bill_rate_type: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )
    number_of_positions: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )
    maximum_allowed_submissions: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    hit_quota: Mapped[int | None] = mapped_column(Integer, nullable=True)
    remote_job: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_hot_job: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Master references. Plain UUID columns for now; ForeignKeys will be added
    # once the corresponding master tables exist.
    client_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, nullable=True, comment="FK to clients - to be added when master exists"
    )
    business_unit_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        nullable=True,
        comment="FK to business_units - to be added when master exists",
    )
    client_practice_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        nullable=True,
        comment="FK to client_practices - to be added when master exists",
    )
    industry_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, nullable=True, comment="FK to industries - to be added when master exists"
    )
    job_category_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        nullable=True,
        comment="FK to job_categories - to be added when master exists",
    )
    job_type_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, nullable=True, comment="FK to job_types - to be added when master exists"
    )
    priority_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, nullable=True, comment="FK to priorities - to be added when master exists"
    )
    clearance_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, nullable=True, comment="FK to clearances - to be added when master exists"
    )
    notice_period_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        nullable=True,
        comment="FK to notice_periods - to be added when master exists",
    )

    # Audit fields. Plain UUID columns, no ForeignKey.
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    modified_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)

    assignments: Mapped[list["JobAssignment"]] = relationship(
        "JobAssignment", cascade="all, delete-orphan"
    )
    locations: Mapped[list["JobLocation"]] = relationship(
        "JobLocation", cascade="all, delete-orphan"
    )
    status_history: Mapped[list["JobStatusHistory"]] = relationship(
        "JobStatusHistory", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "experience_min IS NULL OR experience_max IS NULL "
            "OR experience_max >= experience_min",
            name="ck_jobs_experience_range",
        ),
        CheckConstraint(
            "min_salary IS NULL OR max_salary IS NULL OR max_salary >= min_salary",
            name="ck_jobs_salary_range",
        ),
        CheckConstraint(
            "job_start_date IS NULL OR job_end_date IS NULL "
            "OR job_end_date >= job_start_date",
            name="ck_jobs_date_range",
        ),
        Index("ix_jobs_client_id", "client_id"),
        Index("ix_jobs_status", "status"),
    )
