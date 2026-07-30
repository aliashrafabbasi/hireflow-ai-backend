from pydantic import BaseModel, Field


class SettingsResponse(BaseModel):
    match_score_threshold: float


class SettingsUpdate(BaseModel):
    match_score_threshold: float = Field(..., ge=0, le=100)
