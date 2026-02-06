from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import DevTokenRequest, DevTokenResponse, LoginRequest, LoginResponse
from app.services.auth_service import issue_dev_token, login_with_id_pw

router = APIRouter(prefix="/auth", tags=["인증"])


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="아이디/비밀번호 로그인",
    description="사용자 아이디와 비밀번호를 검증한 뒤 Bearer JWT를 발급합니다.",
    response_description="로그인 성공/실패 결과",
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    return login_with_id_pw(db=db, user_id=payload.id, password=payload.pw)


@router.post(
    "/dev-token",
    response_model=DevTokenResponse,
    summary="개발용 JWT 발급",
    description=(
        "Swagger 테스트를 위해 사용자 ID를 입력하면 JWT를 발급합니다. "
        "요청한 user_id가 존재하지 않으면 404를 반환합니다."
    ),
    response_description="발급된 개발용 JWT",
    responses={404: {"description": "요청한 user_id의 사용자가 없음"}},
)
def dev_token(payload: DevTokenRequest, db: Session = Depends(get_db)) -> DevTokenResponse:
    try:
        return issue_dev_token(db=db, user_id=payload.user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
