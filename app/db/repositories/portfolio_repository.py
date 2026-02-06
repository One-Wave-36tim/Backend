from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.entities.portfolio import Portfolio


def find_portfolio_by_id(db: Session, portfolio_id: int) -> Portfolio | None:
    stmt = select(Portfolio).where(Portfolio.id == portfolio_id)
    return db.execute(stmt).scalars().first()
