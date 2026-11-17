"""Adopt resume storage and add the separate pgvector embedding stage.

Existing local installs may have resume tables created by create_tables.py.
This migration preserves them. Downgrade removes only the new embedding stage.
"""
from alembic import op

revision = "8d1c4a2b6e90"
down_revision = "44579f5e0fa1"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("""CREATE TABLE IF NOT EXISTS resume_batches (
        id UUID PRIMARY KEY, total_jobs INTEGER NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now())""")
    op.execute("""CREATE TABLE IF NOT EXISTS resume_parse_jobs (
        id UUID PRIMARY KEY, batch_id UUID REFERENCES resume_batches(id) ON DELETE SET NULL,
        batch_position INTEGER, status VARCHAR(20) NOT NULL,
        original_filename VARCHAR(255) NOT NULL, content_type VARCHAR(100) NOT NULL,
        file_size INTEGER NOT NULL, file_sha256 VARCHAR(64) NOT NULL,
        storage_key VARCHAR(500) NOT NULL, extracted_text TEXT, parsed_data JSONB,
        error_message TEXT, attempts INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        started_at TIMESTAMPTZ, completed_at TIMESTAMPTZ)""")
    for column in ("batch_id", "status", "file_sha256"):
        op.execute(f"CREATE INDEX IF NOT EXISTS ix_resume_parse_jobs_{column} ON resume_parse_jobs ({column})")
    op.execute("""CREATE TABLE IF NOT EXISTS resume_records (
        resume_id UUID PRIMARY KEY REFERENCES resume_parse_jobs(id) ON DELETE RESTRICT,
        candidate_id VARCHAR(255), parsed_data JSONB, vector_chunks JSONB NOT NULL DEFAULT '[]',
        created_at TIMESTAMPTZ NOT NULL DEFAULT now())""")
    op.execute("CREATE INDEX IF NOT EXISTS ix_resume_records_candidate_id ON resume_records(candidate_id)")
    for column, sql_type in (
        ("embedding_status", "VARCHAR(20)"), ("embedding_attempts", "INTEGER NOT NULL DEFAULT 0"),
        ("embedding_count", "INTEGER NOT NULL DEFAULT 0"), ("embedding_error", "TEXT"),
        ("embedding_completed_at", "TIMESTAMPTZ"),
    ):
        op.execute(f"ALTER TABLE resume_parse_jobs ADD COLUMN IF NOT EXISTS {column} {sql_type}")
    op.execute("""CREATE TABLE IF NOT EXISTS resume_chunk_embeddings (
        chunk_id UUID PRIMARY KEY, resume_id UUID NOT NULL REFERENCES resume_records(resume_id) ON DELETE RESTRICT,
        candidate_id VARCHAR(255), section_type TEXT NOT NULL, chunk_text TEXT NOT NULL,
        metadata JSONB NOT NULL, embedding_model TEXT NOT NULL, embedding vector(384) NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now())""")
    op.execute("""DO $$ BEGIN
        IF (SELECT format_type(atttypid, atttypmod) FROM pg_attribute
            WHERE attrelid = 'resume_chunk_embeddings'::regclass AND attname = 'embedding'
            AND NOT attisdropped) <> 'vector(384)' THEN
            RAISE EXCEPTION 'Existing embedding column must be vector(384); migrate model dimensions explicitly';
        END IF;
    END $$""")
    op.execute("CREATE INDEX IF NOT EXISTS ix_resume_chunk_embeddings_resume_id ON resume_chunk_embeddings(resume_id)")
    op.execute("""CREATE INDEX IF NOT EXISTS resume_chunk_embeddings_cosine_idx
        ON resume_chunk_embeddings USING hnsw (embedding vector_cosine_ops)""")


def downgrade():
    op.execute("DROP TABLE resume_chunk_embeddings")
    for column in ("embedding_status", "embedding_attempts", "embedding_count", "embedding_error", "embedding_completed_at"):
        op.execute(f"ALTER TABLE resume_parse_jobs DROP COLUMN {column}")
