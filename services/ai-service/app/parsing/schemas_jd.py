"""Typed request and response contracts for JD authoring."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class JDInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    job_title: str = Field(min_length=2, max_length=255)
    department: str | None = Field(default=None, max_length=120)
    industry: str | None = Field(default=None, max_length=120)
    employment_type: str | None = Field(default=None, max_length=80)
    work_mode: str | None = Field(default=None, max_length=80)
    job_location: str | None = Field(default=None, max_length=255)
    experience_range: str | None = Field(default=None, max_length=100)
    number_of_openings: int | None = Field(default=None, ge=1, le=10000)
    educational_qualifications: list[str] = Field(default_factory=list, max_length=30)
    primary_skills: list[str] = Field(default_factory=list, max_length=100)
    secondary_skills: list[str] = Field(default_factory=list, max_length=100)
    required_skills: list[str] = Field(default_factory=list, max_length=100)
    preferred_skills: list[str] = Field(default_factory=list, max_length=100)
    responsibilities: list[str] = Field(default_factory=list, max_length=100)
    salary_range: str | None = Field(default=None, max_length=120)
    additional_instructions: str | None = Field(default=None, max_length=4000)


class JDSections(BaseModel):
    model_config = ConfigDict(extra="forbid")
    job_overview: str
    about_the_role: str
    key_responsibilities: list[str]
    required_technical_skills: list[str]
    preferred_skills: list[str]
    educational_qualifications: list[str]
    experience_requirements: str | None
    technical_requirements: list[str]
    soft_skills: list[str]
    what_we_offer: list[str]
    additional_information: list[str]
    recruiter_provided: dict[str, object]
    ai_suggestions: dict[str, list[str]]


class EnhanceRequest(BaseModel):
    text: str = Field(min_length=20, max_length=30000)
    instructions: str | None = Field(default=None, max_length=2000)


class RegenerateSectionRequest(BaseModel):
    sections: JDSections
    section: Literal["job_overview", "about_the_role", "key_responsibilities", "required_technical_skills", "preferred_skills", "educational_qualifications", "experience_requirements", "technical_requirements", "soft_skills", "what_we_offer", "additional_information"]
    instructions: str | None = Field(default=None, max_length=2000)


class SkillsRequest(BaseModel):
    job_title: str = Field(min_length=2, max_length=255)
    requirements: list[str] = Field(default_factory=list, max_length=100)


class BooleanRequest(BaseModel):
    job_title: str = Field(min_length=2, max_length=255)
    required_skills: list[str] = Field(default_factory=list, max_length=100)
    preferred_skills: list[str] = Field(default_factory=list, max_length=100)
    excluded_terms: list[str] = Field(default_factory=list, max_length=100)
    customization: str | None = Field(default=None, max_length=2000)
