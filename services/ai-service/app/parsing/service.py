"""Application service for extracting candidate data from resume text."""

import logging
from datetime import datetime, timezone

from langchain_core.language_models import BaseChatModel
from app.llm.prompts.resume import RESUME_PARSE_PROMPT
from app.parsing.schemas import ResumeParseResult
from app.parsing.validators import normalize_result

logger = logging.getLogger(__name__)


class ResumeParsingError(Exception):
    """Raised when the model cannot produce a valid resume parse result."""


def parse_resume_text(text: str, *, llm: BaseChatModel) -> ResumeParseResult:
    """Run the structured LLM extraction, validate it and apply deterministic fixes."""
    today = datetime.now(timezone.utc).date()
    try:
        # Request JSON directly: tool calling can fail when the model does not
        # emit the required tool call, even for otherwise valid resume text.
        response = llm.with_structured_output(
            ResumeParseResult, method="json_schema", include_raw=True
        ).invoke(
            RESUME_PARSE_PROMPT.format_messages(
                resume_text=text, current_date=today.isoformat()
            )
        )
        if response["raw"].response_metadata.get("finish_reason") == "length":
            raise ValueError("Resume output exceeded the model token budget")
        if response["parsing_error"] is not None:
            raise response["parsing_error"]
        result = response["parsed"]
        if result is None:
            raise ValueError("Model returned no structured resume")
        if not isinstance(result, ResumeParseResult):
            result = ResumeParseResult.model_validate(result)
    except Exception as exc:
        # Provider exception text can contain resume data; log metadata only.
        logger.warning(
            "Resume extraction failed (error_type=%s, status_code=%s)",
            type(exc).__name__,
            getattr(exc, "status_code", None),
        )
        raise ResumeParsingError("The resume could not be parsed by the AI service.") from exc

    try:
        return normalize_result(result.model_copy(deep=True), today)
    except Exception:
        # Post-processing is an improvement, never a reason to fail a valid parse.
        logger.exception("Resume post-processing failed; returning raw model result.")
        return result
