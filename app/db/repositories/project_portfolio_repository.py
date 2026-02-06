import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.entities.project import PortfolioItem, ProjectPortfolio


def create_portfolio_item(
    db: Session,
    user_id: int,
    title: str,
    tech_stack: list[str] | None,
    period_start: date | None,
    period_end: date | None,
    summary: str | None = None,
) -> PortfolioItem:
    row = PortfolioItem(
        user_id=user_id,
        title=title,
        tech_stack=tech_stack,
        period_start=period_start,
        period_end=period_end,
        summary=summary,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_portfolio_item_by_id(
    db: Session,
    user_id: int,
    portfolio_item_id: uuid.UUID,
) -> PortfolioItem | None:
    stmt = select(PortfolioItem).where(
        PortfolioItem.id == portfolio_item_id,
        PortfolioItem.user_id == user_id,
    )
    return db.execute(stmt).scalars().first()


def get_project_portfolio_link(
    db: Session,
    project_id: uuid.UUID,
    portfolio_item_id: uuid.UUID,
) -> ProjectPortfolio | None:
    stmt = select(ProjectPortfolio).where(
        ProjectPortfolio.project_id == project_id,
        ProjectPortfolio.portfolio_item_id == portfolio_item_id,
    )
    return db.execute(stmt).scalars().first()


def create_project_portfolio_link(
    db: Session,
    project_id: uuid.UUID,
    portfolio_item_id: uuid.UUID,
    role_type: str = "SUB",
    is_representative: bool = False,
) -> ProjectPortfolio:
    row = ProjectPortfolio(
        project_id=project_id,
        portfolio_item_id=portfolio_item_id,
        role_type=role_type,
        is_representative=is_representative,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_project_portfolios(
    db: Session,
    project_id: uuid.UUID,
    user_id: int,
) -> list[tuple[ProjectPortfolio, PortfolioItem]]:
    stmt = (
        select(ProjectPortfolio, PortfolioItem)
        .join(PortfolioItem, PortfolioItem.id == ProjectPortfolio.portfolio_item_id)
        .where(ProjectPortfolio.project_id == project_id, PortfolioItem.user_id == user_id)
        .order_by(ProjectPortfolio.created_at.asc())
    )
    rows = db.execute(stmt).all()
    return [(row[0], row[1]) for row in rows]


def set_representative_portfolio(
    db: Session,
    project_id: uuid.UUID,
    portfolio_item_id: uuid.UUID,
    is_representative: bool,
) -> ProjectPortfolio:
    target = get_project_portfolio_link(
        db=db,
        project_id=project_id,
        portfolio_item_id=portfolio_item_id,
    )
    if target is None:
        target = create_project_portfolio_link(
            db=db,
            project_id=project_id,
            portfolio_item_id=portfolio_item_id,
            is_representative=is_representative,
        )
        if not is_representative:
            return target

    if is_representative:
        stmt = select(ProjectPortfolio).where(ProjectPortfolio.project_id == project_id)
        rows = list(db.execute(stmt).scalars().all())
        for row in rows:
            row.is_representative = row.portfolio_item_id == portfolio_item_id
            db.add(row)
        db.commit()
    else:
        target.is_representative = False
        db.add(target)
        db.commit()

    db.refresh(target)
    return target
