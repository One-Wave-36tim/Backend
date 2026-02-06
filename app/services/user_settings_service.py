from sqlalchemy.orm import Session

from app.db.repositories.user_settings_repository import (
    get_user_settings,
    upsert_user_settings,
)
from app.schemas.user_settings import UserSettingsResponse


def save_notion_key(db: Session, user_id: int, notion_api_key: str) -> UserSettingsResponse:
    settings = upsert_user_settings(db=db, user_id=user_id, notion_api_key=notion_api_key)
    return UserSettingsResponse.model_validate(settings)


def fetch_user_settings(db: Session, user_id: int) -> UserSettingsResponse | None:
    settings = get_user_settings(db=db, user_id=user_id)
    if not settings:
        return None
    return UserSettingsResponse.model_validate(settings)
