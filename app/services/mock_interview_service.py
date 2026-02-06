import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.db.repositories.project_repository import get_project_by_id
from app.db.repositories.session_repository import (
    create_session,
    create_turn,
    get_next_turn_index,
    get_session_by_id,
    list_turns_by_session,
    update_session,
)
from app.schemas.mock_interview import (
    MockFinding,
    MockInterviewAnswerResponse,
    MockInterviewQuestion,
    MockInterviewResultResponse,
    MockInterviewSaveResponse,
    MockInterviewStartRequest,
    MockInterviewStartResponse,
    MockOverall,
    MockQuestionResult,
    MockScoreItem,
    MockSessionInfo,
)
from app.schemas.session import SessionRole

QUESTION_BANK = [
    {
        "prompt": "자기소개를 해주세요.",
        "intent": "지원자의 핵심 역량과 회사 적합성을 빠르게 파악하기 위한 질문입니다.",
        "modelAnswer": "예시 구조: 한줄 소개 → 대표 성과 → 지원 동기 연결",
    },
    {
        "prompt": "가장 도전적이었던 프로젝트는 무엇이었나요?",
        "intent": "문제 해결 능력과 회복탄력성을 보기 위한 질문입니다.",
        "modelAnswer": "예시 구조: 상황/문제 → 내 역할 → 선택 근거 → 결과(수치)",
    },
    {
        "prompt": "협업 중 갈등을 해결한 경험이 있나요?",
        "intent": "커뮤니케이션과 조율 역량을 평가하기 위한 질문입니다.",
        "modelAnswer": "예시 구조: 갈등 원인 → 조율 방식 → 합의 결과 → 재발 방지",
    },
    {
        "prompt": "이 직무에 필요한 역량을 어떻게 준비했나요?",
        "intent": "직무 이해도와 자기주도 학습을 보기 위한 질문입니다.",
        "modelAnswer": "예시 구조: 요구 역량 정의 → 준비 방법 → 실제 적용 사례",
    },
    {
        "prompt": "최근 실패 경험과 배운 점을 말해주세요.",
        "intent": "성장 관점과 피드백 수용 태도를 보기 위한 질문입니다.",
        "modelAnswer": "예시 구조: 실패 맥락 → 원인 분석 → 개선 행동 → 이후 변화",
    },
]


def _question_for(index: int) -> dict[str, str]:
    base = QUESTION_BANK[(index - 1) % len(QUESTION_BANK)]
    return {
        "questionId": f"q_{index}",
        "prompt": base["prompt"],
        "intent": base["intent"],
        "modelAnswer": base["modelAnswer"],
    }


def _score_answer(answer: str) -> tuple[float, str]:
    score = 6.0
    text = answer.strip()
    if len(text) >= 80:
        score += 1.0
    if len(text) >= 150:
        score += 0.8
    if any(keyword in text for keyword in ["상황", "문제", "해결", "결과"]):
        score += 0.8
    if any(ch.isdigit() for ch in text):
        score += 0.7
    if any(filler in text for filler in ["어..", "그냥", "음.."]):
        score -= 0.8
    score = max(1.0, min(10.0, round(score, 1)))

    feedback = "핵심은 좋습니다. 근거와 결과 수치를 한 문장 더 보강하세요."
    if score >= 8.5:
        feedback = "구조가 안정적입니다. 선택 근거와 성과 연결이 명확합니다."
    elif score <= 6.0:
        feedback = "답변이 다소 짧습니다. 상황-행동-결과 구조로 다시 정리해보세요."
    return score, feedback


