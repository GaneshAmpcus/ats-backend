# AI Service

Python 3.10+ FastAPI service foundation for ATS parsing and matching workflows.

## Setup

From this directory, create a virtual environment and install dependencies:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `AI_SERVICE_API_KEY`, `GROQ_API_KEY`, and `DATABASE_URL` in `.env`. Every HTTP
endpoint, including health and API documentation, requires the `X-API-Key` header
with the configured service key. Requests are rejected if the key is missing or
incorrect; the service returns `503` if its key has not been configured. Generate
a long, random secret for `AI_SERVICE_API_KEY` and share it only with authorized
service clients.

`AI_DATABASE_SCHEMA` selects the PostgreSQL schema used by this service's pooled
connections (`ai_service` by default). Create the schema and enable pgvector there
when preparing a shared database, for example with `CREATE SCHEMA ai_service;`
and `CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA ai_service;`. Set a separate
`DATABASE_URL` to use a separate database. The embedding model is downloaded
from Hugging Face on its first use. Set `EMBEDDING_DEVICE` to `cuda` when a
compatible CUDA runtime is available; it defaults to CPU.

This service foundation does not create or migrate application tables; schema
ownership and migrations can be added with the relevant feature.

## Run

```powershell
uvicorn app.main:app --reload
```

Health check: `GET /api/v1/health`. To send a message to the configured LLM and
get its response, call `POST /api/v1/llm-test` with a JSON body such as
`{"message":"Reply with exactly: LLM is working."}`.

Core integration factories are available as `app.matching.embeddings.get_embedding_model`,
`app.llm.client.get_llm`, and `app.db.database.get_db_session`. Heavy model and
database connections are not opened during module import.
