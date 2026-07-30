from sqlalchemy.orm import Session

from app.models.resume_skill import ResumeSkill


def create_resume_skill(
    db: Session,
    resume_id,
    skill: str,
):
    resume_skill = ResumeSkill(
        resume_id=resume_id,
        skill=skill,
    )

    db.add(resume_skill)

    return resume_skill


def create_resume_skills(
    db: Session,
    resume_id,
    skills: list[str],
):
    for skill in skills:
        create_resume_skill(
            db=db,
            resume_id=resume_id,
            skill=skill,
        )

    db.commit()