from sqlalchemy.orm import Session

from app.models.resume import Resume


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
    )

    db.add(resume)
    db.commit()
    db.refresh(resume)

    return resume