from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import CurrentUserId
from app.core.errors import NotFoundError
from app.db.session import get_db
from app.schemas.deep_interview import (
    DeepInterviewAnswerRequest,
    DeepInterviewAnswerResponse,
    DeepInterviewGuideRequest,
    DeepInterviewGuideResponse,
    DeepInterviewSessionResponse,
    DeepInterviewStartRequest,
    DeepInterviewStartResponse,
    InsightDocResponse,
)
from app.services.deep_interview_service import (
    generate_deep_interview_guide,
    get_deep_interview_insight_doc,
    get_deep_interview_session,
    start_deep_interview,
    submit_deep_interview_answer,
)

router = APIRouter(prefix="/deep-interview", tags=["심층인터뷰"])
insight_router = APIRouter(prefix="/v1/deep-interview", tags=["심층인터뷰"])


@router.post(
    "/start",
    response_model=DeepInterviewStartResponse,
    summary="심층 인터뷰 시작",
    description=(
        "프로젝트 기반 심층 인터뷰 세션을 만들고 첫 질문을 반환합니다. "
        "질문 생성 시 프로젝트에 귀속된 모든 포트폴리오 텍스트/메타를 "
        "프롬프트 컨텍스트로 사용합니다."
    ),
    response_description="세션 생성 결과와 첫 질문",
    responses={404: {"description": "프로젝트를 찾을 수 없음"}},
)
def start_deep_interview_endpoint(
    payload: DeepInterviewStartRequest,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> DeepInterviewStartResponse:
    try:
        return start_deep_interview(db=db, user_id=user_id, payload=payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/answer",
    response_model=DeepInterviewAnswerResponse,
    summary="심층 인터뷰 답변 제출",
    description="답변을 저장하고 다음 질문(또는 완료)을 반환합니다.",
    response_description="다음 질문 또는 완료 상태",
    responses={404: {"description": "세션을 찾을 수 없음"}},
)
def answer_deep_interview_endpoint(
    payload: DeepInterviewAnswerRequest,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> DeepInterviewAnswerResponse:
    try:
        return submit_deep_interview_answer(
            db=db,
            user_id=user_id,
            session_id=payload.sessionId,
            question_id=payload.questionId,
            answer=payload.answer,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/session/{session_id}",
    response_model=DeepInterviewSessionResponse,
    summary="심층 인터뷰 세션 조회",
    description="중단된 심층 인터뷰 세션의 현재 질문 위치를 조회합니다.",
    response_description="세션 현재 진행 상태",
    responses={404: {"description": "세션을 찾을 수 없음"}},
)
def get_deep_interview_session_endpoint(
    session_id: UUID,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> DeepInterviewSessionResponse:
    try:
        return get_deep_interview_session(db=db, user_id=user_id, session_id=session_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/generate-guide",
    response_model=DeepInterviewGuideResponse,
    summary="심층 인터뷰 개선 가이드 생성",
    description="심층 인터뷰 답변을 기반으로 개선 가이드를 생성합니다.",
    response_description="개선 가이드 섹션",
    responses={404: {"description": "세션을 찾을 수 없음"}},
)
def generate_guide_endpoint(
    payload: DeepInterviewGuideRequest,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> DeepInterviewGuideResponse:
    try:
        return generate_deep_interview_guide(
            db=db,
            user_id=user_id,
            session_id=payload.sessionId,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@insight_router.get(
    "/{session_id}/insight-doc",
    response_model=InsightDocResponse,
    summary="심층 인터뷰 인사이트 문서 조회",
    description="심층 인터뷰 답변을 요약해 강점/보완점/근거/체크리스트 문서를 반환합니다.",
    response_description="심층 인터뷰 인사이트 문서",
    responses={404: {"description": "세션을 찾을 수 없음"}},
)
def get_insight_doc_endpoint(
    session_id: UUID,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> InsightDocResponse:
    try:
        return get_deep_interview_insight_doc(db=db, user_id=user_id, session_id=session_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
