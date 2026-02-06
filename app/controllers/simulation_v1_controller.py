from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import CurrentUserId
from app.core.errors import NotFoundError
from app.db.session import get_db
from app.schemas.simulation_v1 import (
    SimulationPreviewResponse,
    SimulationResultResponse,
    SimulationTurnRequest,
    SimulationTurnResponse,
    SimulationV1SessionResponse,
    SimulationV1StartRequest,
    SimulationV1StartResponse,
)
from app.services.simulation_v1_service import (
    append_simulation_turn_v1,
    get_simulation_preview,
    get_simulation_result_v1,
    get_simulation_session_v1,
    start_simulation_v1,
)

router = APIRouter(prefix="/v1", tags=["직무시뮬레이션"])


@router.get(
    "/projects/{project_id}/simulations/preview",
    response_model=SimulationPreviewResponse,
    summary="시뮬레이션 시작 화면 데이터",
    description="시나리오 프리뷰와 시작 CTA에 필요한 데이터를 반환합니다.",
    response_description="시뮬레이션 프리뷰 데이터",
)
def get_simulation_preview_endpoint(project_id: UUID) -> SimulationPreviewResponse:
    return get_simulation_preview(project_id=project_id)


@router.post(
    "/projects/{project_id}/simulations/start",
    response_model=SimulationV1StartResponse,
    summary="시뮬레이션 시작",
    description="직무 시뮬레이션 세션을 생성하고 초기 메시지를 반환합니다.",
    response_description="생성된 시뮬레이션 세션 정보",
    responses={404: {"description": "프로젝트를 찾을 수 없음"}},
)
def start_simulation_v1_endpoint(
    project_id: UUID,
    payload: SimulationV1StartRequest,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> SimulationV1StartResponse:
    try:
        return start_simulation_v1(
            db=db,
            user_id=user_id,
            project_id=project_id,
            payload=payload,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/simulations/sessions/{session_id}",
    response_model=SimulationV1SessionResponse,
    summary="시뮬레이션 세션 조회",
    description="새로고침/재진입 시 현재 시뮬레이션 대화 내역을 조회합니다.",
    response_description="시뮬레이션 현재 상태",
    responses={404: {"description": "세션을 찾을 수 없음"}},
)
def get_simulation_session_v1_endpoint(
    session_id: UUID,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> SimulationV1SessionResponse:
    try:
        return get_simulation_session_v1(db=db, user_id=user_id, session_id=session_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/simulations/sessions/{session_id}/turns",
    response_model=SimulationTurnResponse,
    summary="시뮬레이션 턴 진행",
    description="사용자 메시지를 저장하고 NPC 다음 메시지를 반환합니다.",
    response_description="추가된 메시지 및 종료 여부",
    responses={404: {"description": "세션을 찾을 수 없음"}},
)
def append_simulation_turn_v1_endpoint(
    session_id: UUID,
    payload: SimulationTurnRequest,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> SimulationTurnResponse:
    try:
        return append_simulation_turn_v1(
            db=db,
            user_id=user_id,
            session_id=session_id,
            text=payload.text,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/simulations/sessions/{session_id}/result",
    response_model=SimulationResultResponse,
    summary="시뮬레이션 결과 조회",
    description="직무 시뮬레이션 결과 페이지 렌더링용 캐시 데이터를 반환합니다.",
    response_description="시뮬레이션 결과 데이터",
    responses={404: {"description": "세션을 찾을 수 없음"}},
)
def get_simulation_result_v1_endpoint(
    session_id: UUID,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> SimulationResultResponse:
    try:
        return get_simulation_result_v1(db=db, user_id=user_id, session_id=session_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

