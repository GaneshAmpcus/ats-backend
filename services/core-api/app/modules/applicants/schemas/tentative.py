"""Pydantic schemas for tables documented as tentative in the supplied schema."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApplicantEducationCreate(BaseModel):
    applicant_id: int
    degree: str | None = Field(default=None, max_length=150)
    specialization: str | None = Field(default=None, max_length=150)
    institution: str | None = Field(default=None, max_length=200)
    university: str | None = Field(default=None, max_length=200)
    start_year: int | None = Field(default=None, ge=1900, le=2200)
    end_year: int | None = Field(default=None, ge=1900, le=2200)
    percentage_cgpa: Decimal | None = Field(default=None, ge=0, le=100)


class ApplicantEducationRead(ApplicantEducationCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ApplicantCertificationCreate(BaseModel):
    applicant_id: int
    certification_name: str | None = Field(default=None, max_length=200)
    issuing_body: str | None = Field(default=None, max_length=200)
    issued_on: date | None = None
    expires_on: date | None = None
    credential_id: str | None = Field(default=None, max_length=150)


class ApplicantCertificationRead(ApplicantCertificationCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ApplicantLanguageCreate(BaseModel):
    applicant_id: int
    language_id: UUID | None = None
    can_read: bool = False
    can_write: bool = False
    can_speak: bool = False
    proficiency: str | None = Field(default=None, max_length=20)


class ApplicantLanguageRead(ApplicantLanguageCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ApplicantWorkExperienceCreate(BaseModel):
    applicant_id: int
    company_name: str | None = Field(default=None, max_length=200)
    job_title: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    responsibilities: str | None = None


class ApplicantWorkExperienceRead(ApplicantWorkExperienceCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ApplicantEmployerCreate(BaseModel):
    applicant_id: int
    employer_name: str | None = Field(default=None, max_length=200)
    contact_name: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=25)
    address: str | None = Field(default=None, max_length=500)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)


class ApplicantEmployerRead(ApplicantEmployerCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ApplicantTestResultCreate(BaseModel):
    applicant_id: int
    test_name: str | None = Field(default=None, max_length=200)
    score: Decimal | None = None
    max_score: Decimal | None = None
    result: str | None = Field(default=None, max_length=100)
    taken_on: date | None = None
    attachment_path: str | None = Field(default=None, max_length=600)


class ApplicantTestResultRead(ApplicantTestResultCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ApplicantTagCreate(BaseModel):
    applicant_id: int
    tag_id: UUID
    tagged_by: UUID | None = None


class ApplicantTagRead(ApplicantTagCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tagged_at: datetime


class TagCreate(BaseModel):
    business_unit_id: UUID
    tag_name: str = Field(min_length=1, max_length=100)
    is_active: bool = True


class TagRead(TagCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


class ApplicantGroupMemberCreate(BaseModel):
    group_id: int
    applicant_id: int
    added_by: UUID | None = None


class ApplicantGroupMemberRead(ApplicantGroupMemberCreate):
    model_config = ConfigDict(from_attributes=True)
    added_at: datetime


class ApplicantNoteCreate(BaseModel):
    applicant_id: int
    note_scope: str = Field(default="Applicants", max_length=15)
    submission_id: int | None = None
    pipeline_id: int | None = None
    title: str | None = Field(default=None, max_length=250)
    job_id: UUID | None = None
    client_id: UUID | None = None
    priority: str = Field(default="Medium", max_length=10)
    note_type_id: UUID | None = None
    action_id: UUID | None = None
    summary_text: str | None = Field(default=None, max_length=500)
    note_body: str | None = None
    remind_me: bool = False
    add_to_task: bool = False
    created_by: UUID | None = None


class ApplicantNoteRead(ApplicantNoteCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class ApplicantTaskCreate(BaseModel):
    applicant_id: int
    related_to_type: str = Field(default="Applicant", max_length=20)
    title: str = Field(min_length=1, max_length=250)
    color_code: str | None = Field(default=None, max_length=10)
    description: str | None = Field(default=None, max_length=2000)
    task_type_id: UUID | None = None
    task_category_id: UUID | None = None
    due_at: datetime | None = None
    time_zone: str = Field(default="Asia/Kolkata", max_length=60)
    status_id: UUID | None = None
    assigned_to_user_id: UUID | None = None
    escalate_to_user_id: UUID | None = None
    reminder_offset_min: int | None = Field(default=None, ge=0)
    ownership_user_id: UUID | None = None
    notify_via_email: bool = False
    show_on_calendar: bool = False
    is_recurring: bool = False
    recurrence_rule: str | None = Field(default=None, max_length=500)
    created_by: UUID | None = None


class ApplicantTaskRead(ApplicantTaskCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_by: UUID | None
    updated_at: datetime | None
    status_modified_at: datetime | None


class ApplicantActivityCreate(BaseModel):
    applicant_id: int
    activity_type: str = Field(min_length=1, max_length=20)
    activity_text: str | None = Field(default=None, max_length=1000)
    ref_entity: str | None = Field(default=None, max_length=30)
    ref_id: int | None = None
    activity_at: datetime | None = None
    created_by: UUID | None = None


class ApplicantActivityRead(ApplicantActivityCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ApplicantEFormCreate(BaseModel):
    applicant_id: int
    submission_id: int | None = None
    request_type: str = Field(min_length=1, max_length=25)
    applicant_employer_id: int | None = None
    form_template_id: UUID | None = None
    status: str = Field(min_length=1, max_length=15)
    response_path: str | None = Field(default=None, max_length=600)
    requested_by: UUID | None = None
    requested_at: datetime | None = None
    completed_at: datetime | None = None


class ApplicantEFormRead(ApplicantEFormCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ApplicantFeedbackReviewCreate(BaseModel):
    applicant_id: int
    job_id: UUID | None = None
    submission_id: int | None = None
    status: str = Field(min_length=1, max_length=15)
    feedback_text: str | None = None
    requested_by: UUID | None = None
    requested_at: datetime | None = None
    received_at: datetime | None = None
    created_by: UUID | None = None


class ApplicantFeedbackReviewRead(ApplicantFeedbackReviewCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class LookupCreate(BaseModel):
    """Base payload for straightforward active/inactive lookup values."""
    label: str = Field(min_length=1, max_length=150)
    is_active: bool = True


class LookupRead(LookupCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


class ApplicantStatusCreate(LookupCreate):
    allow_submission: bool = False
    is_default: bool = False


class ApplicantStatusRead(ApplicantStatusCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


class StateCreate(BaseModel):
    country_id: UUID
    state_name: str = Field(min_length=1, max_length=150)
    is_active: bool = True


class StateRead(StateCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


class ResumeTemplateCreate(BaseModel):
    template_name: str = Field(min_length=1, max_length=150)
    layout_path: str | None = Field(default=None, max_length=600)
    is_active: bool = True


class ResumeTemplateRead(ResumeTemplateCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


class CountryCreate(BaseModel):
    country_name: str = Field(min_length=1, max_length=150)
    iso_code: str | None = Field(default=None, max_length=3)
    is_active: bool = True


class CountryRead(CountryCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


class BusinessUnitCreate(BaseModel):
    unit_name: str = Field(min_length=1, max_length=200)
    is_active: bool = True


class BusinessUnitRead(BusinessUnitCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


class NamedLookupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    is_active: bool = True


class NamedLookupRead(NamedLookupCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
