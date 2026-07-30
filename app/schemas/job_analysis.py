from uuid import UUID

from pydantic import BaseModel


class JobAnalysis(BaseModel):
    skills: list[str]


class JobAnalysisResponse(BaseModel):
    job_id: UUID
    skills: list[str]