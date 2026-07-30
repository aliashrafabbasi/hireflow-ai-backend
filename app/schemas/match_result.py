from uuid import UUID
from datetime import datetime

from pydantic import BaseModel

from app.schemas.match import Recommendation


class MatchResultResponse(BaseModel):
    id: UUID

    resume_id: UUID
    job_id: UUID

    match_score: float

    matched_skills: list[str]
    missing_skills: list[str]

    explanation: str | None = None
    recommendations: list[Recommendation] | None = None

    created_at: datetime

    candidate_name: str | None = None
    resume_filename: str | None = None
    job_title: str | None = None
    company: str | None = None

    class Config:
        from_attributes = True


class JobMatchSummary(BaseModel):
    job_id: UUID
    job_title: str
    company: str
    match_score: float
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    summary: str | None = None


class BestMatchResponse(BaseModel):
    resume_id: UUID
    candidate_name: str | None = None
    resume_filename: str | None = None
    score_threshold: float = 50.0
    best_job: JobMatchSummary
    qualified_jobs: list[JobMatchSummary]
