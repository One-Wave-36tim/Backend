from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.password import verify_password
from app.db.repositories.auth_repository import find_user_by_id
from app.schemas.auth import DevTokenResponse, LoginResponse

try:
    import jwt as pyjwt
except ModuleNotFoundError:  # pragma: no cover - optional dependency on local env.
    pyjwt = None


def _create_access_token(user_id: str) -> tuple[str, int]:
    if pyjwt is None:
        raise RuntimeError(
            "PyJWT module is missing. Install `pyjwt` to enable login token issuance."
        )

    settings = get_settings()
    now = datetime.now(tz=UTC)
    expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    expire_at = now + expires_delta
    payload = {"sub": user_id, "iat": int(now.timestamp()), "exp": int(expire_at.timestamp())}
    token = pyjwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, int(expires_delta.total_seconds())


def login_with_id_pw(db: Session, user_id: str, password: str) -> LoginResponse:
    user = find_user_by_id(db=db, user_id=user_id)
    if not user or not verify_password(password, user.password):
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


def issue_dev_token(db: Session, user_id: str) -> DevTokenResponse:
    user = find_user_by_id(db=db, user_id=user_id)
    if user is None:
        raise ValueError("User not found")

    access_token, expires_in = _create_access_token(user.user_id)
    return DevTokenResponse(
        success=True,
        message="Dev token issued",
        user_id=user.user_id,
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
    )
