"""Provision pgvector storage for backend-generated embeddings.

Run: python -m scripts.prepare_resume_vectors --dimensions <embedding model dimension>
The PostgreSQL server must have pgvector installed. No embeddings are generated.
"""

import argparse

from sqlalchemy import text

from app.db.session import engine
from scripts.create_tables import main as create_tables


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dimensions", type=int, required=True)
    args = parser.parse_args()
    if args.dimensions != 384:
        parser.error("The resume embedding pipeline uses vector(384); other models require an explicit schema migration")
    if engine.dialect.name != "postgresql":
        parser.error("pgvector storage requires PostgreSQL")
    create_tables()
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        existing = connection.execute(text("""
            SELECT format_type(a.atttypid, a.atttypmod)
            FROM pg_attribute a
            WHERE a.attrelid = to_regclass('resume_chunk_embeddings')
              AND a.attname = 'embedding' AND NOT a.attisdropped
        """)).scalar()
        if existing and existing != f"vector({args.dimensions})":
            raise ValueError(f"Existing embedding type {existing} does not match requested dimensions")
        connection.execute(text(f"""
            CREATE TABLE IF NOT EXISTS resume_chunk_embeddings (
                chunk_id UUID PRIMARY KEY,
                resume_id UUID NOT NULL REFERENCES resume_records(resume_id) ON DELETE RESTRICT,
                candidate_id VARCHAR(255),
                section_type TEXT NOT NULL,
                chunk_text TEXT NOT NULL,
                metadata JSONB NOT NULL,
                embedding_model TEXT NOT NULL,
                embedding vector({args.dimensions}) NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """))
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS resume_chunk_embeddings_resume_idx
            ON resume_chunk_embeddings(resume_id)
        """))
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS resume_chunk_embeddings_cosine_idx
            ON resume_chunk_embeddings USING hnsw (embedding vector_cosine_ops)
        """))
    print("pgvector storage prepared; no embeddings generated or inserted.")


if __name__ == "__main__":
    main()
