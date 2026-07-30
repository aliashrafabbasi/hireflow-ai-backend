from uuid import UUID

from sqlalchemy.orm import Session

from app.models.job import Job
from app.schemas.job import JobCreate


def create_job(
    db: Session,
    job_data: JobCreate,
) -> Job:
    job = Job(
        title=job_data.title,
        company=job_data.company,
        description=job_data.description,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


def get_jobs(
    db: Session,
):
    return db.query(Job).all()


def get_job_by_id(
    db: Session,
    job_id: UUID,
):
    return (
        db.query(Job)
        .filter(Job.id == job_id)
        .first()
    )


def delete_job(
    db: Session,
    job: Job,
):
    db.delete(job)
    db.commit()
