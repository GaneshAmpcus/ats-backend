from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.llm.client import get_llm
from app.parsing.service import ResumeParsingError, parse_resume_text

router = APIRouter(tags=["parsing"])


class ParseResumeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=200_000)
    filename: str | None = Field(default=None, max_length=255)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Text cannot be blank")
        return value


@router.post("/parse-resume", summary="Extract structured candidate data from resume text")
def parse_resume(request: ParseResumeRequest) -> dict[str, Any]:
    """Extract only candidate fields consumed by the Core API resume flow."""
    try:
        result = parse_resume_text(request.text, llm=get_llm())
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail="The AI service is not configured to process resumes.",
        ) from exc
    except ResumeParsingError as exc:
        raise HTTPException(
            status_code=502,
            detail="The AI service could not parse this resume. Please retry.",
        ) from exc
    return result.model_dump()
