from typing import Any
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from app.integrations.ai_client import AIServiceClient, AIServiceError, get_ai_client

router = APIRouter(prefix="/jd", tags=["job descriptions"])
logger = logging.getLogger(__name__)

class RequestBody(BaseModel):
    model_config = ConfigDict(extra="allow")

@router.post("/generate")
@router.post("/enhance")
@router.post("/regenerate-section")
@router.post("/skills/suggest")
@router.post("/boolean-string")
def author_jd(request: Request, body: RequestBody, ai: AIServiceClient = Depends(get_ai_client)) -> dict[str, Any]:
    operation = request.url.path.rsplit("/", 1)[-1]
    try:
        return ai.jd_request(operation, body.model_dump())
    except AIServiceError as exc:
        status = 503 if not exc.retryable and "not configured" in str(exc) else (502 if exc.retryable else 400)
        logger.error("JD request failed at AI-service boundary (operation=%s, retryable=%s, status_code=%s, category=%s)", operation, exc.retryable, status, str(exc).split(".", 1)[0])
        raise HTTPException(status_code=status, detail="JD service is temporarily unavailable." if status >= 500 else "JD request was rejected.") from exc
