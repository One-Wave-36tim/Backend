from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.db.entities.user import User
from app.db.repositories.auth_repository import SignupRepository
from app.schemas.auth import SignupRequest, SignupResponse

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)

class SignupService:
    def __init__(self, db: Session):
        self.repo = SignupRepository(db)

    def signup(self, req: SignupRequest) -> SignupResponse:
        if self.repo.find_by_user_id(req.id):
            return SignupResponse(success=False, message="이미 존재하는 아이디입니다.", user_id=None)

        hashed_pw = pwd_context.hash(req.pw)
        user = User(user_id=req.id, password=hashed_pw)
        self.repo.create_user(user)

        return SignupResponse(success=True, message="회원가입 성공", user_id=user.user_id)
