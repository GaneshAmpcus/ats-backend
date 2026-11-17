"""Separate embedding stage; parsing results are never changed on failure."""
import logging
import math
import re
from datetime import datetime, timezone
from uuid import UUID, uuid5

from sqlalchemy import delete, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.integrations.ai_client import AIServiceError
from app.modules.resumes.models import ResumeChunkEmbedding, ResumeParseJob

logger = logging.getLogger(__name__)
DIMENSIONS = 384
SECTIONS = {"professional_summary", "skills", "work_experience", "project", "education", "certification"}


class EmbeddingRetryableError(Exception):
    pass


def embedding_chunks(job):
    """Sanitize embedding input without modifying source JSON or stored source chunks.

    Split long entries into bounded overlapping pieces, with stable IDs for upserts.
    Regex is best-effort for incidental contact text; known parsed contacts are
    explicitly removed. Source metadata is retained in resume_records, not sent to AI.
    """
    personal = (job.parsed_data or {}).get("personal_info") or {}
    output = []
    for chunk in job.vector_chunks:
        if chunk["section_type"] not in SECTIONS:
            continue
        text = re.sub(r"^Candidate: [^\n]*\n", "", chunk["text"])
        for key in ("email", "phone", "linkedin_url"):
            contact = personal.get(key)
            if contact:
                text = re.sub(re.escape(contact), "", text, flags=re.I)
        text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "", text)
        # Ten or more digits: avoid treating normal year/month ranges as phones.
        text = re.sub(r"(?<!\w)\+?\d[\d ().-]{7,}\d(?!\w)",
                      lambda m: "" if sum(c.isdigit() for c in m[0]) >= 10 else m[0], text)
        text = text.strip()
        if not text:
            continue
        for part, start in enumerate(range(0, len(text), 700)):
            piece = text[start:start + 800].strip()
            output.append({
                "chunk_id": uuid5(UUID(chunk["chunk_id"]), f"embedding-v1:{part}"),
                "resume_id": job.id, "candidate_id": job.candidate_id,
                "section_type": chunk["section_type"], "chunk_text": piece,
                "metadata": {"source_chunk_id": chunk["chunk_id"],
                             "source_path": chunk["metadata"]["source_path"],
                             "part": part, "embedding_text_version": 1},
            })
            if start + 800 >= len(text):
                break
    return output


def validate_vectors(payload, count, expected_model):
    vectors = payload.get("embeddings")
    if (payload.get("model") != expected_model or payload.get("dimensions") != DIMENSIONS
            or not isinstance(vectors, list) or len(vectors) != count):
        raise AIServiceError("Embedding model, dimensions or result count does not match.", retryable=False)
    for vector in vectors:
        if (not isinstance(vector, list) or len(vector) != DIMENSIONS
                or any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in vector)
                or not any(vector)):
            raise AIServiceError("AI service returned an invalid embedding vector.", retryable=False)
    return vectors


def process_embeddings(db: Session, job_id: UUID, *, ai_client, expected_model: str, max_attempts: int):
    claimed = db.execute(update(ResumeParseJob).where(
        ResumeParseJob.id == job_id, ResumeParseJob.status == "completed",
        ResumeParseJob.embedding_status == "pending",
    ).values(embedding_status="processing", embedding_error=None,
             embedding_attempts=ResumeParseJob.embedding_attempts + 1))
    db.commit()
    if not claimed.rowcount:
        return
    job = db.get(ResumeParseJob, job_id)
    db.refresh(job)
    try:
        chunks = embedding_chunks(job)
        rows = []
        for start in range(0, len(chunks), 32):
            batch = chunks[start:start + 32]
            payload = ai_client.embed_texts([c["chunk_text"] for c in batch])
            vectors = validate_vectors(payload, len(batch), expected_model)
            rows.extend(dict(c, embedding_model=expected_model, embedding=v) for c, v in zip(batch, vectors))
        # All batches validate before any write. Rows and status commit atomically.
        dialect = db.get_bind().dialect.name
        if dialect == "postgresql":
            from sqlalchemy.dialects.postgresql import insert
        elif dialect == "sqlite":
            from sqlalchemy.dialects.sqlite import insert
        else:
            raise ValueError("Unsupported embedding database")
        table = ResumeChunkEmbedding.__table__
        for row in rows:
            statement = insert(table).values(**row)
            db.execute(statement.on_conflict_do_update(
                index_elements=[table.c.chunk_id],
                set_={k: getattr(statement.excluded, k) for k in row if k != "chunk_id"},
            ))
        db.execute(delete(table).where(table.c.resume_id == job_id,
                                      table.c.chunk_id.not_in([r["chunk_id"] for r in rows])))
        job.embedding_status = "completed"
        job.embedding_count = len(rows)
        job.embedding_error = None
        job.embedding_completed_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as exc:
        db.rollback()
        db.refresh(job)
        retryable = (isinstance(exc, AIServiceError) and exc.retryable) or isinstance(exc, SQLAlchemyError)
        message = str(exc) if isinstance(exc, AIServiceError) else "Resume embedding could not be completed."
        retry = retryable and job.embedding_attempts < max_attempts
        job.embedding_status = "pending" if retry else "failed"
        job.embedding_error = message
        db.commit()
        if retry:
            raise EmbeddingRetryableError(message) from exc
        logger.warning("Resume embedding failed for %s (%s)", job_id, type(exc).__name__)
