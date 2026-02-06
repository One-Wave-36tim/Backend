import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import NotFoundError
from app.db.repositories.job_posting_repository import get_latest_job_posting_by_project
from app.db.repositories.portfolio_repository import get_portfolios_by_user
from app.db.repositories.project_portfolio_repository import list_project_portfolios
from app.db.repositories.project_repository import get_project_by_id
from app.db.repositories.session_repository import (
    create_session,
    create_turn,
    get_next_turn_index,
    get_session_by_id,
    list_turns_by_session,
    update_session,
)
from app.schemas.deep_interview import (
    DeepInterviewAnswerResponse,
    DeepInterviewGuideResponse,
    DeepInterviewProgress,
    DeepInterviewQuestion,
    DeepInterviewSessionResponse,
    DeepInterviewStartRequest,
    DeepInterviewStartResponse,
    GuideSection,
    InsightDocResponse,
)
from app.schemas.session import SessionRole
from app.services.gemini_client import GeminiClient

MAX_QUESTIONS = 6

DEEP_QUESTION_SYSTEM_PROMPT = """당신은 채용 코치이며,
사용자의 프로젝트 이해도를 검증하는 심층 인터뷰어다.
목표는 자소서 작성에 필요한 '근거 데이터'를 모으는 것이다.
절대 답안을 대신 작성하지 말고 질문만 만들어라.

반드시 JSON으로만 응답:
{
  "question": "질문 1개",
  "intent": "질문 의도",
  "should_stop": false,
  "coverage": ["기술선택","대안비교","확장성","협업근거","정량성과"]
}
"""

DEEP_GUIDE_SYSTEM_PROMPT = """너는 자소서 코치다.
사용자 답변 기반으로 개선 가이드를 만든다.
중요: 문장 대필 금지. 방향/점검항목만 제공.

JSON 형식:
{
  "guideSections": [
    {"type":"TECH_DEPTH","title":"...","items":["..."]},
    {"type":"IMPACT","title":"...","items":["..."]}
  ]
}
"""


def _fallback_question(index: int) -> DeepInterviewQuestion:
    templates = [
        "이 프로젝트에서 왜 SQL을 선택했고, NoSQL을 배제한 근거는 무엇인가요?",
        "랭체인/랭그래프를 선택했다면 ADK 같은 대안과 비교 근거는 무엇인가요?",
        "대규모 사용자/트래픽을 가정했을 때 병목 지점과 대응 전략은 무엇인가요?",
        "기능 우선순위 결정 시 비즈니스 영향과 기술 리스크를 어떻게 비교했나요?",
        "협업(기획/디자인/백엔드)에서 갈등을 어떤 데이터와 논리로 조율했나요?",
        "이 프로젝트 경험을 자소서에 넣을 때 핵심 수치 2개는 무엇인가요?",
    ]
    safe = max(1, min(index, len(templates)))
    return DeepInterviewQuestion(questionId=f"q_{safe}", prompt=templates[safe - 1])


def _collect_answers(turns: list[Any]) -> list[str]:
    return [
        (turn.user_answer or "").strip()
        for turn in turns
        if turn.role == SessionRole.USER.value and turn.user_answer
    ]


def _build_context(
    db: Session,
    user_id: int,
    project_id: uuid.UUID,
    turns: list[Any],
) -> str:
    project = get_project_by_id(db=db, project_id=project_id, user_id=user_id)
    posting = get_latest_job_posting_by_project(db=db, project_id=project_id, user_id=user_id)
    links = list_project_portfolios(db=db, project_id=project_id, user_id=user_id)
    portfolios = get_portfolios_by_user(
        db=db,
        user_id=user_id,
        limit=20,
        offset=0,
        project_id=project_id,
    )

    lines = [
        f"지원 회사: {project.company_name if project else '미지정'}",
        f"지원 직무: {project.role_title if project else '미지정'}",
        f"공고 텍스트 일부: {(posting.text[:500] if posting and posting.text else '없음')}",
        "연결된 포트폴리오 이력:",
    ]
    for link, portfolio_item in links[:5]:
        lines.append(
            f"- {portfolio_item.title} / role={link.role_type} / rep={link.is_representative}"
        )
    lines.append("프로젝트 귀속 포트폴리오:")
    for portfolio in portfolios:
        text = (portfolio.extracted_text or "").strip()
        text_preview = text[:1200] if text else "(크롤링 텍스트 없음)"
        lines.append(
            "- "
            f"type={portfolio.source_type}, rep={portfolio.is_representative}, "
            f"url={portfolio.source_url or ''}, "
            f"description={((portfolio.meta or {}).get('representativeDescription') or '')}, "
            f"text={text_preview}"
        )
    lines.append("최근 대화:")
    for turn in turns[-12:]:
        if turn.role == SessionRole.AI.value:
            lines.append(f"Q: {turn.prompt or turn.message or ''}")
        elif turn.role == SessionRole.USER.value:
            lines.append(f"A: {turn.user_answer or turn.message or ''}")
    return "\n".join(lines)


