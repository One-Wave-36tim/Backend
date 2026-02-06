from sqlalchemy.orm import Session

from app.api.schemas.auth import LoginResponse
from app.repositories.auth_repository import find_user_by_credentials


def login_with_id_pw(db: Session, user_id: str, password: str) -> LoginResponse:
    user = find_user_by_credentials(db=db, user_id=user_id, password=password)
    if not user:
        return LoginResponse(success=False, message="Invalid id or password")
    return LoginResponse(success=True, message="Login success", user_id=user.user_id)
