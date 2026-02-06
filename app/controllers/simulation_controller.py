from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import CurrentUserId
from app.core.errors import NotFoundError
from app.db.session import get_db
from app.schemas.simulation import (
    SimulationAnalyzeRequest,
    SimulationAnalyzeResponse,
    SimulationChatRequest,
    SimulationChatResponse,
    SimulationStartRequest,
    SimulationStartResponse,
)
from app.services.simulation_service import analyze_simulation, chat_simulation, start_simulation

router = APIRouter(prefix="/simulation", tags=["직무시뮬레이션(레거시)"])


@router.post(
    "/start",
    response_model=SimulationStartResponse,
    summary="(레거시) 시뮬레이션 시작",
    description="기존 클라이언트 호환용 시뮬레이션 시작 API입니다.",
    response_description="생성된 시뮬레이션 세션",
)
def start_simulation_endpoint(
    payload: SimulationStartRequest,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> SimulationStartResponse:
    try:
        return start_simulation(db=db, user_id=user_id, payload=payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/chat",
    response_model=SimulationChatResponse,
    summary="(레거시) 시뮬레이션 채팅",
    description="기존 클라이언트 호환용 시뮬레이션 채팅 API입니다.",
    response_description="시뮬레이션 응답 데이터",
)
def chat_simulation_endpoint(
    payload: SimulationChatRequest,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> SimulationChatResponse:
    try:
        return chat_simulation(db=db, user_id=user_id, payload=payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/analyze",
    response_model=SimulationAnalyzeResponse,
    summary="(레거시) 시뮬레이션 분석",
    description="기존 클라이언트 호환용 시뮬레이션 분석 API입니다.",
    response_description="분석 결과 리포트",
)
def analyze_simulation_endpoint(
    payload: SimulationAnalyzeRequest,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> SimulationAnalyzeResponse:
    try:
        return analyze_simulation(db=db, user_id=user_id, session_id=payload.session_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
