from copy import deepcopy
from uuid import uuid4

from app.modules.resumes.chunking import build_resume_chunks


def test_chunks_preserve_source_and_separate_entries():
    parsed = {"personal_info": {"full_name": "Jane"}, "summary": "Engineer",
              "skills": ["Python"], "experience": [{"company": "A", "is_current": False},
              {"company": "B"}], "projects": [{"name": "One"}, {"name": "Two"}],
              "education": [{"degree": "BSc"}], "certifications": [{"name": "Course"}],
              "extra_original_field": {"keep": True}}
    original = deepcopy(parsed)
    resume_id = uuid4()
    chunks = build_resume_chunks(parsed, resume_id=resume_id, candidate_id="candidate-1")
    assert parsed == original
    assert len(chunks) == 8
    assert len({c["chunk_id"] for c in chunks}) == 8
    assert all(c["candidate_id"] == "candidate-1" and c["resume_id"] == str(resume_id) for c in chunks)
    assert "Company: A" in chunks[2]["text"] and "Company: B" not in chunks[2]["text"]
    assert "Is current: false" in chunks[2]["text"]
    assert chunks == build_resume_chunks(parsed, resume_id=resume_id, candidate_id="candidate-1")
    chunks[2]["metadata"]["source_fields"]["company"] = "Changed"
    assert parsed == original


def test_missing_sections_are_not_invented():
    assert build_resume_chunks({"summary": None, "projects": [{}]},
                               resume_id=uuid4(), candidate_id=None) == []
