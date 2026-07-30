from sqlalchemy.orm import Session

from app.repositories.job_skill import create_job_skills


def save_job_skills(
    db: Session,
    job_id,
    skills: list[str],
):
    if not skills:
        return

    unique_skills = []

    for skill in skills:
        skill = skill.strip()

        if skill and skill.lower() not in [
            s.lower() for s in unique_skills
        ]:
            unique_skills.append(skill)

    create_job_skills(
        db=db,
        job_id=job_id,
        skills=unique_skills,
    )
