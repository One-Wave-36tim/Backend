from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import CurrentUserId
from app.core.errors import NotFoundError
from app.db.session import get_db
from app.schemas.resume_v1 import (
    ResumeCoachAskRequest,
    ResumeCoachAskResponse,
    ResumeParagraphCompleteResponse,
    ResumeParagraphPatchRequest,
    ResumeParagraphPatchResponse,
    ResumeParagraphResponse,
)
from app.services.resume_v1_service import (
    ask_resume_coach,
    complete_resume_paragraph_v1,
    get_resume_paragraph,
    patch_resume_paragraph,
)

router = APIRouter(prefix="/v1", tags=["자소서"])


@router.get(
    "/projects/{project_id}/resumes/{resume_id}/paragraphs/{paragraph_id}",
    response_model=ResumeParagraphResponse,
    summary="자소서 문단 조회",
    description="특정 자소서 문단의 현재 텍스트와 제한 글자 수를 조회합니다.",
    response_description="문단 데이터",
    responses={404: {"description": "이력서 또는 문단을 찾을 수 없음"}},
)
def get_resume_paragraph_endpoint(
    project_id: UUID,
    resume_id: UUID,
    paragraph_id: UUID,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> ResumeParagraphResponse:
    try:
        return get_resume_paragraph(
            db=db,
            user_id=user_id,
            project_id=project_id,
            resume_id=resume_id,
            paragraph_id=paragraph_id,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch(
    "/projects/{project_id}/resumes/{resume_id}/paragraphs/{paragraph_id}",
    response_model=ResumeParagraphPatchResponse,
    summary="자소서 문단 저장",
    description="자동저장 요청으로 문단 텍스트를 갱신합니다.",
    response_description="저장 결과",
    responses={404: {"description": "이력서 또는 문단을 찾을 수 없음"}},
)
def patch_resume_paragraph_endpoint(
    project_id: UUID,
    resume_id: UUID,
    paragraph_id: UUID,
    payload: ResumeParagraphPatchRequest,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> ResumeParagraphPatchResponse:
    try:
        return patch_resume_paragraph(
            db=db,
            user_id=user_id,
            project_id=project_id,
            resume_id=resume_id,
            paragraph_id=paragraph_id,
            text=payload.text,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/projects/{project_id}/resumes/{resume_id}/paragraphs/{paragraph_id}/complete",
    response_model=ResumeParagraphCompleteResponse,
    summary="자소서 문단 완료 처리",
    description="문단 작성 완료 상태로 전환합니다.",
    response_description="완료 처리 결과",
    responses={404: {"description": "이력서 또는 문단을 찾을 수 없음"}},
)
def complete_resume_paragraph_endpoint(
    project_id: UUID,
    resume_id: UUID,
    paragraph_id: UUID,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> ResumeParagraphCompleteResponse:
    try:
        return complete_resume_paragraph_v1(
            db=db,
            user_id=user_id,
            project_id=project_id,
            resume_id=resume_id,
            paragraph_id=paragraph_id,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/resume-coach/ask",
    response_model=ResumeCoachAskResponse,
    summary="자소서 코치 질문",
    description="문장 대필 없이 가이드/체크리스트/후속 질문만 제공합니다.",
    response_description="코치 가이드 응답",
    responses={400: {"description": "정책 위반(noGhostwriting=false)"}},
)
def ask_resume_coach_endpoint(payload: ResumeCoachAskRequest) -> ResumeCoachAskResponse:
    try:
        return ask_resume_coach(payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

