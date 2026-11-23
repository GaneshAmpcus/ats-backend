import json
import pytest
from pydantic import ValidationError

from app.parsing.jd_generation import _try_extract_json, generate_job_description
from app.parsing.schemas_jd import JDInput, JDSections


def _headers() -> dict[str, str]:
    return {"X-API-Key": "test-key"}


def _result() -> dict:
    return {
        "job_overview": "Senior Python Engineer in Pune, India.",
        "about_the_role": "Build backend services for the platform.",
        "key_responsibilities": ["Design and maintain APIs."],
        "required_technical_skills": ["Python", "FastAPI"],
        "preferred_skills": ["AWS"],
        "educational_qualifications": ["As supplied by recruiter"],
        "experience_requirements": "5-7 years",
        "technical_requirements": ["Python", "FastAPI"],
        "soft_skills": [],
        "what_we_offer": [],
        "additional_information": [],
        "recruiter_provided": {"job_title": "Senior Python Engineer"},
        "ai_suggestions": {"responsibilities": [], "skills": []},
    }


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------

def test_generate_returns_structured_role_specific_jd(client, monkeypatch):
    captured = {}

    class FakeStructured:
        def invoke(self, messages):
            captured["messages"] = messages
            return _result()

    class FakeLLM:
        def with_structured_output(self, schema, *, method):
            captured["schema"] = schema
            captured["method"] = method
            return FakeStructured()

    monkeypatch.setattr("app.api.v1.jd.get_llm", lambda: FakeLLM())
    response = client.post("/api/v1/jd/generate", headers=_headers(), json={
        "job_title": "Senior Python Engineer", "job_location": "Pune, India",
        "experience_range": "5-7 years", "required_skills": ["Python", "FastAPI"],
        "preferred_skills": ["AWS"], "responsibilities": ["Build APIs"],
    })

    assert response.status_code == 200
    assert response.json() == _result()
    assert captured["schema"].__name__ == "JDSections"
    # Must use function_calling, NOT json_schema (open-dict fields in JDSections
    # are incompatible with Groq's strict json_schema constrained-decoding mode).
    assert captured["method"] == "function_calling"
    assert "Senior Python Engineer" in captured["messages"][-1].content
    assert "Pune, India" in captured["messages"][-1].content


def test_generate_prompt_contains_jdsections_schema(client, monkeypatch):
    """The system prompt must embed the JDSections JSON schema so the model
    knows the exact structure to return even without strict constrained decoding."""
    captured = {}

    class FakeStructured:
        def invoke(self, messages):
            captured["messages"] = messages
            return _result()

    class FakeLLM:
        def with_structured_output(self, schema, *, method):
            return FakeStructured()

    monkeypatch.setattr("app.api.v1.jd.get_llm", lambda: FakeLLM())
    client.post("/api/v1/jd/generate", headers=_headers(), json={"job_title": "DevOps Engineer"})

    system_msg = captured["messages"][0].content
    # Schema key names must appear in the system prompt.
    for key in ("job_overview", "key_responsibilities", "recruiter_provided", "ai_suggestions"):
        assert key in system_msg, f"Expected schema key '{key}' missing from system prompt"


# ---------------------------------------------------------------------------
# Input validation tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("payload", [
    {},
    {"job_title": "X"},
    {"job_title": "Backend Engineer", "number_of_openings": 0},
    {"job_title": "Backend Engineer", "surprise": "ignored?"},
    {"job_title": "Backend Engineer", "additional_instructions": "x" * 4001},
])
def test_generate_rejects_invalid_input(client, payload):
    response = client.post("/api/v1/jd/generate", headers=_headers(), json=payload)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# LLM / provider failure tests
# ---------------------------------------------------------------------------

def test_generate_maps_llm_failure(client, monkeypatch):
    class BrokenLLM:
        def with_structured_output(self, schema, *, method):
            raise RuntimeError("provider detail must not leak")

    monkeypatch.setattr("app.api.v1.jd.get_llm", lambda: BrokenLLM())
    response = client.post("/api/v1/jd/generate", headers=_headers(), json={"job_title": "Backend Engineer"})
    assert response.status_code == 502
    assert "provider detail" not in response.text


