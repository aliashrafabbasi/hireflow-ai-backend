from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.match_result import JobMatchSummary


class CareerEvaluationOption(str, Enum):
    EXISTING_JOBS = "existing_jobs"
    AI_CAREER = "ai_career"


class CareerJobMatchesResponse(BaseModel):
    resume_id: UUID
    score_threshold: float = 60.0
    qualified_jobs: list[JobMatchSummary]


class CareerSuggestion(BaseModel):
    title: str
    rationale: str
    matching_skills: list[str] = Field(default_factory=list)
    skills_to_develop: list[str] = Field(default_factory=list)


class CareerAdviceResponse(BaseModel):
    resume_id: UUID
    career_suggestions: list[CareerSuggestion]
