from sqlalchemy.orm import Session

from app.schemas.user_settings import UserSettingsResponse

_USER_SETTINGS: dict[int, str] = {}


def save_notion_key(db: Session, user_id: int, notion_api_key: str) -> UserSettingsResponse:
    _USER_SETTINGS[user_id] = notion_api_key
    return UserSettingsResponse(success=True, user_id=user_id, notion_api_key=notion_api_key)
from sqlalchemy.orm import Session

from app.schemas.user_settings import UserSettingsResponse

_USER_SETTINGS: dict[int, str] = {}


def save_notion_key(db: Session, user_id: int, notion_api_key: str) -> UserSettingsResponse:
    _USER_SETTINGS[user_id] = notion_api_key
    return UserSettingsResponse(success=True, user_id=user_id, notion_api_key=notion_api_key)
