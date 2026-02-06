from itertools import count

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.schemas.portfolio import PortfolioListResponse, PortfolioResponse, PortfolioSourceType

_PORTFOLIOS: dict[int, PortfolioResponse] = {}
_PORTFOLIO_ID_SEQ = count(1)


async def upload_portfolio(
    db: Session,
    user_id: int,
    source_type: PortfolioSourceType,
    source_url: str | None,
    pdf_file: UploadFile | None,
) -> PortfolioResponse:
    portfolio_id = next(_PORTFOLIO_ID_SEQ)
    item = PortfolioResponse(
        id=portfolio_id,
        user_id=user_id,
        source_type=source_type,
        source_url=source_url,
        filename=pdf_file.filename if pdf_file else None,
    )
    _PORTFOLIOS[portfolio_id] = item
    return item


async def get_portfolio(db: Session, portfolio_id: int, user_id: int) -> PortfolioResponse | None:
    item = _PORTFOLIOS.get(portfolio_id)
    if not item or item.user_id != user_id:
        return None
    return item


async def list_portfolios(
    db: Session, user_id: int, limit: int, offset: int
) -> PortfolioListResponse:
    items = [item for item in _PORTFOLIOS.values() if item.user_id == user_id]
    total = len(items)
    sliced = items[offset : offset + limit]
    return PortfolioListResponse(items=sliced, total=total)


async def delete_portfolio(db: Session, portfolio_id: int, user_id: int) -> bool:
    item = _PORTFOLIOS.get(portfolio_id)
    if not item or item.user_id != user_id:
        return False
    del _PORTFOLIOS[portfolio_id]
    return True