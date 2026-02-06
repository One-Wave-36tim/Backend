import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.portfolio import (
    PortfolioQuestionsRequest,
    PortfolioQuestionsResponse,
)
from app.services.portfolio_questions_service import generate_portfolio_questions

router = APIRouter(prefix="/portfolios", tags=["portfolios"])
logger = logging.getLogger(__name__)


@router.post("/{portfolio_id}/questions", response_model=PortfolioQuestionsResponse)
def questions(
    portfolio_id: int,
    payload: PortfolioQuestionsRequest,
    db: Session = Depends(get_db),
) -> PortfolioQuestionsResponse:
    try:
        return generate_portfolio_questions(
            db=db,
            portfolio_id=portfolio_id,
            qa_conversation=payload.qa_conversation,
            stop_requested=payload.stop_requested,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.exception("Portfolio questions failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Portfolio questions unexpected failure")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
