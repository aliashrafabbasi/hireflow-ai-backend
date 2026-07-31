from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.exceptions import LLMRateLimitError
from app.dependencies.auth import get_current_staff, get_current_user
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
    try:
        return resume_service.upload_resume(
            db=db,
            user=current_user,
            file=file,
        )
    except LLMRateLimitError as e:
        raise HTTPException(status_code=429, detail=e.message)


@router.get(
    "",
    response_model=list[ResumeResponse],
)
def get_resumes(
    db: Session = Depends(get_db),
    _=Depends(get_current_staff),
):
    return resume_service.get_all_resumes(db)


@router.get(
    "/{resume_id}",
    response_model=ResumeResponse,
)
def get_resume(
    resume_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(get_current_staff),
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


@router.delete(
    "/{resume_id}",
)
def delete_resume(
    resume_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(get_current_staff),
):
    resume = resume_service.delete_resume(db, resume_id)
    if not resume:
        raise HTTPException(
            status_code=404,
            detail="Resume not found",
        )

    return {"message": "CV deleted successfully"}
