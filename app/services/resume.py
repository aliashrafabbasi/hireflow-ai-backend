from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.file import save_uploaded_file

from app.repositories.resume import (
    create_resume,
    update_resume_parsing,
    get_resumes,
    get_resume_by_id,
)

from app.services.resume_parser import process_resume


def upload_resume(
    db: Session,
    user,
    file: UploadFile,
):
    file_data = save_uploaded_file(file)

    resume = create_resume(
        db=db,
        user_id=user.id,
        file_data=file_data,
    )

    resume = process_resume(
        db=db,
        resume=resume,
    )

    return resume


def get_all_resumes(
    db: Session,
):
    return get_resumes(db)


def get_resume(
    db: Session,
    resume_id: UUID,
):
    return get_resume_by_id(
        db,
        resume_id,
    )