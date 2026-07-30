from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.match import MatchResponse
from app.services import matching


router = APIRouter(
    prefix="/match",
    tags=["Matching"],
)


@router.post(
    "/{resume_id}/{job_id}",
    response_model=MatchResponse,
)
def match_resume_with_job(
    resume_id: UUID,
    job_id: UUID,
    db: Session = Depends(get_db),
):
    result = matching.calculate_match(
        db,
        resume_id,
        job_id,
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Match could not be created",
        )

    return result
