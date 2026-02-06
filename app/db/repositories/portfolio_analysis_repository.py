from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.entities.portfolio_analysis import PortfolioAnalysis


def replace_portfolio_analysis(
    db: Session, portfolio_id: int, analysis_text: str
) -> PortfolioAnalysis:
    db.execute(
        delete(PortfolioAnalysis).where(PortfolioAnalysis.portfolio_id == portfolio_id)
    )
    # Commit deletion first to prevent duplicate rows on repeated calls.
    db.commit()

    analysis = PortfolioAnalysis(portfolio_id=portfolio_id, analysis_text=analysis_text)
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def find_latest_portfolio_analysis(
    db: Session, portfolio_id: int
) -> PortfolioAnalysis | None:
    stmt = (
        select(PortfolioAnalysis)
        .where(PortfolioAnalysis.portfolio_id == portfolio_id)
        .order_by(PortfolioAnalysis.created_at.desc())
        .limit(1)
    )
    return db.execute(stmt).scalars().first()
