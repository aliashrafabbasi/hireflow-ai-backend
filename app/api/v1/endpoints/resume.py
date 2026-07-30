from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.db.session import get_db
from app.schemas.resume import ResumeResponse
from app.services import resume as resume_service


router = APIRouter(
    prefix="/resumes",
    tags=["Resumes"],
)


@router.post(
    "/upload",
    response_model=ResumeResponse,
)
def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return resume_service.upload_resume(
        db=db,
        user=current_user,
        file=file,
    )


@router.get(
    "",
    response_model=list[ResumeResponse],
)
def get_resumes(
    db: Session = Depends(get_db),
):
    return resume_service.get_all_resumes(db)


@router.get(
    "/{resume_id}",
    response_model=ResumeResponse,
)
def get_resume(
    resume_id: UUID,
    db: Session = Depends(get_db),
):
    resume = resume_service.get_resume(
        db=db,
        resume_id=resume_id,
    )

    if not resume:
        raise HTTPException(
            status_code=404,
            detail="Resume not found",
        )

    return resume