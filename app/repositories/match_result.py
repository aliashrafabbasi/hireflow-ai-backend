from uuid import UUID

from sqlalchemy.orm import Session

from app.models.match_result import MatchResult


def create_match_result(
    db: Session,
    resume_id: UUID,
    job_id: UUID,
    match_score: float,
    matched_skills: list[str],
    missing_skills: list[str],
    explanation: str = None,
    recommendations: list[dict] = None,
):

    match_result = MatchResult(
        resume_id=resume_id,
        job_id=job_id,
        match_score=match_score,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        explanation=explanation,
        recommendations=recommendations,
    )


    db.add(match_result)
    db.commit()
    db.refresh(match_result)


    return match_result


def get_match_result(
    db: Session,
    resume_id: UUID,
    job_id: UUID,
):
    return (
        db.query(MatchResult)
        .filter(
            MatchResult.resume_id == resume_id,
            MatchResult.job_id == job_id,
        )
        .first()
    )
