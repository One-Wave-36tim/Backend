import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.entities.portfolio import Portfolio


def create_portfolio(
    db: Session,
    user_id: int,
    source_type: str,
    source_url: str | None,
    original_filename: str | None,
    extracted_text: str = "",
    project_id: uuid.UUID | None = None,
    is_representative: bool = False,
    meta: dict | None = None,
) -> Portfolio:
    portfolio = Portfolio(
        user_id=user_id,
        project_id=project_id,
        source_type=source_type,
        source_url=source_url,
        original_filename=original_filename,
        extracted_text=extracted_text,
        is_representative=is_representative,
        meta=meta,
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


def get_portfolio_by_id(db: Session, portfolio_id: int, user_id: int) -> Portfolio | None:
    stmt = select(Portfolio).where(Portfolio.id == portfolio_id, Portfolio.user_id == user_id)
    return db.execute(stmt).scalars().first()


def find_portfolio_by_id(db: Session, portfolio_id: int, user_id: int) -> Portfolio | None:
    return get_portfolio_by_id(db=db, portfolio_id=portfolio_id, user_id=user_id)


def get_portfolios_by_user(
    db: Session,
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    project_id: uuid.UUID | None = None,
) -> list[Portfolio]:
    stmt = select(Portfolio).where(Portfolio.user_id == user_id)
    if project_id is not None:
        stmt = stmt.where(Portfolio.project_id == project_id)
    stmt = stmt.order_by(Portfolio.created_at.desc()).limit(limit).offset(offset)
    return list(db.execute(stmt).scalars().all())


def count_portfolios_by_user(db: Session, user_id: int, project_id: uuid.UUID | None = None) -> int:
    stmt = select(func.count(Portfolio.id)).where(Portfolio.user_id == user_id)
    if project_id is not None:
        stmt = stmt.where(Portfolio.project_id == project_id)
    return int(db.execute(stmt).scalar_one())


def delete_portfolio(db: Session, portfolio_id: int, user_id: int) -> bool:
    stmt = select(Portfolio).where(Portfolio.id == portfolio_id, Portfolio.user_id == user_id)
    portfolio = db.execute(stmt).scalars().first()
    if not portfolio:
        return False
    db.delete(portfolio)
    db.commit()
    return True


def get_portfolios_by_ids(
    db: Session,
    user_id: int,
    portfolio_ids: list[int],
) -> list[Portfolio]:
    if not portfolio_ids:
        return []
    stmt = (
        select(Portfolio)
        .where(Portfolio.user_id == user_id, Portfolio.id.in_(portfolio_ids))
        .order_by(Portfolio.id.asc())
    )
    return list(db.execute(stmt).scalars().all())


def update_portfolio_extracted_text(
    db: Session,
    portfolio: Portfolio,
    extracted_text: str,
    meta_patch: dict | None = None,
) -> Portfolio:
    meta = portfolio.meta or {}
    if meta_patch:
        meta.update(meta_patch)
    portfolio.extracted_text = extracted_text
    portfolio.meta = meta
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


def mark_portfolio_crawl_failed(
    db: Session,
    portfolio: Portfolio,
    reason: str,
) -> Portfolio:
    meta = portfolio.meta or {}
    meta["crawlStatus"] = "FAILED"
    meta["crawlError"] = reason[:500]
    meta["crawlUpdatedAt"] = datetime.now(tz=UTC).isoformat()
    portfolio.meta = meta
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio
