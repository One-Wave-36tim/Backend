from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import CurrentUserId
from app.core.errors import NotFoundError
from app.db.session import get_db
from app.schemas.session import (
    SessionAnalyzeResponse,
    SessionAppendTurnResponse,
    SessionDetailResponse,
    SessionStartRequest,
    SessionStartResponse,
    SessionTurnCreateRequest,
)
from app.services.session_service import (
    analyze_unified_session,
    append_unified_turn,
    get_unified_session_detail,
    start_unified_session,
)

router = APIRouter(prefix="/v2/sessions", tags=["sessions-v2"])


@router.post("", response_model=SessionStartResponse)
def start_session_endpoint(
    payload: SessionStartRequest,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> SessionStartResponse:
    try:
        return start_unified_session(db=db, user_id=user_id, payload=payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{session_id}/turns", response_model=SessionAppendTurnResponse)
def append_turn_endpoint(
    session_id: UUID,
    payload: SessionTurnCreateRequest,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> SessionAppendTurnResponse:
    try:
        return append_unified_turn(
            db=db,
            user_id=user_id,
            session_id=session_id,
            payload=payload,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{session_id}/analyze", response_model=SessionAnalyzeResponse)
def analyze_session_endpoint(
    session_id: UUID,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> SessionAnalyzeResponse:
    try:
        return analyze_unified_session(db=db, user_id=user_id, session_id=session_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{session_id}", response_model=SessionDetailResponse)
def get_session_endpoint(
    session_id: UUID,
    include_turns: bool = True,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> SessionDetailResponse:
    try:
        return get_unified_session_detail(
            db=db,
            user_id=user_id,
            session_id=session_id,
            include_turns=include_turns,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
