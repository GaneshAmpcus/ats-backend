"""JD generation application service using the configured chat model."""
import json
import logging
import re

from langchain_core.language_models import BaseChatModel
from pydantic import ValidationError

from app.llm.prompts.jd import JD_GENERATION_PROMPT
from app.parsing.schemas_jd import JDInput, JDSections

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Structured-output method selection
# ---------------------------------------------------------------------------
# Groq's native `json_schema` mode (constrained-decoding) requires that every
# nested object in the JSON Schema has `"additionalProperties": false`.
# `JDSections` contains two open-dict fields:
#   - `recruiter_provided: dict[str, object]`   → "additionalProperties": true
#   - `ai_suggestions:     dict[str, list[str]]` → "additionalProperties": {...}
#
# Sending those schemas via json_schema mode causes Groq to reject the request
# (HTTP 400) or return malformed JSON, producing an `OutputParserException`.
#
# `function_calling` (tool-call) mode does NOT apply the same strict constraint
# on additionalProperties, works across every Groq model, and still delivers
# a reliably structured response.  It is the safe default for this schema.
_STRUCTURED_OUTPUT_METHOD = "function_calling"


class JDGenerationError(Exception):
    """The provider failed or returned an invalid structured JD."""


def _safe_provider_error(exc: Exception) -> str:
    """Return useful provider diagnostics without logging credentials or payloads."""
    message = str(exc)
    message = re.sub(r"gsk_[A-Za-z0-9_-]+", "[REDACTED]", message)
    message = re.sub(r"Bearer\s+\S+", "Bearer [REDACTED]", message, flags=re.IGNORECASE)
    message = re.sub(r"(?i)(api[_ -]?key|authorization)(\s*[:=]\s*)[^\s,;]+", r"\1\2[REDACTED]", message)
    return message[:500]


def _safe_truncate(text: str, max_chars: int = 400) -> str:
    """Truncate a string for safe log output."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"... [truncated, total={len(text)} chars]"


def _try_extract_json(raw: str) -> dict | None:
    """
    Best-effort extraction of a JSON object from a raw LLM string.

    Handles:
    - Pure JSON responses.
    - JSON wrapped in markdown fences (```json ... ```).
    - Responses with leading/trailing prose.

    Returns the parsed dict on success, or None if no valid JSON object found.
    Does NOT raise.
    """
    # 1. Try direct parse first (cheapest path).
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # 2. Strip markdown fences and retry.
    fenced = re.search(r"```(?:json)?\s*(\{.*?})\s*```", raw, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass

    # 3. Find the outermost {...} block.
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(raw[start : end + 1])
        except json.JSONDecodeError:
            pass

    return None


def generate_job_description(requirements: JDInput, *, llm: BaseChatModel) -> JDSections:
    """
    Call the LLM to generate a structured JDSections object.

    Strategy
    --------
    1. Use `with_structured_output(method="function_calling")` — the only
       mode that is universally supported on Groq and tolerates open-dict
       fields in the Pydantic schema without triggering a 400 or parse error.
    2. If the LLM chain returns a plain dict instead of a JDSections instance
       (can happen when the tool-call response is returned as raw JSON),
       attempt Pydantic validation directly.
    3. If `with_structured_output` itself raises an `OutputParserException`
       or similar parse error, attempt to recover by extracting a JSON blob
       from the raw message content and validating it against JDSections.
    4. Log the raw LLM output at DEBUG level (safely truncated) whenever a
       parse error occurs so engineers can diagnose schema mismatches without
       exposing sensitive data in production logs.
    5. Any remaining failure raises JDGenerationError with a safe message.
    """
    messages = JD_GENERATION_PROMPT.format_messages(
        requirements=requirements.model_dump_json()
    )

    # --- Primary path: structured output via function-calling tool mode ------
    try:
        result = llm.with_structured_output(
            JDSections, method=_STRUCTURED_OUTPUT_METHOD
        ).invoke(messages)

        if result is None:
            raise ValueError("Model returned no JD output (None response)")

        if isinstance(result, JDSections):
            return result

        # LangChain sometimes returns a dict even with a Pydantic schema.
        try:
            return JDSections.model_validate(result)
        except ValidationError as val_exc:
            logger.warning(
                "JD generation: structured output returned a dict that failed "
                "JDSections validation (error_count=%d, detail=%s)",
                val_exc.error_count(),
                _safe_truncate(str(val_exc)),
            )
            raise  # re-raise to outer except

    except Exception as primary_exc:  # noqa: BLE001
        # --- Fallback: attempt raw-content JSON extraction ------------------
        # LangChain wraps parse failures as OutputParserException and attaches
        # the raw LLM response on `llm_output` or `observation`.  We try to
        # pull that content and parse it ourselves.
        raw_content: str | None = None
        for attr in ("llm_output", "observation", "text"):
            raw_content = getattr(primary_exc, attr, None)
            if raw_content:
                break

        if raw_content:
            logger.debug(
                "JD generation: primary parse failed (%s), attempting JSON "
                "extraction from raw LLM output: %s",
                type(primary_exc).__name__,
                _safe_truncate(raw_content),
            )
            extracted = _try_extract_json(raw_content)
            if extracted:
                try:
                    return JDSections.model_validate(extracted)
                except ValidationError as fallback_val_exc:
                    logger.warning(
                        "JD generation: fallback JSON extraction succeeded but "
                        "JDSections validation failed (error_count=%d, detail=%s)",
                        fallback_val_exc.error_count(),
                        _safe_truncate(str(fallback_val_exc)),
                    )
            else:
                logger.warning(
                    "JD generation: could not extract a JSON object from raw "
                    "LLM output (output_length=%d)",
                    len(raw_content),
                )
        else:
            logger.debug(
                "JD generation: primary parse failed (%s) and no raw LLM "
                "content was available for fallback extraction",
                type(primary_exc).__name__,
            )

        # --- Log and surface a clean error ----------------------------------
        status_code = getattr(primary_exc, "status_code", None)
        error_code = getattr(primary_exc, "code", None)
        safe_message = _safe_provider_error(primary_exc)
        logger.error(
            "JD generation failed (provider=groq, method=%s, "
            "error_type=%s, status_code=%s, error_code=%s, detail=%s)",
            _STRUCTURED_OUTPUT_METHOD,
            type(primary_exc).__name__,
            status_code,
            error_code,
            safe_message,
        )
        raise JDGenerationError(
            "The job description could not be generated."
        ) from primary_exc
