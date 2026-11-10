import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.llm.client import get_llm

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


class LLMTestRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message cannot be blank")
        return value


@router.get("/health", summary="Check service health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/llm-test", summary="Send a message to the LLM")
def llm_test(request: LLMTestRequest) -> dict[str, str]:
    try:
        response = get_llm().invoke(request.message)
    except Exception as exc:
        logger.exception("LLM test request failed")
        raise HTTPException(status_code=502, detail="LLM request failed") from exc

    if not isinstance(response.content, str) or not response.content.strip():
        raise HTTPException(status_code=502, detail="LLM returned an empty response")

    return {"response": response.content}