def test_generate_rejects_invalid_structured_model_response(client, monkeypatch):
    class InvalidStructured:
        def invoke(self, messages):
            return {"job_overview": "only one field"}

    class FakeLLM:
        def with_structured_output(self, schema, *, method):
            return InvalidStructured()

    monkeypatch.setattr("app.api.v1.jd.get_llm", lambda: FakeLLM())
    response = client.post("/api/v1/jd/generate", headers=_headers(), json={"job_title": "Backend Engineer"})
    assert response.status_code == 502


def test_generate_requires_service_key(client):
    response = client.post("/api/v1/jd/generate", json={"job_title": "Backend Engineer"})
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# _try_extract_json unit tests (fallback extraction helper)
# ---------------------------------------------------------------------------

def test_try_extract_json_plain_json():
    payload = {"job_overview": "hello", "about_the_role": "world"}
    assert _try_extract_json(json.dumps(payload)) == payload


def test_try_extract_json_markdown_fence():
    payload = {"job_overview": "hi"}
    raw = f"```json\n{json.dumps(payload)}\n```"
    assert _try_extract_json(raw) == payload


def test_try_extract_json_prose_prefix():
    payload = {"key": "value"}
    raw = f"Here is the JSON output:\n{json.dumps(payload)}\nDone."
    assert _try_extract_json(raw) == payload


def test_try_extract_json_invalid_returns_none():
    assert _try_extract_json("This is not JSON at all.") is None
    assert _try_extract_json("") is None
    assert _try_extract_json("```json\n{bad json\n```") is None


# ---------------------------------------------------------------------------
# generate_job_description unit-level tests (service function, not HTTP)
# ---------------------------------------------------------------------------

def _make_input(**kwargs) -> JDInput:
    return JDInput(job_title="Python Dev", **kwargs)


def test_service_returns_jdsections_when_llm_returns_dict(monkeypatch):
    """If with_structured_output returns a plain dict, the service must
    validate and return a JDSections instance."""
    class FakeChain:
        def invoke(self, _):
            return _result()

    class FakeLLM:
        def with_structured_output(self, schema, *, method):
            assert method == "function_calling"
            return FakeChain()

    from app.parsing import jd_generation
    result = jd_generation.generate_job_description(_make_input(), llm=FakeLLM())
    assert isinstance(result, JDSections)
    assert result.job_overview == "Senior Python Engineer in Pune, India."


def test_service_returns_jdsections_when_llm_returns_instance(monkeypatch):
    """If with_structured_output already returns a JDSections instance the
    service must pass it through unchanged."""
    jd = JDSections(**_result())

    class FakeChain:
        def invoke(self, _):
            return jd

    class FakeLLM:
        def with_structured_output(self, schema, *, method):
            return FakeChain()

    from app.parsing import jd_generation
    result = jd_generation.generate_job_description(_make_input(), llm=FakeLLM())
    assert result is jd


def test_service_fallback_extraction_on_output_parser_exception():
    """If the LLM chain raises an OutputParserException that carries the raw
    JSON in llm_output, the service must recover via _try_extract_json."""
    from app.parsing import jd_generation

    class FakeParseError(Exception):
        llm_output = json.dumps(_result())

    class FakeChain:
        def invoke(self, _):
            raise FakeParseError("Failed to parse")

    class FakeLLM:
        def with_structured_output(self, schema, *, method):
            return FakeChain()

    result = jd_generation.generate_job_description(_make_input(), llm=FakeLLM())
    assert isinstance(result, JDSections)


def test_service_raises_jd_generation_error_when_no_fallback():
    """When the LLM chain raises and no parseable raw output is attached,
    JDGenerationError must be raised (not the original exception)."""
    from app.parsing import jd_generation
    from app.parsing.jd_generation import JDGenerationError

    class FakeChain:
        def invoke(self, _):
            raise ValueError("completely unexpected")

    class FakeLLM:
        def with_structured_output(self, schema, *, method):
            return FakeChain()

    with pytest.raises(JDGenerationError):
        jd_generation.generate_job_description(_make_input(), llm=FakeLLM())

