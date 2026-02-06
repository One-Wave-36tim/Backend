from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import CurrentUserId
from app.db.session import get_db
from app.schemas.home import HomeResponse
from app.services.home_service import get_home_data

router = APIRouter(prefix="/v1", tags=["홈"])


@router.get(
    "/home",
    response_model=HomeResponse,
    summary="홈 화면 데이터 조회",
    description="사용자 카드, 프로젝트 목록, 오늘의 루틴을 한 번에 조회합니다.",
    response_description="홈 화면 렌더링 데이터",
    responses={401: {"description": "인증 실패"}},
)
def get_home_endpoint(
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> HomeResponse:
    try:
        return get_home_data(db=db, user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

