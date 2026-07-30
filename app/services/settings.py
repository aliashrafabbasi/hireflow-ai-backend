from sqlalchemy.orm import Session

from app.repositories import settings as settings_repository
from app.schemas.settings import SettingsResponse, SettingsUpdate


def get_settings(db: Session) -> SettingsResponse:
    return SettingsResponse(
        match_score_threshold=settings_repository.get_match_score_threshold(db),
    )


def update_settings(db: Session, data: SettingsUpdate) -> SettingsResponse:
    settings_repository.set_match_score_threshold(
        db,
        data.match_score_threshold,
    )
    return get_settings(db)
