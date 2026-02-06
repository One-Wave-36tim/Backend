import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.portfolio import PortfolioAnalysisResponse
from app.services.portfolio_analysis_service import analyze_portfolio

router = APIRouter(prefix="/portfolios", tags=["portfolios"])
logger = logging.getLogger(__name__)


@router.post("/{portfolio_id}/analyze", response_model=PortfolioAnalysisResponse)
def analyze(portfolio_id: int, db: Session = Depends(get_db)) -> PortfolioAnalysisResponse:
    try:
        return analyze_portfolio(db, portfolio_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.exception("Portfolio analysis failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Portfolio analysis unexpected failure")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
