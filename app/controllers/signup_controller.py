import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import SignupRequest, SignupResponse
from app.services.signup_service import SignupService

router = APIRouter(prefix="/signup", tags=["인증"])
logger = logging.getLogger(__name__)


@router.post(
    "/",
    response_model=SignupResponse,
    summary="회원가입",
    description="새 사용자 계정을 생성합니다.",
    response_description="회원가입 결과",
)
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    service = SignupService(db)
    try:
        return service.signup(req)
    except ValueError as exc:
        logger.warning("Signup validation failed: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Signup failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
