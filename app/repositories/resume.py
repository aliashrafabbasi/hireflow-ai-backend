from datetime import datetime

from sqlalchemy.orm import Session

from app.models.resume import Resume
from uuid import UUID


def create_resume(
    db: Session,
    user_id,
    file_data: dict,
):
    resume = Resume(
        user_id=user_id,
        original_filename=file_data["original_filename"],
        stored_filename=file_data["stored_filename"],
        file_path=file_data["file_path"],
        file_type=file_data["file_type"],
        file_size=file_data["file_size"],
        status="uploaded",
        processing_status="pending",
        extracted_text=None,
        parsed_at=None,
    )

    db.add(resume)
    db.commit()
    db.refresh(resume)

    return resume


def update_resume_parsing(
    db: Session,
    resume: Resume,
    extracted_text: str,
):
    resume.extracted_text = extracted_text
    resume.processing_status = "completed"
    resume.parsed_at = datetime.utcnow()

    db.commit()
    db.refresh(resume)

    return resume



def get_resumes(
    db: Session,
):
    return db.query(Resume).all()


def get_resume_by_id(
    db: Session,
    resume_id: UUID,
):
    return (
        db.query(Resume)
        .filter(Resume.id == resume_id)
        .first()
    )