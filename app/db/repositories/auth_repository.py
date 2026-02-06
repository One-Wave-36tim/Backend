from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.entities.user import User


def find_user_by_credentials(db: Session, user_id: str, password: str) -> User | None:
    # Backward-compatible wrapper; password check happens in service now.
    stmt = select(User).where(User.user_id == user_id)
    return db.execute(stmt).scalars().first()


def find_user_by_id(db: Session, user_id: str) -> User | None:
    stmt = select(User).where(User.user_id == user_id)
    return db.execute(stmt).scalars().first()


class SignupRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_user_id(self, user_id: str) -> User | None:
        stmt = select(User).where(User.user_id == user_id)
        return self.db.execute(stmt).scalars().first()

    def create_user(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user