def _generate_question_with_ai(
    context: str,
    asked_count: int,
) -> dict[str, Any]:
    gemini = GeminiClient()
    return gemini.generate_json(
        system_prompt=DEEP_QUESTION_SYSTEM_PROMPT,
        user_prompt=(
            f"{context}\n\n"
            f"현재 질문 수: {asked_count}\n"
            "사용자가 프로젝트를 깊게 이해했는지 검증할 다음 질문 1개를 생성해라."
        ),
    )


def _build_rule_guide(answers: list[str]) -> list[GuideSection]:
    has_numeric = any(any(ch.isdigit() for ch in answer) for answer in answers)
    return [
        GuideSection(
            type="TECH_DEPTH",
            title="기술 깊이 보강 포인트",
            items=[
                "기술 선택 이유를 대안(예: SQL vs NoSQL)과 함께 비교해 설명하기",
                "아키텍처 선택의 트레이드오프를 비용/운영 관점으로 명시하기",
            ],
        ),
        GuideSection(
            type="IMPACT",
            title="성과/영향 보강 포인트",
            items=(
                [
                    "성과 수치를 전/후 비교로 명시하기",
                    "역할 분리(내 기여 vs 팀 기여) 한 문장 추가하기",
                ]
                if has_numeric
                else [
                    "정량 지표(처리량, 오류율, 응답시간)를 1개 이상 넣기",
                    "성과 수치가 없다면 로그/관측 근거라도 제시하기",
                ]
            ),
        ),
    ]


def _refine_guide_with_ai(
    sections: list[GuideSection],
    context: str,
) -> list[GuideSection]:
    settings = get_settings()
    if not settings.gemini_api_key:
        return sections
    try:
        gemini = GeminiClient()
        payload = gemini.generate_json(
            system_prompt=DEEP_GUIDE_SYSTEM_PROMPT,
            user_prompt=f"{context}\n\n현재 초안: { [s.model_dump() for s in sections] }",
        )
        rows = payload.get("guideSections")
        if not isinstance(rows, list) or not rows:
            return sections
        return [
            GuideSection(
                type=str(row.get("type", "GENERAL")),
                title=str(row.get("title", "개선 포인트")),
                items=[str(item) for item in row.get("items", [])],
            )
            for row in rows
        ]
    except Exception:
        return sections


def _build_insight(answers: list[str]) -> InsightDocResponse:
    if not answers:
        return InsightDocResponse(
            summary="심층 답변 데이터가 부족합니다.",
            strengthPoints=[],
            weakPoints=["답변 수 부족"],
            evidenceQuotes=[],
            actionChecklist=["심층 인터뷰를 3문항 이상 진행하세요."],
        )
    strength: list[str] = []
    weak: list[str] = []
    if any("근거" in answer or "왜" in answer for answer in answers):
        strength.append("의사결정 근거를 설명하려는 시도가 보입니다.")
    else:
        weak.append("의사결정 근거가 부족합니다.")
    if any(any(ch.isdigit() for ch in answer) for answer in answers):
        strength.append("정량 지표를 일부 포함하고 있습니다.")
    else:
        weak.append("정량 성과 표현이 부족합니다.")
    if any("협업" in answer or "팀" in answer for answer in answers):
        strength.append("협업 맥락 설명이 포함되어 있습니다.")
    else:
        weak.append("협업/조율 맥락이 부족합니다.")
    return InsightDocResponse(
        summary=f"총 {len(answers)}개 답변 기반으로 프로젝트 이해도를 점검했습니다.",
        strengthPoints=strength or ["문제 해결 의지는 확인됩니다."],
        weakPoints=weak,
        evidenceQuotes=[answer[:120] for answer in answers[:3]],
        actionChecklist=[
            "기술 선택 이유를 대안 비교로 설명하기",
            "성과 수치 최소 1개 포함하기",
            "내 역할과 팀 역할 분리하기",
        ],
    )


