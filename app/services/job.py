from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories import job as job_repository
from app.repositories import job_skill as job_skill_repository
from app.schemas.job import JobCreate
from app.services.job_analyzer import analyze_job_text
from app.schemas.job_analysis import JobAnalysisResponse


def create_job(
    db: Session,
    job_data: JobCreate,
):
    job = job_repository.create_job(
        db,
        job_data,
    )

    # Auto-extract & save skills (same as POST /jobs/{id}/analyze)
    analyze_job(db, job.id)

    return job_repository.get_job_by_id(db, job.id)


def get_jobs(
    db: Session,
):
    return job_repository.get_jobs(db)


def get_job_by_id(
    db: Session,
    job_id: UUID,
):
    return job_repository.get_job_by_id(
        db,
        job_id,
    )


def delete_job(
    db: Session,
    job_id: UUID,
):
    job = job_repository.get_job_by_id(
        db,
        job_id,
    )

    if not job:
        return None

    job_repository.delete_job(
        db,
        job,
    )

    return job



def analyze_job(
    db: Session,
    job_id: UUID,
):
    job = job_repository.get_job_by_id(
        db,
        job_id,
    )

    if not job:
        return None


    # purani skills delete
    job_skill_repository.delete_job_skills(
        db,
        job.id,
    )


    analysis = analyze_job_text(
        job.description,
    )


    skills = analysis.skills


    job_skill_repository.create_job_skills(
        db,
        job.id,
        skills,
    )


    return JobAnalysisResponse(
        job_id=job.id,
        skills=skills,
    )