"""Internal, authenticated embedding API. No database writes or matching."""
import math

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.config import get_settings

router = APIRouter(tags=["embeddings"])


def get_embedding_model():
    # Avoid loading transformer dependencies during parsing-only startup.
    from app.matching.embeddings import get_embedding_model as load
    return load()


class EmbedRequest(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=32)

    @field_validator("texts")
    @classmethod
    def validate_texts(cls, texts):
        if any(not text.strip() or len(text) > 12000 for text in texts):
            raise ValueError("Each text must be nonblank and at most 12000 characters")
        return texts


class EmbedResponse(BaseModel):
    model: str
    dimensions: int
    embeddings: list[list[float]]


@router.post("/embeddings", response_model=EmbedResponse)
def embed(request: EmbedRequest):
    try:
        vectors = get_embedding_model().embed_documents(request.texts)
        dimensions = len(vectors[0])
        if (len(vectors) != len(request.texts) or dimensions == 0
                or any(len(v) != dimensions or not all(math.isfinite(x) for x in v)
                       or not any(v) for v in vectors)):
            raise ValueError("Invalid model output")
    except Exception as exc:
        raise HTTPException(503, "Embedding model is unavailable or returned invalid vectors.") from exc
    return EmbedResponse(model=get_settings().embedding_model_name,
                         dimensions=dimensions, embeddings=vectors)
