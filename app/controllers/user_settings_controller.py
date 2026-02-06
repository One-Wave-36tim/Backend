from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import CurrentUserId
from app.db.session import get_db
from app.schemas.user_settings import UserSettingsCreate, UserSettingsResponse
from app.services.user_settings_service import save_notion_key

router = APIRouter(prefix="/users/settings", tags=["사용자설정"])


@router.post(
    "/notion-key",
    response_model=UserSettingsResponse,
    summary="노션 API 키 저장",
    description="사용자별 노션 API 키를 저장합니다.",
    response_description="저장 결과",
)
def upsert_notion_key(
    payload: UserSettingsCreate,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> UserSettingsResponse:
    return save_notion_key(db=db, user_id=user_id, notion_api_key=payload.notion_api_key)
