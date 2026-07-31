from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.job import Job
from app.repositories import job as job_repository
from app.repositories import job_skill as job_skill_repository
from app.schemas.job import JobCreate, JobResponse
from app.services.job_analyzer import analyze_job_text
from app.schemas.job_analysis import JobAnalysisResponse


def _to_response(job: Job) -> JobResponse:
    return JobResponse(
        id=job.id,
        title=job.title,
        company=job.company,
        description=job.description,
        created_at=job.created_at,
        updated_at=job.updated_at,
        skills=[s.skill for s in (job.skills or []) if s.skill],
    )


def _load_job(db: Session, job_id: UUID) -> Job | None:
    return (
        db.query(Job)
        .options(joinedload(Job.skills))
        .filter(Job.id == job_id)
        .first()
    )


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

    loaded = _load_job(db, job.id)
    return _to_response(loaded) if loaded else None


def get_jobs(
    db: Session,
):
    jobs = (
        db.query(Job)
        .options(joinedload(Job.skills))
        .order_by(Job.created_at.desc())
        .all()
    )
    return [_to_response(j) for j in jobs]


def get_job_by_id(
    db: Session,
    job_id: UUID,
):
    job = _load_job(db, job_id)
    if not job:
        return None
    return _to_response(job)


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
