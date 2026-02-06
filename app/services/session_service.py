from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import NotFoundError
from app.db.entities.session_v2 import SessionTurn, UnifiedSession
from app.db.repositories.project_repository import get_project_by_id
from app.db.repositories.session_repository import (
    create_session,
    create_turn,
    get_next_turn_index,
    get_session_by_id,
    list_turns_by_session,
    update_session,
)
from app.schemas.session import (
    SessionAnalyzeResponse,
    SessionAppendTurnResponse,
    SessionDetailResponse,
    SessionResponse,
    SessionRole,
    SessionStartRequest,
    SessionStartResponse,
    SessionStatus,
    SessionTurnCreateRequest,
    SessionTurnResponse,
    SessionType,
)
from app.services.gemini_client import GeminiClient

SIM_SYSTEM_PROMPT = """당신은 지원자에게 어려운 직무 상황을 제시하는 시뮬레이터다.
한국어로 답하고 반드시 JSON으로만 응답한다.

응답 형식:
{
  "response": "사용자에게 보여줄 대사",
  "persona": "페르소나 이름",
  "intent": "질문의 의도",
  "feedback": "답변에 대한 짧은 피드백",
  "score_delta": {"logic": -2, "mental": +1, "responsibility": 0, "collaboration": +2}
}
"""

SIM_REPORT_PROMPT = """너는 채용 코치다.
대화 로그와 점수 요약을 바탕으로 결과 리포트를 JSON으로 작성해라.

응답 형식:
{
  "archetype": "문자열",
  "summary": "2~3문장 요약",
  "best_moment": "가장 좋았던 답변",
  "worst_moment": "개선이 필요한 답변",
  "resume_snippet": "자소서에 넣을 한 문장"
}
"""


