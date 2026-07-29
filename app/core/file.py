import os
import uuid

from fastapi import UploadFile

UPLOAD_DIR = "uploads/resumes"


def save_uploaded_file(file: UploadFile):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    extension = os.path.splitext(file.filename)[1]

    stored_filename = f"{uuid.uuid4()}{extension}"

    file_path = os.path.join(
        UPLOAD_DIR,
        stored_filename,
    )

    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    return {
        "original_filename": file.filename,
        "stored_filename": stored_filename,
        "file_path": file_path,
        "file_type": file.content_type,
        "file_size": os.path.getsize(file_path),
    }