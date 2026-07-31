from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class JobCreate(BaseModel):
    title: str
    company: str
    description: str


class JobResponse(BaseModel):
    id: UUID
    title: str
    company: str
    description: str
    created_at: datetime
    updated_at: datetime
    skills: list[str] = Field(default_factory=list)

    model_config = ConfigDict(
        from_attributes=True
    )
