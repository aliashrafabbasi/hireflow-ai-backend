from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories import resume_skill as resume_skill_repository
from app.repositories import job_skill as job_skill_repository
from app.repositories import match_result as match_result_repository
from app.services.match_analyzer import analyze_match


def _normalize_skills(skills) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []

    for skill in skills:
        name = (skill.skill or "").strip()
        if not name:
            continue

        key = name.lower()
        if key in seen:
            continue

        seen.add(key)
        normalized.append(name)

    return normalized


def calculate_match(
    db: Session,
    resume_id: UUID,
    job_id: UUID,
):
    resume_skills = _normalize_skills(
        resume_skill_repository.get_resume_skills(db, resume_id)
    )
    job_skills = _normalize_skills(
        job_skill_repository.get_job_skills(db, job_id)
    )

    if not job_skills:
        return match_result_repository.create_match_result(
            db,
            resume_id,
            job_id,
            0.0,
            [],
            [],
            "No required skills were found for this job.",
            [],
        )

    analysis = analyze_match(resume_skills, job_skills)

    matched_skills = analysis.get("matched_skills") or []
    missing_skills = analysis.get("missing_skills") or []

    score = analysis.get("match_score")
    if score is None:
        score = (
            (len(matched_skills) / len(job_skills)) * 100
            if job_skills
            else 0
        )
    score = round(float(score), 2)

    return match_result_repository.create_match_result(
        db,
        resume_id,
        job_id,
        score,
        matched_skills,
        missing_skills,
        analysis.get("explanation"),
        analysis.get("recommendations") or [],
    )
