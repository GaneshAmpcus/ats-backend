"""Tentative applicant detail, activity, task, and lookup tables from the schema DOCX.

These definitions are provisional where the source document labels a table or
field tentative. They use BIGINT record keys and UUID references consistent with
the surrounding application models; refine fields when the business definitions
are finalized.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON, Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index,
    Numeric, String, Text, Uuid, UniqueConstraint, false, func, true, text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BigIntPrimaryKeyMixin, BigIntType, UUIDPrimaryKeyMixin

JSONType = JSON().with_variant(JSONB(), "postgresql")


class ApplicantEducation(BigIntPrimaryKeyMixin, Base):
    """Tentative education history (Table 05)."""
    __tablename__ = "applicant_education"
    applicant_id: Mapped[int] = mapped_column(BigIntType, ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False)
    degree: Mapped[str | None] = mapped_column(String(150))
    specialization: Mapped[str | None] = mapped_column(String(150))
    institution: Mapped[str | None] = mapped_column(String(200))
    university: Mapped[str | None] = mapped_column(String(200))
    start_year: Mapped[int | None] = mapped_column()
    end_year: Mapped[int | None] = mapped_column()
    percentage_cgpa: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    __table_args__ = (Index("ix_applicant_education_applicant_id", "applicant_id"),)


class ApplicantCertification(BigIntPrimaryKeyMixin, Base):
    """Tentative applicant certifications (Table 06)."""
    __tablename__ = "applicant_certifications"
    applicant_id: Mapped[int] = mapped_column(BigIntType, ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False)
    certification_name: Mapped[str | None] = mapped_column(String(200))
    issuing_body: Mapped[str | None] = mapped_column(String(200))
    issued_on: Mapped[date | None] = mapped_column(Date)
    expires_on: Mapped[date | None] = mapped_column(Date)
    credential_id: Mapped[str | None] = mapped_column(String(150))
    __table_args__ = (Index("ix_applicant_certifications_applicant_id", "applicant_id"),)


class ApplicantLanguage(BigIntPrimaryKeyMixin, Base):
    """Tentative applicant language skills (Table 07)."""
    __tablename__ = "applicant_languages"
    applicant_id: Mapped[int] = mapped_column(BigIntType, ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False)
    language_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, comment="FK to languages lookup")
    can_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    can_write: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    can_speak: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    proficiency: Mapped[str | None] = mapped_column(String(20))
    __table_args__ = (Index("ix_applicant_languages_applicant_id", "applicant_id"),)


class ApplicantWorkExperience(BigIntPrimaryKeyMixin, Base):
    """Tentative work history (Table 08)."""
    __tablename__ = "applicant_work_experience"
    applicant_id: Mapped[int] = mapped_column(BigIntType, ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(200))
    job_title: Mapped[str | None] = mapped_column(String(200))
    location: Mapped[str | None] = mapped_column(String(200))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    responsibilities: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (Index("ix_applicant_work_experience_applicant_id", "applicant_id"),)


class ApplicantEmployer(BigIntPrimaryKeyMixin, Base):
    """Tentative employer contacts used by eForm requests (Table 09)."""
    __tablename__ = "applicant_employers"
    applicant_id: Mapped[int] = mapped_column(BigIntType, ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False)
    employer_name: Mapped[str | None] = mapped_column(String(200))
    contact_name: Mapped[str | None] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(25))
    address: Mapped[str | None] = mapped_column(String(500))
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    __table_args__ = (Index("ix_applicant_employers_applicant_id", "applicant_id"),)


class ApplicantTestResult(BigIntPrimaryKeyMixin, Base):
    """Tentative employment test results (Table 10)."""
    __tablename__ = "applicant_test_results"
    applicant_id: Mapped[int] = mapped_column(BigIntType, ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False)
    test_name: Mapped[str | None] = mapped_column(String(200))
    score: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    max_score: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    result: Mapped[str | None] = mapped_column(String(100))
    taken_on: Mapped[date | None] = mapped_column(Date)
    attachment_path: Mapped[str | None] = mapped_column(String(600))
    __table_args__ = (Index("ix_applicant_test_results_applicant_id", "applicant_id"),)


class ApplicantTag(UUIDPrimaryKeyMixin, Base):
    """Tentative applicant-to-tag relation; the tag catalog is a separate lookup."""
    __tablename__ = "applicant_tags"
    applicant_id: Mapped[int] = mapped_column(BigIntType, ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False)
    tag_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("tags.id"), nullable=False)
    tagged_by: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    tagged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    __table_args__ = (UniqueConstraint("applicant_id", "tag_id", name="uq_applicant_tags_applicant_tag"), Index("ix_applicant_tags_tag_id", "tag_id"))


class Tag(UUIDPrimaryKeyMixin, Base):
    """Tenant tag lookup (Table 12)."""
    __tablename__ = "tags"
    business_unit_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    tag_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())
    __table_args__ = (UniqueConstraint("business_unit_id", "tag_name", name="uq_tags_business_unit_name"),)


class ApplicantGroupMember(Base):
    """Many-to-many group membership for bulk assignment (Table 15 child)."""
    __tablename__ = "applicant_group_members"
    group_id: Mapped[int] = mapped_column(BigIntType, ForeignKey("applicant_groups.id", ondelete="CASCADE"), primary_key=True)
    applicant_id: Mapped[int] = mapped_column(BigIntType, ForeignKey("applicants.id", ondelete="CASCADE"), primary_key=True)
    added_by: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    __table_args__ = (Index("ix_applicant_group_members_applicant_id", "applicant_id"),)


class ApplicantNote(BigIntPrimaryKeyMixin, Base):
    """Tentative applicant note and activity note record (Table 18)."""
    __tablename__ = "applicant_notes"
    applicant_id: Mapped[int] = mapped_column(BigIntType, ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False)
    note_scope: Mapped[str] = mapped_column(String(15), nullable=False, default="Applicants", server_default="Applicants")
    submission_id: Mapped[int | None] = mapped_column(BigIntType)
    pipeline_id: Mapped[int | None] = mapped_column(BigIntType, ForeignKey("applicant_pipeline.id", ondelete="SET NULL"))
    title: Mapped[str | None] = mapped_column(String(250))
    job_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("jobs.id", ondelete="SET NULL"))
    client_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    priority: Mapped[str] = mapped_column(String(10), nullable=False, default="Medium", server_default="Medium")
    note_type_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    action_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    summary_text: Mapped[str | None] = mapped_column(String(500))
    note_body: Mapped[str | None] = mapped_column(Text)
    remind_me: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    add_to_task: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    __table_args__ = (Index("ix_applicant_notes_applicant_id_created_at", "applicant_id", "created_at"), Index("ix_applicant_notes_submission_id", "submission_id"))


class ApplicantTask(BigIntPrimaryKeyMixin, Base):
    """Tentative applicant task records (Table 19)."""
    __tablename__ = "applicant_tasks"
    applicant_id: Mapped[int] = mapped_column(BigIntType, ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False)
    related_to_type: Mapped[str] = mapped_column(String(20), nullable=False, default="Applicant", server_default="Applicant")
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    color_code: Mapped[str | None] = mapped_column(String(10))
    description: Mapped[str | None] = mapped_column(String(2000))
    task_type_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    task_category_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    time_zone: Mapped[str] = mapped_column(String(60), nullable=False, default="Asia/Kolkata", server_default="Asia/Kolkata")
    status_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    assigned_to_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    escalate_to_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    reminder_offset_min: Mapped[int | None] = mapped_column()
    ownership_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    notify_via_email: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    show_on_calendar: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    is_recurring: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    recurrence_rule: Mapped[str | None] = mapped_column(String(500))
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_by: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    status_modified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (Index("ix_applicant_tasks_assigned_status_due", "assigned_to_user_id", "status_id", "due_at"), Index("ix_applicant_tasks_applicant_id", "applicant_id"))


class ApplicantActivity(BigIntPrimaryKeyMixin, Base):
    """Timeline activity index (Table 19 in source row numbering)."""
    __tablename__ = "applicant_activity"
    applicant_id: Mapped[int] = mapped_column(BigIntType, ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False)
    activity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    activity_text: Mapped[str | None] = mapped_column(String(1000))
    ref_entity: Mapped[str | None] = mapped_column(String(30))
    ref_id: Mapped[int | None] = mapped_column(BigIntType)
    activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    __table_args__ = (Index("ix_applicant_activity_applicant_activity_at", "applicant_id", "activity_at"), Index("ix_applicant_activity_type", "activity_type"))


class ApplicantEForm(BigIntPrimaryKeyMixin, Base):
    """Tentative eForm/detail request record (Table 35)."""
    __tablename__ = "applicant_eforms"
    applicant_id: Mapped[int] = mapped_column(BigIntType, ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False)
    submission_id: Mapped[int | None] = mapped_column(BigIntType)
    request_type: Mapped[str] = mapped_column(String(25), nullable=False)
    applicant_employer_id: Mapped[int | None] = mapped_column(BigIntType, ForeignKey("applicant_employers.id", ondelete="SET NULL"))
    form_template_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    status: Mapped[str] = mapped_column(String(15), nullable=False)
    response_path: Mapped[str | None] = mapped_column(String(600))
    requested_by: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (Index("ix_applicant_eforms_applicant_id", "applicant_id"), Index("ix_applicant_eforms_submission_id", "submission_id"))


class ApplicantFeedbackReview(BigIntPrimaryKeyMixin, Base):
    """Tentative feedback review request (Table 37)."""
    __tablename__ = "applicant_feedback_reviews"
    applicant_id: Mapped[int] = mapped_column(BigIntType, ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("jobs.id", ondelete="SET NULL"))
    submission_id: Mapped[int | None] = mapped_column(BigIntType)
    status: Mapped[str] = mapped_column(String(15), nullable=False)
    feedback_text: Mapped[str | None] = mapped_column(Text)
    requested_by: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    __table_args__ = (Index("ix_applicant_feedback_reviews_applicant_id", "applicant_id"), Index("ix_applicant_feedback_reviews_submission_id", "submission_id"))


class ApplicantLookup(UUIDPrimaryKeyMixin, Base):
    """Generic UUID-backed lookup where the source document did not name a table."""
    __abstract__ = True
    label: Mapped[str] = mapped_column(String(150), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())


def _lookup(name: str, doc: str) -> type[ApplicantLookup]:
    """Create a simple named lookup model for the document's dropdown tables."""
    return type(name, (ApplicantLookup,), {"__tablename__": doc, "__doc__": f"{doc} applicant lookup."})


