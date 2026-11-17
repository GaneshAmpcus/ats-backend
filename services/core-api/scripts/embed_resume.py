"""Queue embeddings for an existing completed resume or retry a failed stage.

Run from core-api: python -m scripts.embed_resume JOB_UUID
Use --recover-processing only after confirming the old worker is no longer running.
"""
import argparse
from uuid import UUID

from sqlalchemy import update

from app.db.session import SessionLocal
from app.modules.resumes.models import ResumeParseJob
from app.modules.resumes.tasks import enqueue_embedding_job


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job_id", type=UUID)
    parser.add_argument("--recover-processing", action="store_true")
    args = parser.parse_args()
    with SessionLocal() as db:
        job = db.get(ResumeParseJob, args.job_id)
        if job is None or job.status != "completed":
            parser.error("Resume must exist and parsing must be completed")
        if job.embedding_status == "completed":
            print("Embeddings already completed; no work queued.")
            return
        if job.embedding_status == "processing" and not args.recover_processing:
            parser.error("Embedding is processing; confirm the old worker is stopped before recovery")
        # Compare-and-set prevents racing a worker claim between read and reset.
        result = db.execute(update(ResumeParseJob).where(
            ResumeParseJob.id == job.id, ResumeParseJob.embedding_status == job.embedding_status,
        ).values(embedding_status="pending", embedding_error=None, embedding_attempts=0))
        db.commit()
        if not result.rowcount:
            parser.error("State changed concurrently; inspect job status before retrying")
        try:
            enqueue_embedding_job(job.id)
        except Exception:
            db.execute(update(ResumeParseJob).where(
                ResumeParseJob.id == job.id, ResumeParseJob.embedding_status == "pending",
            ).values(embedding_status="failed", embedding_error="The embedding job could not be queued."))
            db.commit()
            raise
    print("Embedding task submitted. Poll the existing resume job endpoint.")


if __name__ == "__main__":
    main()
