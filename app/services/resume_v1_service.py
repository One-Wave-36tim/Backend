import uuid

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.db.repositories.resume_repository import (
    count_completed_paragraphs,
    count_total_paragraphs,
    create_paragraph,
    create_resume,
    complete_paragraph,
    get_paragraph_by_id,
    get_latest_resume_by_project,
    get_resume_by_id,
    list_paragraphs_by_resume,
    update_resume_status,
    update_paragraph_text,
)
from app.schemas.resume_v1 import (
    ResumeCoachAnswer,
    ResumeCoachAskRequest,
    ResumeCoachAskResponse,
    ResumeDraftResponse,
    ResumeParagraphCompleteResponse,
    ResumeParagraphPatchResponse,
    ResumeParagraphResponse,
)

_DEFAULT_PARAGRAPHS: list[tuple[str, int]] = [
    ("지원 동기와 직무 적합성", 700),
    ("프로젝트 문제 해결 경험", 900),
    ("협업/소통 경험과 성과", 800),
]


def _to_paragraph_response(paragraph) -> ResumeParagraphResponse:
    return ResumeParagraphResponse(
        paragraphId=paragraph.id,
        title=paragraph.title,
        text=paragraph.text,
        charLimit=paragraph.char_limit,
        status=paragraph.status,
        sortOrder=paragraph.sort_order,
        updatedAt=paragraph.updated_at,
    )


def get_or_create_resume_draft(
    db: Session,
    user_id: int,
    project_id: uuid.UUID,
) -> ResumeDraftResponse:
    resume = get_latest_resume_by_project(db=db, project_id=project_id, user_id=user_id)
    if resume is None:
        resume = create_resume(db=db, project_id=project_id, user_id=user_id)

    paragraphs = list_paragraphs_by_resume(
        db=db,
        resume_id=resume.id,
        project_id=project_id,
        user_id=user_id,
    )
    if not paragraphs:
        for idx, (title, char_limit) in enumerate(_DEFAULT_PARAGRAPHS):
            create_paragraph(
                db=db,
                resume_id=resume.id,
                project_id=project_id,
                user_id=user_id,
                title=title,
                sort_order=idx + 1,
                char_limit=char_limit,
            )
        paragraphs = list_paragraphs_by_resume(
            db=db,
            resume_id=resume.id,
            project_id=project_id,
            user_id=user_id,
        )

    completed = count_completed_paragraphs(db=db, resume_id=resume.id)
    total = count_total_paragraphs(db=db, resume_id=resume.id)
    return ResumeDraftResponse(
        projectId=project_id,
        resumeId=resume.id,
        title=resume.title,
        status=resume.status,
        completedParagraphs=completed,
        totalParagraphs=total,
        paragraphs=[_to_paragraph_response(paragraph) for paragraph in paragraphs],
    )


def list_resume_paragraphs(
    db: Session,
    user_id: int,
    project_id: uuid.UUID,
    resume_id: uuid.UUID,
) -> list[ResumeParagraphResponse]:
    resume = get_resume_by_id(db=db, resume_id=resume_id, project_id=project_id, user_id=user_id)
    if resume is None:
        raise NotFoundError("Resume not found")
    paragraphs = list_paragraphs_by_resume(
        db=db,
        resume_id=resume_id,
        project_id=project_id,
        user_id=user_id,
    )
    return [_to_paragraph_response(paragraph) for paragraph in paragraphs]


def get_resume_paragraph(
    db: Session,
    user_id: int,
    project_id: uuid.UUID,
    resume_id: uuid.UUID,
    paragraph_id: uuid.UUID,
) -> ResumeParagraphResponse:
    resume = get_resume_by_id(db=db, resume_id=resume_id, project_id=project_id, user_id=user_id)
    if resume is None:
        raise NotFoundError("Resume not found")
    paragraph = get_paragraph_by_id(
        db=db,
        paragraph_id=paragraph_id,
        resume_id=resume_id,
        project_id=project_id,
        user_id=user_id,
    )
    if paragraph is None:
        raise NotFoundError("Paragraph not found")
    return _to_paragraph_response(paragraph)


def patch_resume_paragraph(
    db: Session,
    user_id: int,
    project_id: uuid.UUID,
    resume_id: uuid.UUID,
    paragraph_id: uuid.UUID,
    text: str,
) -> ResumeParagraphPatchResponse:
    resume = get_resume_by_id(db=db, resume_id=resume_id, project_id=project_id, user_id=user_id)
    if resume is None:
        raise NotFoundError("Resume not found")
    paragraph = get_paragraph_by_id(
        db=db,
        paragraph_id=paragraph_id,
        resume_id=resume_id,
        project_id=project_id,
        user_id=user_id,
    )
    if paragraph is None:
        raise NotFoundError("Paragraph not found")
    paragraph = update_paragraph_text(db=db, paragraph=paragraph, text=text)
    return ResumeParagraphPatchResponse(
        saved=True,
        updatedAt=paragraph.updated_at,
        charCount=len(paragraph.text),
    )


def complete_resume_paragraph_v1(
    db: Session,
    user_id: int,
    project_id: uuid.UUID,
    resume_id: uuid.UUID,
    paragraph_id: uuid.UUID,
) -> ResumeParagraphCompleteResponse:
    resume = get_resume_by_id(db=db, resume_id=resume_id, project_id=project_id, user_id=user_id)
    if resume is None:
        raise NotFoundError("Resume not found")
    paragraph = get_paragraph_by_id(
        db=db,
        paragraph_id=paragraph_id,
        resume_id=resume_id,
        project_id=project_id,
        user_id=user_id,
    )
    if paragraph is None:
        raise NotFoundError("Paragraph not found")
    paragraph = complete_paragraph(db=db, paragraph=paragraph)
    completed = count_completed_paragraphs(db=db, resume_id=resume.id)
    total = count_total_paragraphs(db=db, resume_id=resume.id)
    if total > 0 and completed >= total:
        update_resume_status(db=db, resume=resume, status="COMPLETED")
    return ResumeParagraphCompleteResponse(
        paragraphId=paragraph.id,
        status=paragraph.status,
        completedAt=paragraph.updated_at,
    )


def _build_coach_answer(question: str, paragraph_text: str) -> ResumeCoachAnswer:
    has_metric = any(ch.isdigit() for ch in paragraph_text)
    summary = (
        "추상 표현을 줄이고 상황-행동-결과를 나눠 근거를 붙이세요. "
        "질문 의도에 맞는 결과 지표를 넣으면 설득력이 올라갑니다."
    )
    checklist = [
        "내 역할 한 문장",
        "의사결정 근거 1개",
        "성과 수치 1개",
        "협업/커뮤니케이션 한 줄",
    ]
    if not has_metric:
        checklist.insert(0, "정량 수치(전/후 비교) 추가")
    follow_ups = [
        "당시 목표 지표(속도/오류율/전환율)는 무엇이었나요?",
        "본인이 직접 바꾼 설계나 코드 포인트는 무엇인가요?",
        "개선 전후를 비교할 수 있는 수치가 있나요?",
    ]
    if "추상" in question:
        follow_ups.insert(0, "어떤 문장이 가장 추상적이라고 느껴지나요?")
    return ResumeCoachAnswer(summary=summary, followUpQuestions=follow_ups, checklist=checklist)


def ask_resume_coach(
    payload: ResumeCoachAskRequest,
) -> ResumeCoachAskResponse:
    if not payload.policy.noGhostwriting:
        raise ValueError("noGhostwriting must be true")
    answer = _build_coach_answer(payload.userQuestion, payload.paragraphText)
    return ResumeCoachAskResponse(coachAnswer=answer)
