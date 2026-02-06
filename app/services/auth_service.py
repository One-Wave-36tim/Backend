from sqlalchemy.orm import Session

from app.db.repositories.auth_repository import find_user_by_credentials
from app.core.security import create_access_token
from app.schemas.auth import LoginResponse


def login_with_id_pw(db: Session, user_id: str, password: str) -> LoginResponse:
    user = find_user_by_credentials(db=db, user_id=user_id, password=password)
    if not user:
        return LoginResponse(success=False, message="Invalid id or password")
    access_token = create_access_token(subject=user.user_id)
    return LoginResponse(
        success=True,
        message="Login success",
        user_id=user.user_id,
        access_token=access_token,
        token_type="bearer",
    )
