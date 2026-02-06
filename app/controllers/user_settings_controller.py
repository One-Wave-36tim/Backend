from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user_settings import UserSettingsCreate, UserSettingsResponse
from app.services.user_settings_service import save_notion_key

router = APIRouter(prefix="/users/settings", tags=["user-settings"])


@router.post("/notion-key", response_model=UserSettingsResponse)
def upsert_notion_key(
    payload: UserSettingsCreate,
    db: Session = Depends(get_db),
) -> UserSettingsResponse:
    user_id = 1
    return save_notion_key(db=db, user_id=user_id, notion_api_key=payload.notion_api_key)
