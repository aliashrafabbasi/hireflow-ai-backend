from sqlalchemy.orm import Session

from app.repositories.resume_skill import create_resume_skills


def save_resume_skills(
    db: Session,
    resume_id,
    skills: list[str],
):
    if not skills:
        return

    unique_skills = []

    for skill in skills:
        skill = skill.strip()

        if skill and skill not in unique_skills:
            unique_skills.append(skill)

    create_resume_skills(
        db=db,
        resume_id=resume_id,
        skills=unique_skills,
    )