import os
import tempfile
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.db.repositories.portfolio_repository import (
    count_portfolios_by_user,
    create_portfolio,
    get_portfolio_by_id,
    get_portfolios_by_user,
)
from app.db.entities.portfolio import ExtractionStatus
from app.db.repositories.user_settings_repository import get_notion_key_by_user
from app.schemas.portfolio import PortfolioListResponse, PortfolioResponse, PortfolioSourceType
from app.services.text_extractor import TextExtractor


async def upload_portfolio(
    db: Session,
    user_id: int,
    source_type: PortfolioSourceType,
    source_url: str | None = None,
    pdf_file: UploadFile | None = None,
) -> PortfolioResponse:
    extracted_text = ""
    extraction_status = "pending"
    error_message: str | None = None
    original_filename: str | None = None
    temp_path: str | None = None

    try:
        if source_type == PortfolioSourceType.NOTION:
            if not source_url:
                raise ValueError("source_url is required for Notion")
            notion_api_key = get_notion_key_by_user(db=db, user_id=user_id)
            if not notion_api_key:
                raise ValueError("Notion API key is not registered for this user")
            extractor = TextExtractor(notion_api_key=notion_api_key)
            extracted_text = await extractor.extract_from_notion(source_url)
            extraction_status = "success"
        elif source_type == PortfolioSourceType.BLOG:
            if not source_url:
                raise ValueError("source_url is required for Blog")
            extractor = TextExtractor()
            extracted_text = await extractor.extract_from_blog(source_url)
            extraction_status = "success"
        elif source_type == PortfolioSourceType.PDF:
            if not pdf_file:
                raise ValueError("PDF file is required")
            original_filename = pdf_file.filename or "uploaded.pdf"
            suffix = Path(original_filename).suffix or ".pdf"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as buffer:
                temp_path = buffer.name
                content = await pdf_file.read()
                buffer.write(content)
            extractor = TextExtractor()
            extracted_text = await extractor.extract_from_pdf(temp_path)
            extraction_status = "success"
            source_url = None
        else:
            raise ValueError(f"Unsupported source_type: {source_type}")
    except Exception as exc:
        extraction_status = "failed"
        error_message = str(exc)
        extracted_text = ""
    finally:
        if temp_path:
            try:
                os.remove(temp_path)
            except OSError:
                pass

    # extraction_status 문자열을 enum으로 변환
    extraction_status_enum = (
        ExtractionStatus.SUCCESS
        if extraction_status == "success"
        else ExtractionStatus.FAILED
        if extraction_status == "failed"
        else ExtractionStatus.PENDING
    )

    portfolio = create_portfolio(
        db=db,
        user_id=user_id,
        source_type=source_type,
        source_url=source_url,
        original_filename=original_filename,
        extracted_text=extracted_text,
        extraction_status=extraction_status_enum,
        error_message=error_message,
    )
    return PortfolioResponse.model_validate(portfolio)


async def get_portfolio(db: Session, portfolio_id: int, user_id: int) -> PortfolioResponse | None:
    portfolio = get_portfolio_by_id(db=db, portfolio_id=portfolio_id, user_id=user_id)
    if not portfolio:
        return None
    return PortfolioResponse.model_validate(portfolio)


async def list_portfolios(
    db: Session, user_id: int, limit: int = 50, offset: int = 0
) -> PortfolioListResponse:
    portfolios = get_portfolios_by_user(db=db, user_id=user_id, limit=limit, offset=offset)
    total = count_portfolios_by_user(db=db, user_id=user_id)
    return PortfolioListResponse(
        portfolios=[PortfolioResponse.model_validate(p) for p in portfolios],
        total=total,
    )


async def delete_portfolio(db: Session, portfolio_id: int, user_id: int) -> bool:
    """
    포트폴리오를 삭제합니다.
    Returns:
        bool: 삭제 성공 여부
    """
    from app.db.repositories.portfolio_repository import delete_portfolio as delete_portfolio_repo
    
    return delete_portfolio_repo(db=db, portfolio_id=portfolio_id, user_id=user_id)