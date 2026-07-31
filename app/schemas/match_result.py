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
    checked_at: datetime | None = None

    candidate_name: str | None = None
    resume_filename: str | None = None
    job_title: str | None = None
    company: str | None = None

    checked_by_id: UUID | None = None
    checked_by: str | None = None
    checked_by_email: str | None = None

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
    checked_by: str | None = None
    checked_by_id: UUID | None = None


class CheckedByUser(BaseModel):
    user_id: UUID
    full_name: str
    email: str


class CheckerStats(BaseModel):
    user_id: UUID
    full_name: str
    email: str
    resumes_checked: int


class CheckedResumeItem(BaseModel):
    resume_id: UUID
    candidate_name: str | None = None
    resume_filename: str | None = None
    jobs_matched: int
    best_score: float
    checked_at: datetime | None = None
    checked_by_id: UUID | None = None
    checked_by: str | None = None
    checked_by_email: str | None = None
    checked_by_users: list[CheckedByUser] = []


class CheckedResumesResponse(BaseModel):
    total_checked: int
    by_checker: list[CheckerStats]
    resumes: list[CheckedResumeItem]


class CheckSequenceItem(BaseModel):
    resume_id: UUID
    candidate_name: str | None = None
    resume_filename: str | None = None
    checked_by_id: UUID
    checked_by: str
    checked_by_email: str | None = None
    checked_at: datetime | None = None
    best_score: float


class MyChecksSummary(BaseModel):
    user_id: UUID
    full_name: str
    email: str
    resumes_checked: int
    resumes: list[CheckSequenceItem]


class ChecksResponse(BaseModel):
    """Who checked how many resumes — me + team + time sequence."""

    total_unique_resumes: int
    me: MyChecksSummary
    team: list[CheckerStats]
    sequence: list[CheckSequenceItem]


class SimplePersonCount(BaseModel):
    user_id: UUID | None = None
    name: str
    count: int


class SimpleRecentCheck(BaseModel):
    who: str
    who_id: UUID | None = None
    candidate: str
    score: float
    when: datetime | None = None


class SimpleChecksResponse(BaseModel):
    """User-friendly: who checked how many CVs."""

    my_id: UUID
    my_name: str
    my_count: int
    people: list[SimplePersonCount]
    recent: list[SimpleRecentCheck]


class PersonCheckItem(BaseModel):
    resume_id: UUID
    job_id: UUID | None = None
    candidate: str
    score: float
    best_job: str | None = None
    company: str | None = None
    when: datetime | None = None
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    explanation: str | None = None


class PersonChecksResponse(BaseModel):
    user_id: UUID
    name: str
    email: str | None = None
    count: int
    resumes: list[PersonCheckItem]