class Country(UUIDPrimaryKeyMixin, Base):
    """Country dropdown lookup."""
    __tablename__ = "countries"
    country_name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    iso_code: Mapped[str | None] = mapped_column(String(3), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())


State = type("State", (Base,), {
    "__tablename__": "states",
    "id": mapped_column(Uuid, primary_key=True, default=uuid.uuid4),
    "country_id": mapped_column(Uuid, ForeignKey("countries.id"), nullable=False),
    "state_name": mapped_column(String(150), nullable=False),
    "is_active": mapped_column(Boolean, nullable=False, default=True, server_default=true()),
    "__table_args__": (Index("ix_states_country_id", "country_id"),),
})
class WorkAuthorization(UUIDPrimaryKeyMixin, Base):
    """Work authorization dropdown lookup."""
    __tablename__ = "work_authorizations"
    name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())


class ApplicantSource(UUIDPrimaryKeyMixin, Base):
    """Applicant source dropdown lookup."""
    __tablename__ = "applicant_sources"
    name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())


class BusinessUnit(UUIDPrimaryKeyMixin, Base):
    """Business-unit tenant lookup."""
    __tablename__ = "business_units"
    unit_name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())


ApplicantStatus = type("ApplicantStatus", (UUIDPrimaryKeyMixin, Base), {
    "__tablename__": "applicant_statuses",
    "status_name": mapped_column(String(100), nullable=False),
    "allow_submission": mapped_column(Boolean, nullable=False, default=False, server_default=false()),
    "is_default": mapped_column(Boolean, nullable=False, default=False, server_default=false()),
    "is_active": mapped_column(Boolean, nullable=False, default=True, server_default=true()),
    "__table_args__": (Index("uq_applicant_statuses_default", "is_default", unique=True, postgresql_where=text("is_default"), sqlite_where=text("is_default")),),
})
NoticePeriod = _lookup("NoticePeriod", "notice_periods")
PreferredShift = _lookup("PreferredShift", "preferred_shifts")
Industry = _lookup("Industry", "industries")
MaritalStatus = _lookup("MaritalStatus", "marital_statuses")
Nationality = _lookup("Nationality", "nationalities")
EeoGender = _lookup("EeoGender", "eeo_genders")
EeoRace = _lookup("EeoRace", "eeo_races")
EeoVeteranStatus = _lookup("EeoVeteranStatus", "eeo_veteran_statuses")
EeoDisability = _lookup("EeoDisability", "eeo_disabilities")
Language = _lookup("Language", "languages")
NoteType = _lookup("NoteType", "note_types")
NoteAction = _lookup("NoteAction", "note_actions")
TaskType = _lookup("TaskType", "task_types")
TaskCategory = _lookup("TaskCategory", "task_categories")
TaskStatus = type("TaskStatus", (UUIDPrimaryKeyMixin, Base), {
    "__tablename__": "task_statuses",
    "label": mapped_column(String(150), nullable=False),
    "is_default": mapped_column(Boolean, nullable=False, default=False, server_default=false()),
    "is_active": mapped_column(Boolean, nullable=False, default=True, server_default=true()),
})
CallType = _lookup("CallType", "call_types")
ResumeTemplate = type("ResumeTemplate", (UUIDPrimaryKeyMixin, Base), {
    "__tablename__": "resume_templates",
    "template_name": mapped_column(String(150), nullable=False),
    "layout_path": mapped_column(String(600), nullable=True),
    "is_active": mapped_column(Boolean, nullable=False, default=True, server_default=true()),
})
EFormTemplate = _lookup("EFormTemplate", "eform_templates")
EInterviewTemplate = _lookup("EInterviewTemplate", "einterview_templates")
RequestType = _lookup("RequestType", "request_types")
