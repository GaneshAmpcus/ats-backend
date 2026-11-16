"""Deterministic text preparation for backend embedding and pgvector indexing."""

from copy import deepcopy
from uuid import UUID, uuid5


def build_resume_chunks(parsed: dict, *, resume_id: UUID, candidate_id: str | None,
                        filename: str | None = None) -> list[dict]:
    """Never mutate the source JSON or infer absent facts; one chunk per entry."""
    chunks: list[dict] = []
    personal = parsed.get("personal_info") or {}
    name = personal.get("full_name") if isinstance(personal, dict) else None

    def add(section: str, index: int, value, path: str) -> None:
        if isinstance(value, dict):
            lines = []
            for key, item in value.items():
                if item is None or item == "" or item == [] or item == {}:
                    continue
                if isinstance(item, list):
                    text = ", ".join(str(v) for v in item if v is not None)
                elif isinstance(item, bool):
                    text = "true" if item else "false"
                else:
                    text = str(item)
                lines.append(f"{key.replace('_', ' ').capitalize()}: {text}")
            body = "\n".join(lines)
        elif isinstance(value, list):
            body = ", ".join(str(v) for v in value if v is not None and str(v).strip())
        else:
            body = str(value).strip() if value is not None else ""
        if not body:
            return
        context = f"Candidate: {name}\n" if name else ""
        chunks.append({
            "chunk_id": str(uuid5(resume_id, path)),
            "candidate_id": candidate_id,
            "resume_id": str(resume_id),
            "section_type": section,
            "text": f"{context}{section.replace('_', ' ').capitalize()}\n{body}",
            "metadata": {"source_path": path, "section_index": index,
                         "filename": filename, "chunking_version": 1,
                         "source_fields": deepcopy(value)},
        })

    add("professional_summary", 0, parsed.get("summary"), "summary")
    add("skills", 0, parsed.get("skills"), "skills")
    for field, section in (("experience", "work_experience"), ("projects", "project"),
                           ("education", "education"), ("certifications", "certification")):
        for index, entry in enumerate(parsed.get(field) or []):
            add(section, index, entry, f"{field}[{index}]")
    return chunks
