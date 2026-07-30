from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.exceptions import LLMRateLimitError
from app.db.session import get_db
from app.dependencies.auth import get_current_staff
from app.schemas.match import MatchResponse
from app.schemas.match_result import BestMatchResponse, MatchResultResponse
from app.services import matching


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
    _=Depends(get_current_staff),
):
    try:
        result = matching.calculate_best_match(db, resume_id, force=force)
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
    _=Depends(get_current_staff),
):
    try:
        result = matching.calculate_match(
            db,
            resume_id,
            job_id,
            force=force,
        )
    except LLMRateLimitError as e:
        raise HTTPException(status_code=429, detail=e.message)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Match could not be created",
        )

    return result
