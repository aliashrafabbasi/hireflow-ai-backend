from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.repositories.resume import (
    create_resume,
    delete_resume as delete_resume_row,
    get_resume_by_id,
    get_staff_resume_by_id,
    get_resumes,
    get_resumes_by_user,
)

from app.services.resume_parser import process_resume


def upload_resume(
    db: Session,
    user,
    file: UploadFile,
):
    file_data = {
        "original_filename": file.filename or "resume",
        "file_content": file.file.read(),
        "file_type": file.content_type or "application/octet-stream",
    }
    file_data["file_size"] = len(file_data["file_content"])

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


def get_user_resumes(
    db: Session,
    user_id: UUID,
):
    return get_resumes_by_user(db, user_id)


def get_resume(
    db: Session,
    resume_id: UUID,
):
    return get_staff_resume_by_id(
        db,
        resume_id,
    )


def delete_resume(
    db: Session,
    resume_id: UUID,
):
    resume = get_staff_resume_by_id(db, resume_id)
    if not resume:
        return None

    deleted = delete_resume_row(db, resume_id)
    return deleted
