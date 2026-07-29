from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ResumeResponse(BaseModel):
    id: UUID
    user_id: UUID

    original_filename: str
    stored_filename: str
    file_path: str
    file_type: str
    file_size: int

    status: str

    extracted_text: str | None = None
    processing_status: str | None = None
    parsed_at: datetime | None = None

    uploaded_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )