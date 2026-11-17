"""Opt-in real PostgreSQL migration/storage check, rolled back in a unique schema.

RUN_PGVECTOR_TESTS=1 python -m pytest tests/test_pgvector_integration.py -q
Uses APP_DATABASE_URL. Requires pgvector already installed; no user data is touched.
"""
import importlib.util
import os
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import text
from sqlalchemy.orm import Session

pytestmark = pytest.mark.skipif(os.getenv("RUN_PGVECTOR_TESTS") != "1", reason="Opt-in PostgreSQL integration")


def test_migration_and_vector_roundtrip():
    from app.db.session import engine
    from app.modules.resumes import repository
    from app.modules.resumes.embedding import process_embeddings
    from app.modules.resumes.models import ResumeParseJob
    schema = "embedding_test_" + uuid4().hex
    path = Path(__file__).parents[1] / "alembic/versions/8d1c4a2b6e90_resume_embeddings.py"
    spec = importlib.util.spec_from_file_location("embedding_migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            assert connection.execute(text("SELECT 1 FROM pg_extension WHERE extname='vector'")).scalar() == 1
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            connection.execute(text(f'SET LOCAL search_path TO "{schema}", public'))
            with Operations.context(MigrationContext.configure(connection)):
                migration.upgrade()
                # Existing local tables are adopted without destructive replacement.
                migration.upgrade()
            with Session(bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False) as db:
                job = ResumeParseJob(id=uuid4(), original_filename="synthetic.txt", content_type="text/plain",
                                     file_size=10, file_sha256="0" * 64, storage_key="synthetic.txt")
                repository.add_job(db, job)
                db.commit()
                repository.mark_completed(db, job, {"skills": ["Python", "PostgreSQL"]})
                class AI:
                    def embed_texts(self, texts):
                        return {"model": "test-model", "dimensions": 384,
                                "embeddings": [[1.0] + [0.0] * 383 for _ in texts]}
                for _ in range(2):
                    job.embedding_status = "pending"
                    db.commit()
                    process_embeddings(db, job.id, ai_client=AI(), expected_model="test-model", max_attempts=2)
                    assert job.embedding_status == "completed" and job.embedding_count == 1
                result = db.execute(text("SELECT vector_dims(embedding), count(*) OVER () FROM resume_chunk_embeddings")).one()
                assert tuple(result) == (384, 1)
                assert db.execute(text("SELECT indexname FROM pg_indexes WHERE schemaname=:schema AND indexname='resume_chunk_embeddings_cosine_idx'"), {"schema": schema}).scalar()
            with Operations.context(MigrationContext.configure(connection)):
                migration.downgrade()
            assert connection.execute(text("SELECT to_regclass(:name)"), {"name": schema + '.resume_chunk_embeddings'}).scalar() is None
        finally:
            transaction.rollback()
