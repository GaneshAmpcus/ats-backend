# Resume embeddings: setup and verification

The pipeline now ends with numeric embeddings stored in PostgreSQL. Job matching is not implemented.

## Setup

1. Install the updated Core requirements in the service environment. AI already declares sentence-transformers/langchain-huggingface. The default model is `sentence-transformers/all-MiniLM-L6-v2`; its output has 384 dimensions.
2. PostgreSQL must have pgvector available. From `services/core-api`, run `python -m alembic upgrade head`. The new revision is `8d1c4a2b6e90`. It creates/adopts the resume tables and creates `resume_chunk_embeddings`, embedding-status columns and an HNSW cosine index. It preserves existing parsed resumes.
3. **Existing databases created with `create_tables.py`:** if they already contain application tables but have no Alembic revision, do not blindly stamp them. First reconcile their schema with baseline `44579f5e0fa1`; only after verifying equivalence, stamp that baseline and upgrade. `create_all()` alone cannot add the new columns to existing tables. The standalone old `prepare_resume_vectors` script is not a substitute for this migration.
4. Keep `APP_AI_SERVICE_API_KEY` in Core equal to `AI_SERVICE_API_KEY` in AI. Core's `APP_RESUME_EMBEDDING_MODEL` must equal AI's `EMBEDDING_MODEL_NAME`. Both default to the model above. A different-dimensional model requires a migration and a corresponding validation update; never mix model spaces silently.
5. Restart both APIs and workers. For truly separate execution, set `APP_CELERY_TASK_ALWAYS_EAGER=false` in Core and run Redis plus workers consuming `resume_priority,resume_bulk,resume_embeddings`. In eager development mode, the separate task still executes inline and the upload can take longer.

```powershell
python -m celery -A app.workers.celery_app:celery_app worker --loglevel=INFO -Q resume_priority,resume_bulk,resume_embeddings --pool=solo
```

The first embedding request may download/load model weights. The model runs locally in the AI service, independently of the Groq resume parser. Health/LLM diagnostics do not establish embedding-model readiness.

## API checks

Import the regenerated collection and environment; retain your locally configured key. `Generate embeddings directly` calls authenticated `POST /api/v1/embeddings` with `{"texts":["Skills: Python, SQL"]}`. The response has `model`, `dimensions`, and `embeddings` in input order. Up to 32 nonblank strings of 12,000 characters each are accepted. This diagnostic does not persist anything; normal Core upload does.

Upload a resume and poll its existing GET job endpoint. New fields:

- `embedding_status`: null before successful parsing (and for untouched historical jobs), then `pending`, `processing`, `completed` or `failed`.
- `embedding_attempts`: increments when an embedding task claims the job.
- `embedding_count`: number of persisted numeric-vector rows, only updated when the entire stage commits.
- `embedding_error`: safe failure/retry message, cleared on success.
- `embedding_completed_at`: timestamp of successful embedding persistence.

Parsing `status=completed` remains independent. Success through both stages requires `status=completed` and `embedding_status=completed`. Batch top-level counts still describe parsing; examine embedding fields within each `jobs` entry. Postman now polls until both stages terminate, and fails assertions when embedding fails. Use Runner with `auto_poll=true`, 2000ms delay, and raise the poll limit if needed.

`vector_chunks` still contains original prepared text/metadata. The embedding stage strips candidate-name context, known parsed email/phone/LinkedIn values and common incidental email/phone patterns from embedding text. It only uses professional summary, skills, experience, projects, education and certifications. This is best-effort contact removal, not a general PII anonymization guarantee. Parsed JSON is preserved. Metadata sent to the model is empty: only sanitized text is sent. Stored vector metadata links to the source chunk/path without duplicating its raw fields.

Long sections are split into at most 800-character pieces with 100-character overlap. Each piece has a deterministic ID; embedding count may exceed the original chunk count. Tokenizers can still truncate unusually token-dense text. A resume with no meaningful sections completes with zero vectors; bundled synthetic-resume tests expect positive counts.

## Database verification

Run against the Core database, substituting the upload job ID (also the resume ID):

```sql
SELECT id, status, embedding_status, embedding_attempts,
       embedding_count, embedding_error, embedding_completed_at
FROM resume_parse_jobs WHERE id = 'YOUR_JOB_UUID'::uuid;

SELECT chunk_id, resume_id, candidate_id, section_type,
       embedding_model, vector_dims(embedding) AS dimensions,
       chunk_text
FROM resume_chunk_embeddings
WHERE resume_id = 'YOUR_JOB_UUID'::uuid;

SELECT count(*) AS actual_stored_vectors
FROM resume_chunk_embeddings WHERE resume_id = 'YOUR_JOB_UUID'::uuid;
```

Rows should have dimension 384 and their count should equal `embedding_count`. Chunks, vectors and completion status commit atomically after all embedding batches succeed. Stable-ID upserts prevent duplicate rows on regeneration; stale rows are removed within the same transaction. A response count is useful operationally, but the SQL query verifies actual pgvector storage.

## Retry and historical resumes

Timeouts, transport errors and AI 429/5xx retry with exponential 10/20/40-second delays by default (`APP_RESUME_EMBEDDING_MAX_RETRIES=3`, four total attempts). Invalid vectors/model/dimensions and other 4xx fail without retry. Parse data/status remain unchanged on any embedding failure.

Queue submission failures are recorded separately. Historical resumes are not automatically embedded by the migration. To embed one, or retry a terminal failure after fixing its cause:

```powershell
python -m scripts.embed_resume YOUR_JOB_UUID
```

Already-completed embeddings are left alone. If a worker was killed while embedding and the job is stuck processing, first confirm that worker is stopped, then use `--recover-processing`. This is explicit recovery; there is no periodic dispatcher/lease reaper. A crash between parse commit and enqueue can leave a pending job requiring the same command. The command resets embedding attempts only, not parsing or source data.

For a retry test, in an isolated setup make the embedding endpoint unavailable after parsing completes, inspect pending/attempts, restore it and wait for completion. Unit tests cover this without contacting live services.

## Automated checks

Core tests cover contact removal, splitting/batching, successful persistence, retry success/exhaustion, invalid vectors, duplicate deliveries/upserts, queue failure isolation and retry scheduling. AI tests cover authentication, request validation, order and model failure mapping.

`tests/test_pgvector_integration.py` is opt-in (`RUN_PGVECTOR_TESTS=1`) and uses the configured PostgreSQL database only inside a unique temporary schema and an outer rollback. It exercises migration upgrade/adoption/downgrade, real vector(384) writes, index creation and upsert behavior without retaining fixtures or touching application data.
