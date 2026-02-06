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

router = APIRouter(prefix="/v2/sessions", tags=["세션 코어(v2)"])


@router.post(
    "",
    response_model=SessionStartResponse,
    summary="(v2) 통합 세션 시작",
    description="세션 코어 API로 DEEP/MOCK/SIMULATION 세션을 생성합니다.",
    response_description="생성된 세션 및 초기 턴",
)
def start_session_endpoint(
    payload: SessionStartRequest,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> SessionStartResponse:
    try:
        return start_unified_session(db=db, user_id=user_id, payload=payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/{session_id}/turns",
    response_model=SessionAppendTurnResponse,
    summary="(v2) 세션 턴 추가",
    description="세션 코어 API로 턴을 추가하고(옵션) 자동 응답 턴을 생성합니다.",
    response_description="추가된 턴 정보",
)
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


@router.post(
    "/{session_id}/analyze",
    response_model=SessionAnalyzeResponse,
    summary="(v2) 세션 분석",
    description="세션 코어 API로 세션 결과를 계산하고 result_json을 갱신합니다.",
    response_description="분석 결과",
)
def analyze_session_endpoint(
    session_id: UUID,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> SessionAnalyzeResponse:
    try:
        return analyze_unified_session(db=db, user_id=user_id, session_id=session_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/{session_id}",
    response_model=SessionDetailResponse,
    summary="(v2) 세션 조회",
    description="세션 코어 API로 세션 상세와 턴 내역을 조회합니다.",
    response_description="세션 상세 데이터",
)
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
