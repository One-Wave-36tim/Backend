from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.entities.user import User


def get_user_by_pk(db: Session, user_pk: int) -> User | None:
    stmt = select(User).where(User.id == user_pk)
    return db.execute(stmt).scalars().first()


def get_user_by_user_id(db: Session, user_id: str) -> User | None:
    stmt = select(User).where(User.user_id == user_id)
    return db.execute(stmt).scalars().first()

