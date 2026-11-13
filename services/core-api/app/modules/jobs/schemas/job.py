from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.jobs.enums import JobStatus


class JobBase(BaseModel):
    job_title: str
    client_job_id: str | None = None
    job_description: str | None = None
    status: JobStatus = JobStatus.ACTIVE
    job_start_date: date | None = None
    job_end_date: date | None = None
    respond_by: datetime | None = None
    duration: int | None = None
    duration_unit: str | None = None
    experience_min: Decimal | None = None
    experience_max: Decimal | None = None
    min_salary: Decimal | None = None
    max_salary: Decimal | None = None
    currency_code: str | None = None
    client_bill_rate: Decimal | None = None
    client_bill_rate_type: str | None = None
    number_of_positions: int = 1
    maximum_allowed_submissions: int | None = None
    hit_quota: int | None = None
    remote_job: bool = False
    is_hot_job: bool = False
    comments: str | None = None
    client_id: UUID | None = None
    business_unit_id: UUID | None = None
    client_practice_id: UUID | None = None
    industry_id: UUID | None = None
    job_category_id: UUID | None = None
    job_type_id: UUID | None = None
    priority_id: UUID | None = None
    clearance_id: UUID | None = None
    notice_period_id: UUID | None = None


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    job_title: str | None = None
    client_job_id: str | None = None
    job_description: str | None = None
    job_start_date: date | None = None
    job_end_date: date | None = None
    respond_by: datetime | None = None
    duration: int | None = None
    duration_unit: str | None = None
    experience_min: Decimal | None = None
    experience_max: Decimal | None = None
    min_salary: Decimal | None = None
    max_salary: Decimal | None = None
    currency_code: str | None = None
    client_bill_rate: Decimal | None = None
    client_bill_rate_type: str | None = None
    number_of_positions: int | None = None
    maximum_allowed_submissions: int | None = None
    hit_quota: int | None = None
    remote_job: bool | None = None
    is_hot_job: bool | None = None
    comments: str | None = None
    client_id: UUID | None = None
    business_unit_id: UUID | None = None
    client_practice_id: UUID | None = None
    industry_id: UUID | None = None
    job_category_id: UUID | None = None
    job_type_id: UUID | None = None
    priority_id: UUID | None = None
    clearance_id: UUID | None = None
    notice_period_id: UUID | None = None


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_code: str
    job_title: str
    client_job_id: str | None
    job_description: str | None
    status: JobStatus
    job_start_date: date | None
    job_end_date: date | None
    respond_by: datetime | None
    duration: int | None
    duration_unit: str | None
    experience_min: Decimal | None
    experience_max: Decimal | None
    min_salary: Decimal | None
    max_salary: Decimal | None
    currency_code: str | None
    client_bill_rate: Decimal | None
    client_bill_rate_type: str | None
    number_of_positions: int
    maximum_allowed_submissions: int | None
    hit_quota: int | None
    remote_job: bool
    is_hot_job: bool
    comments: str | None
    client_id: UUID | None
    business_unit_id: UUID | None
    client_practice_id: UUID | None
    industry_id: UUID | None
    job_category_id: UUID | None
    job_type_id: UUID | None
    priority_id: UUID | None
    clearance_id: UUID | None
    notice_period_id: UUID | None
    created_by: UUID | None
    modified_by: UUID | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class JobListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_code: str
    job_title: str
    status: JobStatus
    client_id: UUID | None
    created_at: datetime
