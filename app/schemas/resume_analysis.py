from pydantic import BaseModel


class ExperienceItem(BaseModel):
    company: str
    role: str
    duration: str


class ResumeAnalysis(BaseModel):
    candidate_name: str
    email: str
    phone: str
    title: str

    skills: list[str]
    education: list[str]
    projects: list[str]

    experience: list[ExperienceItem]