def _build_result_json(
    session,
    question_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    if question_rows:
        avg_score = round(sum(float(row["score"]) for row in question_rows) / len(question_rows), 1)
    else:
        avg_score = 0.0

    overall_score = int(round(avg_score * 10))
    key_findings = [
        {
            "code": "STRUCTURE_WEAK",
            "title": "답변 구조 점검",
            "detail": "결론→근거→결과 순서로 말하면 설득력이 높아집니다.",
        },
        {
            "code": "METRIC_MISSING",
            "title": "성과 수치 보강",
            "detail": "가능하면 개선 전후 지표를 함께 제시하세요.",
        },
        {
            "code": "QUESTION_FIT",
            "title": "질문 의도 적합성",
            "detail": "질문 의도를 한 문장으로 재정의하고 답하면 정확도가 올라갑니다.",
        },
    ]
    return {
        "sessionInfo": {
            "sessionId": str(session.id),
            "projectId": str(session.project_id),
            "title": "모의면접 결과",
            "startedAt": session.started_at.isoformat() if session.started_at else None,
            "durationSec": session.duration_sec,
        },
            "overall": {
                "score": overall_score,
                "subScores": [
                    {
                        "key": "habit",
                        "label": "습관",
                        "percent": max(10, min(100, overall_score - 8)),
                    },
                    {
                        "key": "improvement",
                        "label": "보완점",
                        "percent": max(10, min(100, overall_score - 22)),
                    },
                    {
                        "key": "confidence",
                        "label": "자신감",
                        "percent": max(10, min(100, overall_score + 5)),
                    },
                    {
                        "key": "vocab",
                        "label": "어휘력",
                        "percent": max(10, min(100, overall_score - 4)),
                    },
                ],
            },
        "keyFindings": key_findings,
        "questions": question_rows,
    }


def start_mock_interview(
    db: Session,
    user_id: int,
    project_id: uuid.UUID,
    payload: MockInterviewStartRequest,
) -> MockInterviewStartResponse:
    project = get_project_by_id(db=db, project_id=project_id, user_id=user_id)
    if project is None:
        raise NotFoundError("Project not found")

    session = create_session(
        db=db,
        project_id=project_id,
        user_id=user_id,
        session_type="MOCK_INTERVIEW",
        total_items=payload.questionCount,
        meta={"mode": payload.mode, "saved": False},
    )

    first = _question_for(1)
    create_turn(
        db=db,
        session=session,
        role=SessionRole.AI.value,
        speaker="면접관",
        prompt=first["prompt"],
        user_answer=None,
        message=first["prompt"],
        intent=first["intent"],
        feedback=None,
        score=None,
        score_delta=None,
        meta={"questionId": first["questionId"], "modelAnswer": first["modelAnswer"]},
        turn_index=1,
    )
    session.current_index = 1
    update_session(db=db, session=session)
    return MockInterviewStartResponse(
        sessionId=session.id,
        totalQuestions=payload.questionCount,
        currentIndex=1,
        firstQuestion=MockInterviewQuestion(
            questionId=first["questionId"],
            prompt=first["prompt"],
            prepSeconds=30,
            answerSeconds=120,
        ),
    )


def answer_mock_interview(
    db: Session,
    user_id: int,
    session_id: uuid.UUID,
    question_id: str,
    answer: str,
) -> MockInterviewAnswerResponse:
    session = get_session_by_id(db=db, session_id=session_id, user_id=user_id)
    if session is None or session.session_type != "MOCK_INTERVIEW":
        raise NotFoundError("Mock interview session not found")

    current = session.current_index
    expected = _question_for(current)
    if question_id != expected["questionId"]:
        raise ValueError(f"Expected questionId={expected['questionId']}")

    score, feedback = _score_answer(answer)
    turn_index = get_next_turn_index(db=db, session_id=session.id)
    create_turn(
        db=db,
        session=session,
        role=SessionRole.USER.value,
        speaker="지원자",
        prompt=expected["prompt"],
        user_answer=answer,
        message=answer,
        intent=expected["intent"],
        feedback=feedback,
        score=score,
        score_delta=None,
        meta={"questionId": question_id, "modelAnswer": expected["modelAnswer"]},
        turn_index=turn_index,
    )

    result_json = dict(session.result_json or {})
    question_rows = list(result_json.get("questions", []))
    question_rows.append(
        {
            "index": current,
            "questionId": question_id,
            "prompt": expected["prompt"],
            "intent": expected["intent"],
            "userAnswer": answer,
            "feedback": feedback,
            "modelAnswer": expected["modelAnswer"],
            "score": score,
        }
    )
    result_json["questions"] = question_rows
    session.result_json = result_json

    total = session.total_items or 8
    if current < total:
        next_index = current + 1
        next_question = _question_for(next_index)
        create_turn(
            db=db,
            session=session,
            role=SessionRole.AI.value,
            speaker="면접관",
            prompt=next_question["prompt"],
            user_answer=None,
            message=next_question["prompt"],
            intent=next_question["intent"],
            feedback=None,
            score=None,
            score_delta=None,
            meta={
                "questionId": next_question["questionId"],
                "modelAnswer": next_question["modelAnswer"],
            },
            turn_index=turn_index + 1,
        )
        session.current_index = next_index
        update_session(db=db, session=session)
        return MockInterviewAnswerResponse(
            nextQuestion=MockInterviewQuestion(
                questionId=next_question["questionId"],
                prompt=next_question["prompt"],
                prepSeconds=30,
                answerSeconds=120,
            ),
            progress={"current": next_index, "total": total},
            completed=False,
        )

    session.status = "COMPLETED"
    session.ended_at = datetime.now(tz=UTC)
    if session.started_at:
        session.duration_sec = int((session.ended_at - session.started_at).total_seconds())
    session.result_json = _build_result_json(session=session, question_rows=question_rows)
    update_session(db=db, session=session)
    return MockInterviewAnswerResponse(
        completed=True,
        resultUrl=f"/v1/mock-interviews/sessions/{session.id}/result",
    )


def _parse_result(session) -> MockInterviewResultResponse:
    payload = session.result_json or {}
    info = payload.get("sessionInfo", {})
    overall_payload = payload.get("overall", {})
    findings_payload = payload.get("keyFindings", [])
    questions_payload = payload.get("questions", [])
    return MockInterviewResultResponse(
        sessionInfo=MockSessionInfo(
            sessionId=session.id,
            projectId=session.project_id,
            title=str(info.get("title", "모의면접 결과")),
            startedAt=session.started_at,
            durationSec=session.duration_sec,
        ),
        overall=MockOverall(
            score=int(overall_payload.get("score", 0)),
            subScores=[
                MockScoreItem(
                    key=str(item.get("key")),
                    label=str(item.get("label")),
                    percent=int(item.get("percent", 0)),
                )
                for item in overall_payload.get("subScores", [])
            ],
        ),
        keyFindings=[
            MockFinding(
                code=str(item.get("code")),
                title=str(item.get("title")),
                detail=str(item.get("detail")),
            )
            for item in findings_payload
        ],
        questions=[
            MockQuestionResult(
                index=int(item.get("index", 0)),
                questionId=str(item.get("questionId")),
                prompt=str(item.get("prompt")),
                intent=str(item.get("intent")),
                userAnswer=str(item.get("userAnswer")),
                feedback=str(item.get("feedback")),
                modelAnswer=str(item.get("modelAnswer")),
                score=float(item.get("score", 0)),
            )
            for item in questions_payload
        ],
    )


def get_mock_interview_result(
    db: Session,
    user_id: int,
    session_id: uuid.UUID,
) -> MockInterviewResultResponse:
    session = get_session_by_id(db=db, session_id=session_id, user_id=user_id)
    if session is None or session.session_type != "MOCK_INTERVIEW":
        raise NotFoundError("Mock interview session not found")
    if not session.result_json:
        turns = list_turns_by_session(db=db, session_id=session.id, desc=False)
        rows: list[dict[str, Any]] = []
        for turn in turns:
            if turn.role != SessionRole.USER.value or not turn.user_answer:
                continue
            meta = turn.meta or {}
            rows.append(
                {
                    "index": len(rows) + 1,
                    "questionId": meta.get("questionId", f"q_{len(rows)+1}"),
                    "prompt": turn.prompt or "",
                    "intent": turn.intent or "",
                    "userAnswer": turn.user_answer,
                    "feedback": turn.feedback or "",
                    "modelAnswer": meta.get("modelAnswer", ""),
                    "score": float(turn.score) if turn.score is not None else 0.0,
                }
            )
        session.result_json = _build_result_json(session=session, question_rows=rows)
        update_session(db=db, session=session)
    return _parse_result(session)


def save_mock_interview_result(
    db: Session,
    user_id: int,
    session_id: uuid.UUID,
) -> MockInterviewSaveResponse:
    session = get_session_by_id(db=db, session_id=session_id, user_id=user_id)
    if session is None or session.session_type != "MOCK_INTERVIEW":
        raise NotFoundError("Mock interview session not found")

    meta = dict(session.meta or {})
    meta["saved"] = True
    meta["savedAt"] = datetime.now(tz=UTC).isoformat()
    session.meta = meta
    update_session(db=db, session=session)
    saved_at = datetime.fromisoformat(meta["savedAt"])
    return MockInterviewSaveResponse(sessionId=session.id, saved=True, savedAt=saved_at)
