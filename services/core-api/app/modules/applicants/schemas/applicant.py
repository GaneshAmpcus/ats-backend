"""API schemas for applicant records."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.applicants.enums import CreationMethod


class ApplicantCreate(BaseModel):
    """Create an applicant. Service code supplies business defaults/master IDs."""

    business_unit_id: UUID
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date
    email: str = Field(min_length=1, max_length=255)
    mobile_number: str = Field(min_length=1, max_length=25)
    source_id: UUID
    applicant_status_id: UUID
    salutation: str | None = Field(default=None, max_length=10)
    middle_name: str | None = Field(default=None, max_length=100)
    legal_name: str | None = Field(default=None, max_length=255)
    maiden_name: str | None = Field(default=None, max_length=100)
    profile_photo_url: str | None = Field(default=None, max_length=500)
    alternate_email: str | None = Field(default=None, max_length=255)
    mobile_number_e164: str | None = Field(default=None, max_length=20)
    home_phone: str | None = Field(default=None, max_length=25)
    work_phone: str | None = Field(default=None, max_length=25)
    other_phone: str | None = Field(default=None, max_length=25)
    linkedin_url: str | None = Field(default=None, max_length=500)
    facebook_url: str | None = Field(default=None, max_length=500)
    twitter_url: str | None = Field(default=None, max_length=500)
    video_reference_url: str | None = Field(default=None, max_length=500)
    address: str | None = Field(default=None, max_length=500)
    country_id: UUID | None = None
    state_id: UUID | None = None
    city: str | None = Field(default=None, max_length=100)
    zip_code: str | None = Field(default=None, max_length=20)
    work_authorization_id: UUID | None = None
    relocation: bool = True
    referred_by: str | None = Field(default=None, max_length=150)
    applicant_group_id: int | None = None
    owner_user_id: UUID | None = None
    current_title: str | None = Field(default=None, max_length=200)
    current_company: str | None = Field(default=None, max_length=200)
    experience_years: int | None = Field(default=None, ge=0, le=60)
    experience_months: int | None = Field(default=None, ge=0, le=11)
    relevant_experience: str | None = Field(default=None, max_length=50)
    current_ctc_currency: str | None = Field(default="INR", max_length=3)
    current_ctc_amount: Decimal | None = Field(default=None, ge=0)
    current_ctc_period: str | None = Field(default=None, max_length=15)
    expected_ctc_currency: str | None = Field(default="INR", max_length=3)
    expected_ctc_amount: Decimal | None = Field(default=None, ge=0)
    expected_ctc_period: str | None = Field(default=None, max_length=15)
    notice_period_id: UUID | None = None
    preferred_shift_id: UUID | None = None
    industry_id: UUID | None = None
    technology: str | None = Field(default=None, max_length=255)
    applicant_remarks: str | None = None
    reference_id: str | None = Field(default=None, max_length=50)
    pan_number: str | None = None
    aadhaar_number: str | None = None
    passport_number: str | None = None
    marital_status_id: UUID | None = None
    nationality_id: UUID | None = None
    gender_id: UUID | None = None
    race_ethnicity_id: UUID | None = None
    veteran_status_id: UUID | None = None
    disability_id: UUID | None = None
    is_email_merge_active: bool = True
    is_portal_account_active: bool = False
    creation_method: CreationMethod = CreationMethod.MANUAL
    is_sms_blocked: bool = False
    gdpr_consent_approved: bool = False
    gdpr_consent_at: datetime | None = None

    @model_validator(mode="after")
    def require_city_for_manual_entry(self) -> "ApplicantCreate":
        if self.creation_method == CreationMethod.MANUAL and not self.city:
            raise ValueError("city is required for manually created applicants")
        return self


class ApplicantUpdate(BaseModel):
    """Partial applicant update; omitted fields remain unchanged."""

    business_unit_id: UUID | None = None
    salutation: str | None = Field(default=None, max_length=10)
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    middle_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    legal_name: str | None = Field(default=None, max_length=255)
    maiden_name: str | None = Field(default=None, max_length=100)
    profile_photo_url: str | None = Field(default=None, max_length=500)
    date_of_birth: date | None = None
    email: str | None = Field(default=None, min_length=1, max_length=255)
    alternate_email: str | None = Field(default=None, max_length=255)
    mobile_number: str | None = Field(default=None, min_length=1, max_length=25)
    mobile_number_e164: str | None = Field(default=None, max_length=20)
    home_phone: str | None = Field(default=None, max_length=25)
    work_phone: str | None = Field(default=None, max_length=25)
    other_phone: str | None = Field(default=None, max_length=25)
    linkedin_url: str | None = Field(default=None, max_length=500)
    facebook_url: str | None = Field(default=None, max_length=500)
    twitter_url: str | None = Field(default=None, max_length=500)
    video_reference_url: str | None = Field(default=None, max_length=500)
    address: str | None = Field(default=None, max_length=500)
    country_id: UUID | None = None
    state_id: UUID | None = None
    city: str | None = Field(default=None, max_length=100)
    zip_code: str | None = Field(default=None, max_length=20)
    work_authorization_id: UUID | None = None
    relocation: bool | None = None
    source_id: UUID | None = None
    referred_by: str | None = Field(default=None, max_length=150)
    applicant_status_id: UUID | None = None
    applicant_group_id: int | None = None
    owner_user_id: UUID | None = None
    current_title: str | None = Field(default=None, max_length=200)
    current_company: str | None = Field(default=None, max_length=200)
    experience_years: int | None = Field(default=None, ge=0, le=60)
    experience_months: int | None = Field(default=None, ge=0, le=11)
    relevant_experience: str | None = Field(default=None, max_length=50)
    current_ctc_currency: str | None = Field(default=None, max_length=3)
    current_ctc_amount: Decimal | None = Field(default=None, ge=0)
    current_ctc_period: str | None = Field(default=None, max_length=15)
    expected_ctc_currency: str | None = Field(default=None, max_length=3)
    expected_ctc_amount: Decimal | None = Field(default=None, ge=0)
    expected_ctc_period: str | None = Field(default=None, max_length=15)
    notice_period_id: UUID | None = None
    preferred_shift_id: UUID | None = None
    industry_id: UUID | None = None
    technology: str | None = Field(default=None, max_length=255)
    applicant_remarks: str | None = None
    reference_id: str | None = Field(default=None, max_length=50)
    pan_number: str | None = None
    aadhaar_number: str | None = None
    passport_number: str | None = None
    marital_status_id: UUID | None = None
    nationality_id: UUID | None = None
    gender_id: UUID | None = None
    race_ethnicity_id: UUID | None = None
    veteran_status_id: UUID | None = None
    disability_id: UUID | None = None
    is_email_merge_active: bool | None = None
    is_portal_account_active: bool | None = None
    creation_method: CreationMethod | None = None
    is_sms_blocked: bool | None = None
    gdpr_consent_approved: bool | None = None
    gdpr_consent_at: datetime | None = None


class ApplicantRead(BaseModel):
    """Applicant response. Sensitive identity values are intentionally omitted."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    business_unit_id: UUID
    salutation: str | None
    first_name: str
    middle_name: str | None
    last_name: str
    full_name: str
    legal_name: str | None
    maiden_name: str | None
    profile_photo_url: str | None
    date_of_birth: date
    email: str
    alternate_email: str | None
    mobile_number: str
    mobile_number_e164: str | None
    home_phone: str | None
    work_phone: str | None
    other_phone: str | None
    linkedin_url: str | None
    facebook_url: str | None
    twitter_url: str | None
    video_reference_url: str | None
    address: str | None
    country_id: UUID | None
    state_id: UUID | None
    city: str | None
    zip_code: str | None
    work_authorization_id: UUID | None
    relocation: bool
    source_id: UUID
    referred_by: str | None
    applicant_status_id: UUID
    applicant_group_id: int | None
    owner_user_id: UUID | None
    current_title: str | None
    current_company: str | None
    experience_years: int | None
    experience_months: int | None
    relevant_experience: str | None
    current_ctc_currency: str | None
    current_ctc_amount: Decimal | None
    current_ctc_period: str | None
    expected_ctc_currency: str | None
    expected_ctc_amount: Decimal | None
    expected_ctc_period: str | None
    notice_period_id: UUID | None
    preferred_shift_id: UUID | None
    industry_id: UUID | None
    technology: str | None
    applicant_remarks: str | None
    reference_id: str | None
    marital_status_id: UUID | None
    nationality_id: UUID | None
    gender_id: UUID | None
    race_ethnicity_id: UUID | None
    veteran_status_id: UUID | None
    disability_id: UUID | None
    is_email_merge_active: bool
    is_portal_account_active: bool
    creation_method: CreationMethod
    is_sms_blocked: bool
    gdpr_consent_approved: bool
    gdpr_consent_at: datetime | None
    created_by: UUID | None
    modified_by: UUID | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class ApplicantListItem(BaseModel):
    """Small payload for applicant search/list screens."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    mobile_number: str
    current_title: str | None
    current_company: str | None
    city: str | None
    applicant_status_id: UUID
    owner_user_id: UUID | None
    created_at: datetime
