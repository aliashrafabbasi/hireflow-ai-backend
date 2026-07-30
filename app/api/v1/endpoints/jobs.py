from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
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
):
    return job_service.create_job(
        db,
        job_data,
    )


@router.get(
    "",
    response_model=list[JobResponse],
)
def get_jobs(
    db: Session = Depends(get_db),
):
    return job_service.get_jobs(db)


@router.get(
    "/{job_id}",
    response_model=JobResponse,
)
def get_job(
    job_id: UUID,
    db: Session = Depends(get_db),
):
    job = job_service.get_job_by_id(
        db,
        job_id,
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return job


@router.delete(
    "/{job_id}",
)
def delete_job(
    job_id: UUID,
    db: Session = Depends(get_db),
):
    job = job_service.delete_job(
        db,
        job_id,
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return {
        "message": "Job deleted successfully"
    }
@router.post(
    "/{job_id}/analyze",
    response_model=JobAnalysisResponse,
)
def analyze_job(
    job_id: UUID,
    db: Session = Depends(get_db),
):
    result = job_service.analyze_job(
        db,
        job_id,
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return result
