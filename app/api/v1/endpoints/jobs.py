from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.exceptions import LLMRateLimitError
from app.db.session import get_db
from app.dependencies.auth import get_current_staff
from app.schemas.job import JobCreate, JobResponse
from app.services import job as job_service
from app.schemas.job_analysis import JobAnalysisResponse

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)


@router.post(
    "",
    response_model=JobResponse,
)
def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db),
    _=Depends(get_current_staff),
):
    try:
        return job_service.create_job(db, job_data)
    except LLMRateLimitError as e:
        raise HTTPException(status_code=429, detail=e.message)


@router.get(
    "",
    response_model=list[JobResponse],
)
def get_jobs(
    db: Session = Depends(get_db),
    _=Depends(get_current_staff),
):
    return job_service.get_jobs(db)


@router.get(
    "/{job_id}",
    response_model=JobResponse,
)
def get_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(get_current_staff),
):
    job = job_service.get_job_by_id(db, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@router.delete(
    "/{job_id}",
)
def delete_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(get_current_staff),
):
    job = job_service.delete_job(db, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {"message": "Job deleted successfully"}


@router.post(
    "/{job_id}/analyze",
    response_model=JobAnalysisResponse,
)
def analyze_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(get_current_staff),
):
    try:
        result = job_service.analyze_job(db, job_id)
    except LLMRateLimitError as e:
        raise HTTPException(status_code=429, detail=e.message)

    if not result:
        raise HTTPException(status_code=404, detail="Job not found")

    return result
