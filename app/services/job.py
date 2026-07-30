from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories import job as job_repository
from app.schemas.job import JobCreate


def create_job(
    db: Session,
    job_data: JobCreate,
):
    return job_repository.create_job(
        db,
        job_data,
    )


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
