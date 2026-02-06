from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.db.repositories.portfolio_repository import (
    count_portfolios_by_user,
    create_portfolio,
    delete_portfolio as delete_portfolio_repo,
    get_portfolio_by_id,
    get_portfolios_by_user,
)
from app.schemas.portfolio import PortfolioListResponse, PortfolioResponse, PortfolioSourceType


async def upload_portfolio(
    db: Session,
    user_id: int,
    source_type: PortfolioSourceType,
    source_url: str | None,
    pdf_file: UploadFile | None,
) -> PortfolioResponse:
    # TODO: 텍스트 추출 로직 추가 (notion, blog, pdf에서 텍스트 추출)
    extracted_text = ""
    
    portfolio = create_portfolio(
        db=db,
        user_id=user_id,
        source_type=source_type.value,
        source_url=source_url,
        original_filename=pdf_file.filename if pdf_file else None,
        extracted_text=extracted_text,
    )
    
    return PortfolioResponse(
        id=portfolio.id,
        user_id=portfolio.user_id,
        source_type=PortfolioSourceType(portfolio.source_type),
        source_url=portfolio.source_url,
        filename=portfolio.original_filename,
        extracted_text=portfolio.extracted_text,
    )


async def get_portfolio(db: Session, portfolio_id: int, user_id: int) -> PortfolioResponse | None:
    portfolio = get_portfolio_by_id(db=db, portfolio_id=portfolio_id, user_id=user_id)
    if not portfolio:
        return None
    
    return PortfolioResponse(
        id=portfolio.id,
        user_id=portfolio.user_id,
        source_type=PortfolioSourceType(portfolio.source_type),
        source_url=portfolio.source_url,
        filename=portfolio.original_filename,
        extracted_text=portfolio.extracted_text,
    )


async def list_portfolios(
    db: Session, user_id: int, limit: int, offset: int
) -> PortfolioListResponse:
    portfolios = get_portfolios_by_user(db=db, user_id=user_id, limit=limit, offset=offset)
    total = count_portfolios_by_user(db=db, user_id=user_id)
    
    items = [
        PortfolioResponse(
            id=p.id,
            user_id=p.user_id,
            source_type=PortfolioSourceType(p.source_type),
            source_url=p.source_url,
            filename=p.original_filename,
            extracted_text=p.extracted_text,
        )
        for p in portfolios
    ]
    
    return PortfolioListResponse(items=items, total=total)


async def delete_portfolio(db: Session, portfolio_id: int, user_id: int) -> bool:
    """
    포트폴리오를 삭제합니다.
    Returns:
        bool: 삭제 성공 여부
    """
    return delete_portfolio_repo(db=db, portfolio_id=portfolio_id, user_id=user_id)