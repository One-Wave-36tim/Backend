from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.auth import CurrentUserId
from app.db.session import get_db
from app.schemas.portfolio import PortfolioListResponse, PortfolioResponse, PortfolioSourceType
from app.services.portfolio_service import (
    delete_portfolio,
    get_portfolio,
    list_portfolios,
    upload_portfolio,
)

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


@router.post("/upload", response_model=PortfolioResponse)
async def upload_portfolio_endpoint(
    source_type: str = Form(
        ..., description="포트폴리오 소스 타입", examples=["notion", "blog", "pdf"]
    ),
    source_url: str | None = Form(None, description="노션/블로그 URL (notion/blog인 경우 필수)"),
    pdf_file: UploadFile | None = File(None, description="PDF 파일 (pdf인 경우 필수)"),
    project_id: UUID | None = Form(None, description="귀속할 지원 프로젝트 ID"),
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> PortfolioResponse:
    try:
        source_type_enum = PortfolioSourceType(source_type.lower())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="source_type must be notion|blog|pdf") from exc

    if (
        source_type_enum in {PortfolioSourceType.NOTION, PortfolioSourceType.BLOG}
        and not source_url
    ):
        raise HTTPException(status_code=400, detail="source_url is required for notion/blog")
    if source_type_enum == PortfolioSourceType.PDF and not pdf_file:
        raise HTTPException(status_code=400, detail="PDF file is required")

    return await upload_portfolio(
        db=db,
        user_id=user_id,
        source_type=source_type_enum,
        source_url=source_url,
        pdf_file=pdf_file,
        project_id=project_id,
    )


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio_endpoint(
    portfolio_id: int,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> PortfolioResponse:
    portfolio = await get_portfolio(db=db, portfolio_id=portfolio_id, user_id=user_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


@router.get("/", response_model=PortfolioListResponse)
async def list_portfolios_endpoint(
    limit: int = 50,
    offset: int = 0,
    project_id: UUID | None = None,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> PortfolioListResponse:
    return await list_portfolios(
        db=db,
        user_id=user_id,
        limit=limit,
        offset=offset,
        project_id=project_id,
    )


@router.delete("/{portfolio_id}")
async def delete_portfolio_endpoint(
    portfolio_id: int,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
):
    deleted = await delete_portfolio(db=db, portfolio_id=portfolio_id, user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return {"message": "Portfolio deleted successfully"}
