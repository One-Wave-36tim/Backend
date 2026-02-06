from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.repositories.auth_repository import find_user_by_id
from app.schemas.auth import LoginResponse


pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)


def _create_access_token(user_id: str) -> tuple[str, int]:
    settings = get_settings()
    now = datetime.now(tz=timezone.utc)
    expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    expire_at = now + expires_delta
    payload = {"sub": user_id, "iat": int(now.timestamp()), "exp": int(expire_at.timestamp())}
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, int(expires_delta.total_seconds())


def login_with_id_pw(db: Session, user_id: str, password: str) -> LoginResponse:
    user = find_user_by_id(db=db, user_id=user_id)
    if not user or not pwd_context.verify(password, user.password):
        return LoginResponse(success=False, message="Invalid id or password")
    access_token, expires_in = _create_access_token(user.user_id)
    return LoginResponse(
        success=True,
        message="Login success",
        user_id=user.user_id,
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
    )
