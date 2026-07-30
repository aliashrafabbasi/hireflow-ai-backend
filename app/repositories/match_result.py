from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.match_result import MatchResult


def upsert_match_result(
    db: Session,
    resume_id: UUID,
    job_id: UUID,
    match_score: float,
    matched_skills: list[str],
    missing_skills: list[str],
    explanation: str = None,
    recommendations: list[dict] = None,
):
    existing = (
        db.query(MatchResult)
        .filter(
            MatchResult.resume_id == resume_id,
            MatchResult.job_id == job_id,
        )
        .order_by(MatchResult.created_at.desc())
        .first()
    )

    if existing:
        existing.match_score = match_score
        existing.matched_skills = matched_skills
        existing.missing_skills = missing_skills
        existing.explanation = explanation
        existing.recommendations = recommendations
        # keep created_at as first-seen; bump logical freshness via refresh
        db.commit()
        db.refresh(existing)
        return existing

    match_result = MatchResult(
        resume_id=resume_id,
        job_id=job_id,
        match_score=match_score,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        explanation=explanation,
        recommendations=recommendations,
        created_at=datetime.utcnow(),
    )

    db.add(match_result)
    db.commit()
    db.refresh(match_result)
    return match_result


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
    """Backward-compatible alias — always upserts. """
    return upsert_match_result(
        db,
        resume_id,
        job_id,
        match_score,
        matched_skills,
        missing_skills,
        explanation,
        recommendations,
    )


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
        .order_by(MatchResult.created_at.desc())
        .first()
    )


def _with_relations(query):
    return query.options(
        joinedload(MatchResult.resume),
        joinedload(MatchResult.job),
    )


def get_match_result_by_id(db: Session, match_id: UUID):
    return (
        _with_relations(db.query(MatchResult))
        .filter(MatchResult.id == match_id)
        .first()
    )


def get_all_match_results(db: Session, limit: int = 100):
    return (
        _with_relations(db.query(MatchResult))
        .order_by(MatchResult.created_at.desc())
        .limit(limit)
        .all()
    )


def get_match_results_by_resume(db: Session, resume_id: UUID):
    return (
        _with_relations(db.query(MatchResult))
        .filter(MatchResult.resume_id == resume_id)
        .order_by(MatchResult.match_score.desc(), MatchResult.created_at.desc())
        .all()
    )


def get_match_results_by_job(db: Session, job_id: UUID):
    return (
        _with_relations(db.query(MatchResult))
        .filter(MatchResult.job_id == job_id)
        .order_by(MatchResult.match_score.desc(), MatchResult.created_at.desc())
        .all()
    )
