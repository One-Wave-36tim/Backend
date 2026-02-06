import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import CurrentUserId
from app.db.session import get_db
from app.schemas.portfolio import PortfolioAnalysisResponse
from app.services.portfolio_analysis_service import analyze_portfolio

router = APIRouter(prefix="/portfolios", tags=["포트폴리오"])
logger = logging.getLogger(__name__)


@router.post(
    "/{portfolio_id}/analyze",
    response_model=PortfolioAnalysisResponse,
    summary="포트폴리오 분석",
    description="포트폴리오 텍스트를 기반으로 분석 결과를 생성/저장합니다.",
    response_description="생성된 포트폴리오 분석 결과",
)
def analyze(
    portfolio_id: int,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> PortfolioAnalysisResponse:
    try:
        return analyze_portfolio(db=db, portfolio_id=portfolio_id, user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.exception("Portfolio analysis failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Portfolio analysis unexpected failure")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
