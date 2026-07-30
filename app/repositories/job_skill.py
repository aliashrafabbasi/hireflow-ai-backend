from uuid import UUID

from sqlalchemy.orm import Session

from app.models.job_skill import JobSkill


def create_job_skills(
    db: Session,
    job_id: UUID,
    skills: list[str],
):
    job_skills = [
        JobSkill(
            job_id=job_id,
            skill=skill.strip(),
        )
        for skill in skills
    ]

    db.add_all(job_skills)
    db.commit()

    return job_skills


def get_job_skills(
    db: Session,
    job_id: UUID,
):
    return (
        db.query(JobSkill)
        .filter(
            JobSkill.job_id == job_id
        )
        .all()
    )


def delete_job_skills(
    db: Session,
    job_id: UUID,
):
    db.query(JobSkill).filter(
        JobSkill.job_id == job_id
    ).delete()

    db.commit()