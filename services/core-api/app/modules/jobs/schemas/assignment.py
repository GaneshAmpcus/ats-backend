from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.jobs.enums import AssignmentType


class JobAssignmentCreate(BaseModel):
    job_id: UUID
    user_id: UUID
    assignment_type: AssignmentType
    is_primary: bool = False
    assigned_by: UUID | None = None


class JobAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    user_id: UUID
    assignment_type: AssignmentType
    is_primary: bool
    assigned_by: UUID | None
    assigned_at: datetime
    ended_at: datetime | None
