from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class Recommendation(BaseModel):
    skill: str
    resource: str


class MatchResponse(BaseModel):
    id: UUID

    resume_id: UUID
    job_id: UUID

    match_score: float

    matched_skills: list[str]
    missing_skills: list[str]

    explanation: str | None = None
    recommendations: list[Recommendation] | None = None

    created_at: datetime

    class Config:
        from_attributes = True