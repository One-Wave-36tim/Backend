from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.entities.user import User


def find_user_by_credentials(db: Session, user_id: str, password: str) -> User | None:
    stmt = select(User).where(User.user_id == user_id, User.password == password)
    return db.execute(stmt).scalars().first()
