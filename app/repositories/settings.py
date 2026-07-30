from datetime import datetime

from sqlalchemy.orm import Session

from app.models.app_setting import AppSetting

DEFAULT_MATCH_SCORE_THRESHOLD = 50.0
MATCH_SCORE_THRESHOLD_KEY = "match_score_threshold"


def get_setting(db: Session, key: str) -> AppSetting | None:
    return db.query(AppSetting).filter(AppSetting.key == key).first()


def upsert_setting(db: Session, key: str, value: str) -> AppSetting:
    setting = get_setting(db, key)
    if setting:
        setting.value = value
        setting.updated_at = datetime.utcnow()
    else:
        setting = AppSetting(key=key, value=value)
        db.add(setting)

    db.commit()
    db.refresh(setting)
    return setting


def get_match_score_threshold(db: Session) -> float:
    setting = get_setting(db, MATCH_SCORE_THRESHOLD_KEY)
    if not setting:
        return DEFAULT_MATCH_SCORE_THRESHOLD
    try:
        return float(setting.value)
    except (TypeError, ValueError):
        return DEFAULT_MATCH_SCORE_THRESHOLD


def set_match_score_threshold(db: Session, threshold: float) -> AppSetting:
    if threshold < 0 or threshold > 100:
        raise ValueError("match_score_threshold must be between 0 and 100")
    return upsert_setting(
        db,
        MATCH_SCORE_THRESHOLD_KEY,
        str(threshold),
    )
