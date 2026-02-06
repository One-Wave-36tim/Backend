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

router = APIRouter(prefix="/portfolios", tags=["포트폴리오"])


@router.post(
    "/upload",
    response_model=PortfolioResponse,
    summary="포트폴리오 업로드",
    description="노션/블로그/PDF 소스의 포트폴리오를 업로드하고 project_id에 귀속시킵니다.",
    response_description="업로드된 포트폴리오 정보",
)
async def upload_portfolio_endpoint(
    source_type: str = Form(
        ..., description="포트폴리오 소스 타입", examples=["notion", "blog", "pdf"]
    ),
    source_url: str | None = Form(None, description="노션/블로그 URL (notion/blog인 경우 필수)"),
    pdf_file: UploadFile | None = File(None, description="PDF 파일 (pdf인 경우 필수)"),
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
    )


@router.get(
    "/{portfolio_id}",
    response_model=PortfolioResponse,
    summary="포트폴리오 단건 조회",
    description="포트폴리오 ID로 단건 데이터를 조회합니다.",
    response_description="포트폴리오 데이터",
)
async def get_portfolio_endpoint(
    portfolio_id: int,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> PortfolioResponse:
    portfolio = await get_portfolio(db=db, portfolio_id=portfolio_id, user_id=user_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


@router.get(
    "/",
    response_model=PortfolioListResponse,
    summary="포트폴리오 목록 조회",
    description="사용자 포트폴리오 목록을 조회하며 project_id 필터를 지원합니다.",
    response_description="포트폴리오 목록",
)
async def list_portfolios_endpoint(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> PortfolioListResponse:
    return await list_portfolios(
        db=db,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )


@router.delete(
    "/{portfolio_id}",
    summary="포트폴리오 삭제",
    description="포트폴리오를 삭제합니다.",
    response_description="삭제 결과",
)
async def delete_portfolio_endpoint(
    portfolio_id: int,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
):
    deleted = await delete_portfolio(db=db, portfolio_id=portfolio_id, user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return {"message": "Portfolio deleted successfully"}
