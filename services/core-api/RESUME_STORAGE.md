# Resume storage and pgvector preparation

The Core API keeps `parsed_data` unchanged. After parsing, the same transaction
saves a permanent `resume_records` row containing the original JSON and
`vector_chunks`, and marks the parse job complete. PostgreSQL uses JSONB for
both fields. Chunk creation is deterministic and makes no model or embedding
calls. AI-service response format is unchanged.

Run `python -m scripts.create_tables` before starting the updated API/worker to
create the additional table. Existing tables are not rebuilt. Existing completed
jobs are not automatically backfilled; resubmit to prepare their chunks.

Single uploads accept optional multipart `candidate_id`. It is an opaque caller
identifier, not inferred from a person's name. Bulk uploads currently have no
candidate mapping and return null candidate IDs. The upload job UUID serves as
`resume_id`; each chunk carries it explicitly.

Poll `GET /api/v1/resumes/jobs/{id}` for `parsed_data` and `vector_chunks`.
Each chunk includes `chunk_id`, `candidate_id`, `resume_id`, `section_type`,
`text`, and `metadata` (filename, source path, entry index, original section
fields, chunking version). Work entries and projects never share chunks.
Empty sections are skipped. No absent dates, issuers, roles or other facts are
invented. Chunk IDs are stable for the same resume UUID and section position.

## Backend-generated embeddings

Use PostgreSQL with pgvector, not Qdrant. The backend must choose an embedding
model and its output dimension, then run:

```powershell
python -m scripts.prepare_resume_vectors --dimensions <model-output-dimension>
```

This provisions `resume_chunk_embeddings` and a cosine HNSW index. It neither
generates nor inserts embeddings. Send each chunk's `text` to the selected
embedding model, then persist the vector with its chunk ID, resume ID, candidate
ID, section type, metadata, text and embedding model identifier. Use one model
and dimension per index; embed search queries with that same model. Changed
source text must be re-embedded, and removed chunk IDs must be removed from the
index. Upsert by chunk ID only after successful embedding generation.

The original JSON remains in `resume_records.parsed_data` independently of the
search index. Do not overwrite it with chunk text or embeddings. Vector index
provisioning is explicit because the embedding model/dimension is not selected
by this parsing feature. Long entries remain single chunks; embedding workers
must respect their model's input limits without silently truncating source data.
