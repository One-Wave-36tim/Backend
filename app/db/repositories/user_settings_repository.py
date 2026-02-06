from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.entities.user_settings import UserSettings


def get_user_settings(db: Session, user_id: int) -> UserSettings | None:
    stmt = select(UserSettings).where(UserSettings.user_id == user_id)
    return db.execute(stmt).scalars().first()


def get_notion_key_by_user(db: Session, user_id: int) -> str | None:
    settings = get_user_settings(db=db, user_id=user_id)
    if not settings:
        return None
    return settings.notion_api_key


def upsert_user_settings(db: Session, user_id: int, notion_api_key: str) -> UserSettings:
    settings = get_user_settings(db=db, user_id=user_id)
    if settings:
        settings.notion_api_key = notion_api_key
    else:
        settings = UserSettings(user_id=user_id, notion_api_key=notion_api_key)
        db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings
