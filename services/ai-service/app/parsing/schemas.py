"""Validated response shape shared by resume extraction prompts and the API."""

from pydantic import BaseModel, ConfigDict, Field


class PersonalInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None


class ExperienceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    company: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool | None = None
    description: str | None = None


class EducationItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    degree: str | None = None
    institution: str | None = None
    start_year: int | None = None
    end_year: int | None = None


class ProjectItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)
    url: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class CertificationItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    issuer: str | None = None
    issue_date: str | None = None
    expiry_date: str | None = None
    credential_id: str | None = None
    credential_url: str | None = None


class ResumeParseResult(BaseModel):
    """Fields persisted by Core API and exposed as the resume parse result."""

    model_config = ConfigDict(extra="forbid")

    personal_info: PersonalInfo = Field(default_factory=PersonalInfo)
    summary: str | None = None
    skills: list[str] = Field(default_factory=list)
    total_experience_years: float | None = None
    experience: list[ExperienceItem] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)
    certifications: list[CertificationItem] = Field(default_factory=list)