def start_deep_interview(
    db: Session,
    user_id: int,
    payload: DeepInterviewStartRequest,
) -> DeepInterviewStartResponse:
    project = get_project_by_id(db=db, project_id=payload.projectId, user_id=user_id)
    if project is None:
        raise NotFoundError("Project not found")

    session = create_session(
        db=db,
        project_id=payload.projectId,
        user_id=user_id,
        session_type="DEEP_INTERVIEW",
        total_items=MAX_QUESTIONS,
        meta={
            "askedCount": 1,
            "coverage": [],
        },
    )

    question = _fallback_question(1)
    intent = "프로젝트 핵심 의사결정 검증"
    settings = get_settings()
    if settings.gemini_api_key:
        try:
            generated = _generate_question_with_ai(
                context=_build_context(
                    db=db,
                    user_id=user_id,
                    project_id=payload.projectId,
                    turns=[],
                ),
                asked_count=0,
            )
            question = DeepInterviewQuestion(
                questionId="q_1",
                prompt=str(generated.get("question", question.prompt)),
            )
            intent = str(generated.get("intent") or intent)
            meta = dict(session.meta or {})
            coverage = generated.get("coverage")
            if isinstance(coverage, list):
                meta["coverage"] = [str(item) for item in coverage]
            session.meta = meta
            update_session(db=db, session=session)
        except Exception as exc:
            meta = dict(session.meta or {})
            meta["questionGeneration"] = "fallback"
            meta["lastAiError"] = str(exc)[:500]
            session.meta = meta
            update_session(db=db, session=session)

    create_turn(
        db=db,
        session=session,
        role=SessionRole.AI.value,
        speaker="AI 인터뷰어",
        prompt=question.prompt,
        user_answer=None,
        message=question.prompt,
        intent=intent,
        feedback=None,
        score=None,
        score_delta=None,
        meta={"questionId": question.questionId},
        turn_index=1,
    )
    return DeepInterviewStartResponse(
        sessionId=session.id,
        totalQuestions=MAX_QUESTIONS,
        currentIndex=1,
        firstQuestion=question,
    )


def submit_deep_interview_answer(
    db: Session,
    user_id: int,
    session_id: uuid.UUID,
    question_id: str,
    answer: str,
) -> DeepInterviewAnswerResponse:
    session = get_session_by_id(db=db, session_id=session_id, user_id=user_id)
    if session is None or session.session_type != "DEEP_INTERVIEW":
        raise NotFoundError("Deep interview session not found")

    current = session.current_index
    turn_index = get_next_turn_index(db=db, session_id=session.id)
    create_turn(
        db=db,
        session=session,
        role=SessionRole.USER.value,
        speaker="사용자",
        prompt=f"questionId={question_id}",
        user_answer=answer,
        message=answer,
        intent=None,
        feedback=None,
        score=None,
        score_delta=None,
        meta={"questionId": question_id},
        turn_index=turn_index,
    )

    max_questions = session.total_items or MAX_QUESTIONS
    should_stop = current >= max_questions
    next_question = _fallback_question(current + 1)
    next_intent = "답변 심화 검증"
    coverage = list((session.meta or {}).get("coverage") or [])

    turns = list_turns_by_session(db=db, session_id=session.id, desc=False)
    settings = get_settings()
    if settings.gemini_api_key and not should_stop:
        try:
            generated = _generate_question_with_ai(
                context=_build_context(
                    db=db,
                    user_id=user_id,
                    project_id=session.project_id,
                    turns=turns,
                ),
                asked_count=current,
            )
            next_question = DeepInterviewQuestion(
                questionId=f"q_{current + 1}",
                prompt=str(generated.get("question", next_question.prompt)),
            )
            next_intent = str(generated.get("intent") or next_intent)
            should_stop = bool(generated.get("should_stop")) or should_stop
            if isinstance(generated.get("coverage"), list):
                coverage = [str(item) for item in generated.get("coverage")]
        except Exception as exc:
            meta = dict(session.meta or {})
            meta["questionGeneration"] = "fallback"
            meta["lastAiError"] = str(exc)[:500]
            session.meta = meta
            update_session(db=db, session=session)

    if not should_stop:
        next_index = current + 1
        create_turn(
            db=db,
            session=session,
            role=SessionRole.AI.value,
            speaker="AI 인터뷰어",
            prompt=next_question.prompt,
            user_answer=None,
            message=next_question.prompt,
            intent=next_intent,
            feedback=None,
            score=None,
            score_delta=None,
            meta={"questionId": next_question.questionId},
            turn_index=turn_index + 1,
        )
        session.current_index = next_index
        meta = dict(session.meta or {})
        meta["askedCount"] = next_index
        meta["coverage"] = coverage
        session.meta = meta
        update_session(db=db, session=session)
        return DeepInterviewAnswerResponse(
            nextQuestion=next_question,
            progress=DeepInterviewProgress(current=next_index, total=max_questions),
            completed=False,
        )

    answers = _collect_answers(turns)
    session.status = "COMPLETED"
    session.ended_at = datetime.now(tz=UTC)
    if session.started_at:
        session.duration_sec = int((session.ended_at - session.started_at).total_seconds())
    session.result_json = {
        "answerCount": len(answers),
        "summary": f"총 {len(answers)}개 문항을 완료했습니다.",
        "coverage": coverage,
    }
    update_session(db=db, session=session)
    return DeepInterviewAnswerResponse(completed=True, nextStep="IMPROVEMENT_GUIDE")


