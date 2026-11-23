"""API schemas for the applicant module's supporting Wave 1 tables."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.applicants.enums import EmailType, SearchHistoryType


class SkillCreate(BaseModel):
    skill_name: str = Field(min_length=1, max_length=150)
    is_active: bool = True


class SkillRead(SkillCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ApplicantSkillCreate(BaseModel):
    skill_id: int
    is_primary: bool = False


class ApplicantSkillRead(ApplicantSkillCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    applicant_id: int
    created_at: datetime | None


class ApplicantFavoriteCreate(BaseModel):
    applicant_id: int


class ApplicantFavoriteRead(ApplicantFavoriteCreate):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    created_at: datetime | None


class ApplicantViewLogWrite(BaseModel):
    applicant_id: int
    last_viewed_at: datetime | None = None


class ApplicantViewLogRead(ApplicantViewLogWrite):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID


class ApplicantGroupCreate(BaseModel):
    business_unit_id: UUID | None = None
    group_name: str = Field(min_length=1, max_length=150)


class ApplicantGroupUpdate(BaseModel):
    business_unit_id: UUID | None = None
    group_name: str | None = Field(default=None, min_length=1, max_length=150)


class ApplicantGroupRead(ApplicantGroupCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ApplicantViewCreate(BaseModel):
    business_unit_id: UUID
    view_name: str = Field(min_length=1, max_length=150)
    is_default: bool = False
    filter_gdpr_consent: bool = False
    owner_user_id: UUID


class ApplicantViewUpdate(BaseModel):
    view_name: str | None = Field(default=None, min_length=1, max_length=150)
    is_default: bool | None = None
    filter_gdpr_consent: bool | None = None


class ApplicantViewRead(ApplicantViewCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class ApplicantViewColumnCreate(BaseModel):
    view_id: int | None = None
    folder_id: int | None = None
    column_key: str = Field(min_length=1, max_length=60)
    display_order: int = Field(ge=0)


class ApplicantViewColumnRead(ApplicantViewColumnCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ApplicantViewFilterCreate(BaseModel):
    view_id: int
    field_name: str = Field(min_length=1, max_length=60)
    operator: str = Field(min_length=1, max_length=20)
    filter_value: str | None = Field(default=None, max_length=500)
    display_order: int | None = None


class ApplicantViewFilterRead(ApplicantViewFilterCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ApplicantFolderCreate(BaseModel):
    business_unit_id: UUID
    folder_name: str = Field(min_length=1, max_length=150)
    owner_user_id: UUID


class ApplicantFolderRead(ApplicantFolderCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime | None


class ApplicantFolderMemberCreate(BaseModel):
    folder_id: int
    applicant_id: int
    added_by: UUID | None = None


class ApplicantFolderMemberRead(ApplicantFolderMemberCreate):
    model_config = ConfigDict(from_attributes=True)

    added_at: datetime | None


class ApplicantSearchHistoryCreate(BaseModel):
    user_id: UUID
    search_source: str = Field(min_length=1, max_length=20)
    history_type: SearchHistoryType
    search_name: str | None = Field(default=None, max_length=150)
    keywords: str | None = Field(default=None, max_length=1000)
    exclude_keywords: str | None = Field(default=None, max_length=1000)
    job_title: str | None = Field(default=None, max_length=200)
    recent_job_title_only: bool = False
    location_mode: str | None = Field(default=None, max_length=20)
    country_id: UUID | None = None
    state_id: UUID | None = None
    city: str | None = Field(default=None, max_length=100)
    include_without_country: bool = False
    advanced_options_json: dict[str, Any] | None = None


class ApplicantSearchHistoryRead(ApplicantSearchHistoryCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime | None


class ApplicantEmailCreate(BaseModel):
    applicant_id: int
    email_type: EmailType = EmailType.GENERAL
    job_id: UUID | None = None
    from_user_id: UUID
    to_email: str | None = Field(default=None, max_length=500)
    cc_email: str | None = Field(default=None, max_length=500)
    bcc_email: str | None = Field(default=None, max_length=500)
    subject: str | None = Field(default=None, max_length=500)
    body: str | None = None
    sent_at: datetime | None = None
    delivery_status: str | None = Field(default=None, max_length=15)


class ApplicantEmailRead(ApplicantEmailCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ApplicantDocumentCreate(BaseModel):
    applicant_id: int
    resume_parse_job_id: UUID | None = None
    document_type: str = Field(min_length=1, max_length=30)
    file_name: str = Field(min_length=1, max_length=300)
    storage_path: str = Field(min_length=1, max_length=600)
    mime_type: str | None = Field(default=None, max_length=100)
    file_size_bytes: int | None = Field(default=None, ge=0)
    is_primary_resume: bool = False
    is_parsed: bool = False
    comments: str | None = Field(default=None, max_length=1000)
    created_by: UUID | None = None


class ApplicantDocumentRead(ApplicantDocumentCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_by: UUID | None
    updated_at: datetime | None


class ApplicantResumeDownloadCreate(BaseModel):
    applicant_id: int
    document_id: int
    download_mode: str | None = Field(default=None, max_length=10)
    downloaded_by: UUID | None = None


class ApplicantResumeDownloadRead(ApplicantResumeDownloadCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    downloaded_at: datetime


class ApplicantRatingCreate(BaseModel):
    applicant_id: int
    submission_id: int | None = None
    technical_skills: int | None = Field(default=None, ge=1, le=5)
    communication_skills: int | None = Field(default=None, ge=1, le=5)
    professionalism: int | None = Field(default=None, ge=1, le=5)
    overall_rating: float | None = Field(default=None, ge=1, le=5)
    rated_by: UUID | None = None


class ApplicantRatingRead(ApplicantRatingCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rated_at: datetime | None


class ApplicantPipelineCreate(BaseModel):
    applicant_id: int
    job_id: UUID
    pipeline_status: str | None = Field(default=None, max_length=20)
    tagged_by: UUID | None = None
    tagged_at: datetime | None = None


class ApplicantPipelineRead(ApplicantPipelineCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
