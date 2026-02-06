from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import CurrentUserId
from app.core.errors import NotFoundError
from app.db.session import get_db
from app.schemas.mock_interview import (
    MockInterviewAnswerRequest,
    MockInterviewAnswerResponse,
    MockInterviewResultResponse,
    MockInterviewSaveResponse,
    MockInterviewStartRequest,
    MockInterviewStartResponse,
)
from app.services.mock_interview_service import (
    answer_mock_interview,
    get_mock_interview_result,
    save_mock_interview_result,
    start_mock_interview,
)

router = APIRouter(prefix="/v1", tags=["모의면접"])


@router.post(
    "/projects/{project_id}/mock-interview/start",
    response_model=MockInterviewStartResponse,
    summary="모의면접 시작",
    description="모의면접 세션을 생성하고 첫 질문을 반환합니다.",
    response_description="시작된 모의면접 세션 정보",
    responses={404: {"description": "프로젝트를 찾을 수 없음"}},
)
def start_mock_interview_endpoint(
    project_id: UUID,
    payload: MockInterviewStartRequest,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> MockInterviewStartResponse:
    try:
        return start_mock_interview(
            db=db,
            user_id=user_id,
            project_id=project_id,
            payload=payload,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/mock-interviews/sessions/{session_id}/answer",
    response_model=MockInterviewAnswerResponse,
    summary="모의면접 답변 제출",
    description="답변을 저장하고 다음 질문 또는 완료 상태를 반환합니다.",
    response_description="다음 질문/진행률/완료 정보",
    responses={404: {"description": "세션을 찾을 수 없음"}},
)
def answer_mock_interview_endpoint(
    session_id: UUID,
    payload: MockInterviewAnswerRequest,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> MockInterviewAnswerResponse:
    try:
        return answer_mock_interview(
            db=db,
            user_id=user_id,
            session_id=session_id,
            question_id=payload.questionId,
            answer=payload.answer,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/mock-interviews/sessions/{session_id}/result",
    response_model=MockInterviewResultResponse,
    summary="모의면접 결과 조회",
    description="모의면접 세션의 캐시된 결과 페이지 데이터를 반환합니다.",
    response_description="모의면접 결과 데이터",
    responses={404: {"description": "세션을 찾을 수 없음"}},
)
def get_mock_interview_result_endpoint(
    session_id: UUID,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> MockInterviewResultResponse:
    try:
        return get_mock_interview_result(db=db, user_id=user_id, session_id=session_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/mock-interviews/sessions/{session_id}/save",
    response_model=MockInterviewSaveResponse,
    summary="모의면접 결과 저장",
    description="결과 저장 버튼 동작으로 세션 meta에 saved 플래그를 기록합니다.",
    response_description="저장 결과",
    responses={404: {"description": "세션을 찾을 수 없음"}},
)
def save_mock_interview_result_endpoint(
    session_id: UUID,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> MockInterviewSaveResponse:
    try:
        return save_mock_interview_result(db=db, user_id=user_id, session_id=session_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

