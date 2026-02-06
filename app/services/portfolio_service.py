import uuid

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.db.repositories.portfolio_repository import (
    count_portfolios_by_user,
    create_portfolio,
    get_portfolio_by_id,
    get_portfolios_by_user,
)
from app.db.repositories.portfolio_repository import (
    delete_portfolio as delete_portfolio_repo,
)
from app.schemas.portfolio import PortfolioListResponse, PortfolioResponse, PortfolioSourceType


def _to_portfolio_response(portfolio) -> PortfolioResponse:
    return PortfolioResponse(
        id=portfolio.id,
        user_id=portfolio.user_id,
        project_id=portfolio.project_id,
        source_type=PortfolioSourceType(portfolio.source_type),
        source_url=portfolio.source_url,
        filename=portfolio.original_filename,
        extracted_text=portfolio.extracted_text,
    )


async def upload_portfolio(
    db: Session,
    user_id: int,
    source_type: PortfolioSourceType,
    source_url: str | None,
    pdf_file: UploadFile | None,
    project_id: uuid.UUID | None,
) -> PortfolioResponse:
    extracted_text = ""

    portfolio = create_portfolio(
        db=db,
        user_id=user_id,
        source_type=source_type.value,
        source_url=source_url,
        original_filename=pdf_file.filename if pdf_file else None,
        extracted_text=extracted_text,
        project_id=project_id,
    )
    return _to_portfolio_response(portfolio)


async def get_portfolio(db: Session, portfolio_id: int, user_id: int) -> PortfolioResponse | None:
    portfolio = get_portfolio_by_id(db=db, portfolio_id=portfolio_id, user_id=user_id)
    if not portfolio:
        return None
    return _to_portfolio_response(portfolio)


async def list_portfolios(
    db: Session,
    user_id: int,
    limit: int,
    offset: int,
    project_id: uuid.UUID | None,
) -> PortfolioListResponse:
    portfolios = get_portfolios_by_user(
        db=db,
        user_id=user_id,
        limit=limit,
        offset=offset,
        project_id=project_id,
    )
    total = count_portfolios_by_user(db=db, user_id=user_id, project_id=project_id)

    items = [_to_portfolio_response(p) for p in portfolios]
    return PortfolioListResponse(items=items, total=total)


async def delete_portfolio(db: Session, portfolio_id: int, user_id: int) -> bool:
    return delete_portfolio_repo(db=db, portfolio_id=portfolio_id, user_id=user_id)
