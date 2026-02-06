import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.auth import SignupRequest, SignupResponse
from app.services.signup_service import SignupService
from app.db.session import get_db

router = APIRouter(prefix="/signup", tags=["signup"])
logger = logging.getLogger(__name__)

@router.post("/", response_model=SignupResponse)
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
