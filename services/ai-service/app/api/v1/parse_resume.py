from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

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


@router.post("/parse-resume", summary="Parse resume text (static placeholder response)")
def parse_resume(request: ParseResumeRequest) -> dict[str, Any]:
    """Temporary stub: returns fixed JSON so the backend pipeline can be tested end to end.

    Replace the body with the real parsing pipeline; keep the response shape stable.
    """
    return {
        "personal_info": {
            "full_name": "Jane Doe",
            "email": "jane.doe@example.com",
            "phone": "+1-555-0100",
            "location": "San Francisco, CA",
            "linkedin_url": "https://www.linkedin.com/in/janedoe",
        },
        "summary": "Software engineer with 6 years of experience building backend systems.",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
        "total_experience_years": 6.0,
        "experience": [
            {
                "title": "Senior Software Engineer",
                "company": "Example Corp",
                "start_date": "2021-03",
                "end_date": None,
                "is_current": True,
                "description": "Led development of internal platform services.",
            }
        ],
        "education": [
            {
                "degree": "B.S. Computer Science",
                "institution": "Example University",
                "start_year": 2014,
                "end_year": 2018,
            }
        ],
        "meta": {
            "is_stub": True,
            "received_characters": len(request.text),
            "filename": request.filename,
        },
    }
