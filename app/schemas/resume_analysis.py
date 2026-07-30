from pydantic import BaseModel


class ExperienceItem(BaseModel):
    company: str
    role: str
    duration: str


class EducationItem(BaseModel):
    degree: str
    institution: str
    duration: str


class ProjectItem(BaseModel):
    name: str
    tech_stack: list[str]


class ResumeAnalysis(BaseModel):
    candidate_name: str
    email: str
    phone: str
    title: str

    skills: list[str]
    education: list[EducationItem]
    projects: list[ProjectItem]

    experience: list[ExperienceItem]