from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.exceptions import LLMRateLimitError
from app.db.session import get_db
from app.dependencies.auth import get_current_staff
from app.schemas.match import MatchResponse
from app.schemas.match_result import (
    BestMatchResponse,
    CheckedResumesResponse,
    MatchResultResponse,
    PersonChecksResponse,
    SimpleChecksResponse,
)
from app.services import matching
from app.services import resume as resume_service


router = APIRouter(
    prefix="/match",
    tags=["Matching"],
)


@router.get(
    "",
    response_model=list[MatchResultResponse],
)
def get_all_matches(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _=Depends(get_current_staff),
):
    return matching.list_all_matches(db, limit=limit)


@router.get(
    "/checked",
    response_model=CheckedResumesResponse,
)
def get_checked_resumes(
    limit: int = Query(500, ge=1, le=1000),
    db: Session = Depends(get_db),
    _=Depends(get_current_staff),
):
    """
    List resumes that have been matched/checked, who checked them
    (e.g. Ali, Nasar), and per-person counts.
    Shown on UI: Home → Checked CVs button (/checked).
    """
    return matching.list_checked_resumes(db, limit=limit)


@router.get(
    "/checks",
    response_model=SimpleChecksResponse,
)
def get_checks(
    limit: int = Query(500, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_staff),
):
    """
    Simple view for HR:
    - my_count: how many resumes YOU checked
    - people: each person and their count (Ali: 5, Nasar: 7)
    - recent: latest checks in plain language
    """
    return matching.list_checks(db, user_id=current_user.id, limit=limit)


@router.get(
    "/checks/person/{user_id}",
    response_model=PersonChecksResponse,
)
def get_person_checks(
    user_id: UUID,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _=Depends(get_current_staff),
):
    """One person's checked CVs with scores — for profile/detail page."""
    result = matching.get_person_checks(db, person_id=user_id, limit=limit)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result


@router.get(
    "/by-resume/{resume_id}",
    response_model=list[MatchResultResponse],
)
def get_matches_for_resume(
    resume_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(get_current_staff),
):
    return matching.list_matches_for_resume(db, resume_id)


@router.get(
    "/by-job/{job_id}",
    response_model=list[MatchResultResponse],
)
def get_matches_for_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(get_current_staff),
):
    return matching.list_matches_for_job(db, job_id)


@router.get(
    "/result/{match_id}",
    response_model=MatchResultResponse,
)
def get_match_result(
    match_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(get_current_staff),
):
    result = matching.get_match_by_id(db, match_id)
    if not result:
        raise HTTPException(status_code=404, detail="Match result not found")
    return result


@router.post(
    "/{resume_id}",
    response_model=BestMatchResponse,
)
def match_resume_best_job(
    resume_id: UUID,
    force: bool = Query(
        False,
        description="If true, re-run LLM for all jobs. Default reuses cached matches.",
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_staff),
):
    if not resume_service.get_resume(db, resume_id):
        raise HTTPException(status_code=404, detail="Resume not found")

    try:
        result = matching.calculate_best_match(
            db,
            resume_id,
            force=force,
            checked_by_id=current_user.id,
        )
    except LLMRateLimitError as e:
        raise HTTPException(status_code=429, detail=e.message)

    if result is None:
        raise HTTPException(status_code=404, detail="Resume not found")

    if result.get("error") == "no_jobs":
        raise HTTPException(
            status_code=404,
            detail="No jobs found. Create a job first.",
        )

    return result


@router.post(
    "/{resume_id}/{job_id}",
    response_model=MatchResponse,
)
def match_resume_with_job(
    resume_id: UUID,
    job_id: UUID,
    force: bool = Query(False),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_staff),
):
    if not resume_service.get_resume(db, resume_id):
        raise HTTPException(status_code=404, detail="Resume not found")

    try:
        result = matching.calculate_match(
            db,
            resume_id,
            job_id,
            force=force,
            checked_by_id=current_user.id,
        )
    except LLMRateLimitError as e:
        raise HTTPException(status_code=429, detail=e.message)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Match could not be created",
        )

    full = matching.get_match_by_id(db, result.id)
    return full or result
