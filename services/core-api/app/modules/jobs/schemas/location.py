from uuid import UUID

from pydantic import BaseModel, ConfigDict


class JobLocationCreate(BaseModel):
    job_id: UUID
    country: str | None = None
    state: str | None = None
    city: str | None = None
    address: str | None = None
    postal_code: str | None = None
    is_primary: bool = False


class JobLocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    country: str | None
    state: str | None
    city: str | None
    address: str | None
    postal_code: str | None
    is_primary: bool