def get_deep_interview_session(
    db: Session,
    user_id: int,
    session_id: uuid.UUID,
) -> DeepInterviewSessionResponse:
    session = get_session_by_id(db=db, session_id=session_id, user_id=user_id)
    if session is None or session.session_type != "DEEP_INTERVIEW":
        raise NotFoundError("Deep interview session not found")

    current_question: DeepInterviewQuestion | None = None
    if session.status != "COMPLETED":
        current_question = _fallback_question(session.current_index)
    return DeepInterviewSessionResponse(
        sessionId=session.id,
        currentIndex=session.current_index,
        totalQuestions=session.total_items or MAX_QUESTIONS,
        currentQuestion=current_question,
    )


def generate_deep_interview_guide(
    db: Session,
    user_id: int,
    session_id: uuid.UUID,
) -> DeepInterviewGuideResponse:
    session = get_session_by_id(db=db, session_id=session_id, user_id=user_id)
    if session is None or session.session_type != "DEEP_INTERVIEW":
        raise NotFoundError("Deep interview session not found")

    turns = list_turns_by_session(db=db, session_id=session.id, desc=False)
    answers = _collect_answers(turns)
    context = _build_context(db=db, user_id=user_id, project_id=session.project_id, turns=turns)
    guide_sections = _build_rule_guide(answers)
    guide_sections = _refine_guide_with_ai(guide_sections, context=context)

    result_json = dict(session.result_json or {})
    result_json["guideSections"] = [section.model_dump() for section in guide_sections]
    session.result_json = result_json
    update_session(db=db, session=session)
    return DeepInterviewGuideResponse(guideSections=guide_sections)


def get_deep_interview_insight_doc(
    db: Session,
    user_id: int,
    session_id: uuid.UUID,
) -> InsightDocResponse:
    session = get_session_by_id(db=db, session_id=session_id, user_id=user_id)
    if session is None or session.session_type != "DEEP_INTERVIEW":
        raise NotFoundError("Deep interview session not found")

    turns = list_turns_by_session(db=db, session_id=session.id, desc=False)
    answers = _collect_answers(turns)
    insight = _build_insight(answers)
    settings = get_settings()
    if settings.gemini_api_key:
        try:
            gemini = GeminiClient()
            context = _build_context(
                db=db,
                user_id=user_id,
                project_id=session.project_id,
                turns=turns,
            )
            payload = gemini.generate_json(
                system_prompt=(
                    "너는 자소서 코치다. 대필 없이 분석문서만 작성한다. "
                    "JSON 키는 summary/strengthPoints/weakPoints/"
                    "evidenceQuotes/actionChecklist 고정."
                ),
                user_prompt=f"{context}\n\n현재 초안: {insight.model_dump()}",
            )
            insight = InsightDocResponse(
                summary=str(payload.get("summary", insight.summary)),
                strengthPoints=[
                    str(x) for x in payload.get("strengthPoints", insight.strengthPoints)
                ],
                weakPoints=[str(x) for x in payload.get("weakPoints", insight.weakPoints)],
                evidenceQuotes=[
                    str(x) for x in payload.get("evidenceQuotes", insight.evidenceQuotes)
                ],
                actionChecklist=[
                    str(x) for x in payload.get("actionChecklist", insight.actionChecklist)
                ],
            )
        except Exception:
            pass

    result_json = dict(session.result_json or {})
    result_json["insightDoc"] = insight.model_dump()
    session.result_json = result_json
    update_session(db=db, session=session)
    return insight
