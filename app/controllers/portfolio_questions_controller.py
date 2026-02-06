import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import CurrentUserId
from app.db.session import get_db
from app.schemas.portfolio import (
    PortfolioQuestionsRequest,
    PortfolioQuestionsResponse,
)
from app.services.portfolio_questions_service import generate_portfolio_questions

router = APIRouter(prefix="/portfolios", tags=["포트폴리오"])
logger = logging.getLogger(__name__)


@router.post(
    "/{portfolio_id}/questions",
    response_model=PortfolioQuestionsResponse,
    summary="포트폴리오 심화 질문 생성",
    description="포트폴리오 분석 결과와 대화 이력을 바탕으로 꼬리 질문을 생성합니다.",
    response_description="생성된 질문 또는 종료 안내",
)
def questions(
    portfolio_id: int,
    payload: PortfolioQuestionsRequest,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> PortfolioQuestionsResponse:
    try:
        return generate_portfolio_questions(
            db=db,
            portfolio_id=portfolio_id,
            user_id=user_id,
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