def _to_session_response(session: UnifiedSession) -> SessionResponse:
    return SessionResponse(
        id=session.id,
        project_id=session.project_id,
        user_id=session.user_id,
        session_type=SessionType(session.session_type),
        status=SessionStatus(session.status),
        total_items=session.total_items,
        current_index=session.current_index,
        started_at=session.started_at,
        ended_at=session.ended_at,
        duration_sec=session.duration_sec,
        meta=session.meta,
        result_json=session.result_json,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


def _as_float(value: Decimal | float | int | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _to_turn_response(turn: SessionTurn) -> SessionTurnResponse:
    return SessionTurnResponse(
        id=turn.id,
        session_id=turn.session_id,
        project_id=turn.project_id,
        user_id=turn.user_id,
        turn_index=turn.turn_index,
        role=SessionRole(turn.role),
        speaker=turn.speaker,
        prompt=turn.prompt,
        user_answer=turn.user_answer,
        message=turn.message,
        intent=turn.intent,
        feedback=turn.feedback,
        score=_as_float(turn.score),
        score_delta=turn.score_delta,
        meta=turn.meta,
        created_at=turn.created_at,
        updated_at=turn.updated_at,
    )


def _build_job_sim_context(session: UnifiedSession, turns: list[SessionTurn]) -> str:
    role = (session.meta or {}).get("role") or "미지정"
    scenario = (session.meta or {}).get("scenario") or "미지정"
    lines = [f"지원 직무: {role}", f"시나리오: {scenario}", "대화 로그:"]
    for turn in turns:
        speaker = turn.speaker or turn.role
        content = turn.message or turn.user_answer or turn.prompt or ""
        lines.append(f"[{speaker}] {content}")
    return "\n".join(lines)


def _extract_score_delta(payload: dict[str, Any]) -> dict[str, int] | None:
    value = payload.get("score_delta")
    if not isinstance(value, dict):
        return None
    normalized: dict[str, int] = {}
    for key, score in value.items():
        if isinstance(score, (int, float)):
            normalized[key] = int(score)
    return normalized or None


def _default_start_message(session: UnifiedSession) -> str:
    meta = session.meta or {}
    role = meta.get("role") or "직무"
    return f"{role} 상황 면접을 시작합니다. 가장 까다로운 이슈를 먼저 설명해보세요."


def _generate_job_sim_message(context: str, user_message: str | None) -> dict[str, Any]:
    prompt = context
    if user_message:
        prompt = f"{context}\n\n사용자 최신 답변:\n{user_message}"

    gemini = GeminiClient()
    return gemini.generate_json(SIM_SYSTEM_PROMPT, prompt)


def start_unified_session(
    db: Session,
    user_id: int,
    payload: SessionStartRequest,
) -> SessionStartResponse:
    project = get_project_by_id(db=db, project_id=payload.project_id, user_id=user_id)
    if not project:
        raise NotFoundError("Project not found")

    session = create_session(
        db=db,
        project_id=payload.project_id,
        user_id=user_id,
        session_type=payload.session_type.value,
        total_items=payload.total_items,
        meta=payload.meta,
    )

    initial_turn: SessionTurn | None = None
    if payload.session_type == SessionType.JOB_SIMULATION:
        generated: dict[str, Any] = {}
        try:
            generated = _generate_job_sim_message(
                context=_build_job_sim_context(session, turns=[]),
                user_message=None,
            )
        except Exception:
            generated = {}

        initial_turn = create_turn(
            db=db,
            session=session,
            role=SessionRole.AI.value,
            speaker=str(generated.get("persona") or "AI 시뮬레이터"),
            prompt=None,
            user_answer=None,
            message=str(generated.get("response") or _default_start_message(session)),
            intent=str(generated.get("intent") or "상황 적응력 확인"),
            feedback=str(generated.get("feedback") or ""),
            score=None,
            score_delta=_extract_score_delta(generated),
            meta=None,
            turn_index=1,
        )
        session.current_index = 2
        update_session(db=db, session=session)

    return SessionStartResponse(
        session=_to_session_response(session),
        initial_turn=_to_turn_response(initial_turn) if initial_turn else None,
    )


def append_unified_turn(
    db: Session,
    user_id: int,
    session_id: uuid.UUID,
    payload: SessionTurnCreateRequest,
) -> SessionAppendTurnResponse:
    session = get_session_by_id(db=db, session_id=session_id, user_id=user_id)
    if not session:
        raise NotFoundError("Session not found")

    turn_index = get_next_turn_index(db=db, session_id=session.id)
    created_turn = create_turn(
        db=db,
        session=session,
        role=payload.role.value,
        speaker=payload.speaker,
        prompt=payload.prompt,
        user_answer=payload.user_answer,
        message=payload.message,
        intent=payload.intent,
        feedback=payload.feedback,
        score=payload.score,
        score_delta=payload.score_delta,
        meta=payload.meta,
        turn_index=turn_index,
    )

    generated_turn: SessionTurn | None = None
    auto_reply = payload.auto_reply and payload.role == SessionRole.USER
    is_job_simulation = session.session_type == SessionType.JOB_SIMULATION.value

    if auto_reply and is_job_simulation and payload.message:
        recent_turns_desc = list_turns_by_session(db=db, session_id=session.id, limit=10, desc=True)
        recent_turns = list(reversed(recent_turns_desc))

        generated: dict[str, Any] = {}
        try:
            generated = _generate_job_sim_message(
                context=_build_job_sim_context(session, turns=recent_turns),
                user_message=payload.message,
            )
        except Exception:
            generated = {}

        generated_turn = create_turn(
            db=db,
            session=session,
            role=SessionRole.AI.value,
            speaker=str(generated.get("persona") or "AI 시뮬레이터"),
            prompt=str(generated.get("intent") or "압박 꼬리 질문"),
            user_answer=None,
            message=str(generated.get("response") or "답변을 더 구체적으로 설명해 주세요."),
            intent=str(generated.get("intent") or "의사결정 근거 확인"),
            feedback=str(generated.get("feedback") or ""),
            score=None,
            score_delta=_extract_score_delta(generated),
            meta=None,
            turn_index=created_turn.turn_index + 1,
        )

    latest_turn_index = generated_turn.turn_index if generated_turn else created_turn.turn_index
    session.current_index = latest_turn_index + 1
    session.status = SessionStatus.IN_PROGRESS.value
    session = update_session(db=db, session=session)

    return SessionAppendTurnResponse(
        session=_to_session_response(session),
        created_turn=_to_turn_response(created_turn),
        generated_turn=_to_turn_response(generated_turn) if generated_turn else None,
    )


def analyze_unified_session(
    db: Session,
    user_id: int,
    session_id: uuid.UUID,
) -> SessionAnalyzeResponse:
    session = get_session_by_id(db=db, session_id=session_id, user_id=user_id)
    if not session:
        raise NotFoundError("Session not found")

    turns = list_turns_by_session(db=db, session_id=session.id, desc=False)

    result_json: dict[str, Any]
    if session.session_type == SessionType.JOB_SIMULATION.value:
        score_summary: dict[str, int] = {}
        for turn in turns:
            if not turn.score_delta:
                continue
            for key, value in turn.score_delta.items():
                if isinstance(value, (int, float)):
                    score_summary[key] = score_summary.get(key, 0) + int(value)

        report = {
            "archetype": "실전형",
            "summary": "대화를 기반으로 커뮤니케이션/책임감/협업 점수를 집계했습니다.",
            "best_moment": "근거를 제시한 답변",
            "worst_moment": "근거가 부족한 답변",
            "resume_snippet": "압박 상황에서도 우선순위를 재정의하며 문제를 해결했습니다.",
        }

        settings = get_settings()
        if settings.gemini_api_key:
            try:
                context = _build_job_sim_context(session, turns)
                gemini = GeminiClient()
                payload = gemini.generate_json(
                    SIM_REPORT_PROMPT,
                    f"{context}\n\n점수 요약: {score_summary}",
                )
                report = {
                    "archetype": str(payload.get("archetype") or report["archetype"]),
                    "summary": str(payload.get("summary") or report["summary"]),
                    "best_moment": str(payload.get("best_moment") or report["best_moment"]),
                    "worst_moment": str(payload.get("worst_moment") or report["worst_moment"]),
                    "resume_snippet": str(
                        payload.get("resume_snippet") or report["resume_snippet"]
                    ),
                }
            except Exception:
                pass

        result_json = {
            "session_type": SessionType.JOB_SIMULATION.value,
            "score_summary": score_summary,
            "report": report,
            "turn_count": len(turns),
        }
    else:
        scored = [float(turn.score) for turn in turns if turn.score is not None]
        feedbacks = [turn.feedback for turn in turns if turn.feedback]
        result_json = {
            "session_type": session.session_type,
            "average_score": round(sum(scored) / len(scored), 2) if scored else None,
            "score_count": len(scored),
            "feedback_count": len(feedbacks),
            "feedback_samples": feedbacks[:5],
            "turn_count": len(turns),
        }

    now = datetime.now(tz=UTC)
    session.result_json = result_json
    session.status = SessionStatus.COMPLETED.value
    session.ended_at = now
    if session.started_at:
        session.duration_sec = int((now - session.started_at).total_seconds())
    session = update_session(db=db, session=session)

    return SessionAnalyzeResponse(session=_to_session_response(session), result_json=result_json)


def get_unified_session_detail(
    db: Session,
    user_id: int,
    session_id: uuid.UUID,
    include_turns: bool,
) -> SessionDetailResponse:
    session = get_session_by_id(db=db, session_id=session_id, user_id=user_id)
    if not session:
        raise NotFoundError("Session not found")

    turns = list_turns_by_session(db=db, session_id=session.id, desc=False) if include_turns else []
    return SessionDetailResponse(
        session=_to_session_response(session),
        turns=[_to_turn_response(turn) for turn in turns],
    )
