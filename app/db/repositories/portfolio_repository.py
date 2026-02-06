from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.entities.portfolio import ExtractionStatus, Portfolio, PortfolioSourceType


def create_portfolio(
    db: Session,
    user_id: int,
    source_type: PortfolioSourceType,
    source_url: str | None,
    original_filename: str | None,
    extracted_text: str,
    extraction_status: ExtractionStatus | str = ExtractionStatus.PENDING,
    error_message: str | None = None,
) -> Portfolio:
    # extraction_status가 문자열인 경우 enum으로 변환
    if isinstance(extraction_status, str):
        extraction_status = ExtractionStatus(extraction_status)
    
    # SQLAlchemy가 enum 값을 올바르게 사용하도록 enum의 value를 명시적으로 전달
    # DB enum은 소문자 값("notion", "blog", "pdf")을 기대하므로 enum.value를 사용하여
    # SQLAlchemy가 enum 이름("BLOG") 대신 enum 값("blog")을 사용하도록 함
    portfolio = Portfolio(
        user_id=user_id,
        source_type=source_type.value if isinstance(source_type, PortfolioSourceType) else source_type,
        source_url=source_url,
        original_filename=original_filename,
        extracted_text=extracted_text,
        extraction_status=extraction_status,
        error_message=error_message,
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


def get_portfolio_by_id(db: Session, portfolio_id: int, user_id: int) -> Portfolio | None:
    stmt = select(Portfolio).where(Portfolio.id == portfolio_id, Portfolio.user_id == user_id)
    return db.execute(stmt).scalars().first()


def get_portfolios_by_user(
    db: Session, user_id: int, limit: int = 50, offset: int = 0
) -> list[Portfolio]:
    stmt = (
        select(Portfolio)
        .where(Portfolio.user_id == user_id)
        .order_by(Portfolio.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(stmt).scalars().all())


def count_portfolios_by_user(db: Session, user_id: int) -> int:
    stmt = select(func.count(Portfolio.id)).where(Portfolio.user_id == user_id)
    return int(db.execute(stmt).scalar_one())


def update_portfolio_status(
    db: Session,
    portfolio_id: int,
    extraction_status: ExtractionStatus | str,
    error_message: str | None = None,
) -> Portfolio | None:
    portfolio = db.get(Portfolio, portfolio_id)
    if not portfolio:
        return None
    # extraction_status가 문자열인 경우 enum으로 변환
    if isinstance(extraction_status, str):
        extraction_status = ExtractionStatus(extraction_status)
    portfolio.extraction_status = extraction_status
    if error_message is not None:
        portfolio.error_message = error_message
    db.commit()
    db.refresh(portfolio)
    return portfolio


def delete_portfolio(db: Session, portfolio_id: int, user_id: int) -> bool:
    """
    포트폴리오를 삭제합니다.
    user_id로 소유권을 확인합니다.
    Returns:
        bool: 삭제 성공 여부 (포트폴리오가 존재하고 소유자가 맞으면 True)
    """
    stmt = select(Portfolio).where(Portfolio.id == portfolio_id, Portfolio.user_id == user_id)
    portfolio = db.execute(stmt).scalars().first()
    if not portfolio:
        return False
    db.delete(portfolio)
    db.commit()
    return True