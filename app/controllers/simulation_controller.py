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

router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.post("/start", response_model=SimulationStartResponse)
def start_simulation_endpoint(
    payload: SimulationStartRequest,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> SimulationStartResponse:
    return start_simulation(db=db, user_id=user_id, payload=payload)


@router.post("/chat", response_model=SimulationChatResponse)
def chat_simulation_endpoint(
    payload: SimulationChatRequest,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> SimulationChatResponse:
    try:
        return chat_simulation(db=db, user_id=user_id, payload=payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/analyze", response_model=SimulationAnalyzeResponse)
def analyze_simulation_endpoint(
    payload: SimulationAnalyzeRequest,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> SimulationAnalyzeResponse:
    try:
        return analyze_simulation(db=db, user_id=user_id, session_id=payload.session_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
