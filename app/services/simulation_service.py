from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.db.entities.simulation import SimulationLog, SimulationSession
from app.schemas.simulation import (
    SimulationAnalyzeResponse,
    SimulationChatRequest,
    SimulationChatResponse,
    SimulationReport,
    SimulationStartRequest,
    SimulationStartResponse,
)
from app.services.gemini_client import GeminiClient


SYSTEM_PROMPT = """당신은 '악독한 직무 시뮬레이터'입니다.
사용자가 선택한 직무와 공고를 바탕으로 가장 스트레스 받는 상황을 연출하세요.

[역할]
당신은 상황에 따라 '다급한 팀장', '화난 고객', '말 안 통하는 협력사' 등 페르소나를 계속 바꿉니다.

[규칙]
1. 사용자의 답변을 분석하여 내부적으로 [논리성/책임감/멘탈/협업] 점수(-10 ~ +10)를 매기세요.
2. 답변이 너무 훌륭하면 더 어려운 꼬리 상황(Crisis)을 만드세요.
3. 답변이 감정적이거나 회피적이면, 그 약점을 파고드는 압박 질문을 던지세요.
4. 절대 AI처럼 말하지 말고, 사람처럼(오타 포함, 격한 감정) 연기하세요.

[출력 형식(JSON)]
thought: 내부 판단
persona: 현재 페르소나
response: 사용자에게 보여줄 대사
score_change: {"logic": -10~10, "mental": -10~10, "responsibility": -10~10, "collaboration": -10~10}
current_score: 누적 점수(선택)
"""


REPORT_PROMPT = """너는 면접/자소서용 리포트를 작성하는 코치다.
다음 대화 로그와 누적 점수를 바탕으로 리포트를 JSON으로 작성해라.

[출력 형식(JSON)]
archetype: 문자열
radar_scores: {"logic":0~100,"mental":0~100,"responsibility":0~100,"collaboration":0~100}
best_moment: 문자열
worst_moment: 문자열
summary: 문자열 (2~3문장)
resume_snippet: 문자열 (자소서 문구 1문장)
"""


def _merge_scores(base: dict[str, int], delta: dict[str, int] | None) -> dict[str, int]:
    if not delta:
        return dict(base)
    merged = dict(base)
    for key, value in delta.items():
        merged[key] = merged.get(key, 0) + int(value)
    return merged


def _extract_score(payload: dict[str, Any], key: str) -> dict[str, int] | None:
    value = payload.get(key)
    if isinstance(value, dict):
        return {k: int(v) for k, v in value.items() if isinstance(v, (int, float))}
    return None


def _build_context(session: SimulationSession, logs: list[SimulationLog]) -> str:
    lines = [
        f"직무: {session.job_role}",
        f"기업 상황: {session.company_context or '미지정'}",
        f"공고 요약: {session.job_description or '미지정'}",
    ]
    lines.append("대화 로그:")
    for log in logs:
        role = "User" if log.sender == "user" else "AI"
        lines.append(f"{role}: {log.message}")
    return "\n".join(lines)


def _next_turn_order(db: Session, session_id: UUID) -> int:
    stmt = select(func.max(SimulationLog.turn_order)).where(SimulationLog.session_id == session_id)
    last = db.execute(stmt).scalar()
    return (last or 0) + 1


def start_simulation(
    db: Session,
    user_id: int,
    payload: SimulationStartRequest,
) -> SimulationStartResponse:
    session = SimulationSession(
        user_id=user_id,
        job_role=payload.job_role,
        company_context=payload.company_context,
        job_description=payload.job_description,
        total_score={},
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    gemini = GeminiClient()
    user_prompt = (
        "아래 정보를 바탕으로 시뮬레이션을 시작해라.\n"
        f"직무: {payload.job_role}\n"
        f"기업 상황: {payload.company_context or '미지정'}\n"
        f"공고 요약: {payload.job_description or '미지정'}\n"
        "첫 대사를 생성하고 JSON으로 응답해라."
    )
    ai_payload = gemini.generate_json(SYSTEM_PROMPT, user_prompt)
    response = str(ai_payload.get("response", "")).strip()
    persona = str(ai_payload.get("persona", "")).strip() or None
    thought = str(ai_payload.get("thought", "")).strip() or None
    score_change = _extract_score(ai_payload, "score_change") or {}
    current_score = _extract_score(ai_payload, "current_score")

    total_score = current_score or _merge_scores({}, score_change)
    session.total_score = total_score
    log = SimulationLog(
        session_id=session.id,
        turn_order=1,
        sender="ai",
        message=response or "(빈 응답)",
        ai_thought=thought,
        score_change=score_change or None,
    )
    db.add(log)
    db.commit()

    return SimulationStartResponse(
        session_id=session.id,
        initial_message=log.message,
        persona=persona,
        current_score=total_score,
    )


def chat_simulation(
    db: Session,
    user_id: int,
    payload: SimulationChatRequest,
) -> SimulationChatResponse:
    session = db.get(SimulationSession, payload.session_id)
    if not session or session.user_id != user_id:
        raise NotFoundError("Simulation session not found")

    user_turn = _next_turn_order(db, session.id)
    user_log = SimulationLog(
        session_id=session.id,
        turn_order=user_turn,
        sender="user",
        message=payload.message,
    )
    db.add(user_log)
    db.commit()

    stmt = (
        select(SimulationLog)
        .where(SimulationLog.session_id == session.id)
        .order_by(SimulationLog.turn_order.desc())
        .limit(10)
    )
    logs = list(reversed(db.execute(stmt).scalars().all()))
    context = _build_context(session, logs)
    user_prompt = f"{context}\n\n다음 사용자 메시지에 응답해라:\n{payload.message}"

    gemini = GeminiClient()
    ai_payload = gemini.generate_json(SYSTEM_PROMPT, user_prompt)
    response = str(ai_payload.get("response", "")).strip()
    persona = str(ai_payload.get("persona", "")).strip() or None
    thought = str(ai_payload.get("thought", "")).strip() or None
    score_change = _extract_score(ai_payload, "score_change")
    current_score = _extract_score(ai_payload, "current_score")

    total_score = (
        current_score if current_score is not None else _merge_scores(session.total_score or {}, score_change)
    )
    session.total_score = total_score

    ai_log = SimulationLog(
        session_id=session.id,
        turn_order=user_turn + 1,
        sender="ai",
        message=response or "(빈 응답)",
        ai_thought=thought,
        score_change=score_change,
    )
    db.add(ai_log)
    db.commit()

    return SimulationChatResponse(
        response=ai_log.message,
        persona=persona,
        current_score=total_score,
        score_change=score_change,
        ai_thought=thought,
    )


def analyze_simulation(
    db: Session,
    user_id: int,
    session_id: SimulationSession.id,
) -> SimulationAnalyzeResponse:
    session = db.get(SimulationSession, session_id)
    if not session or session.user_id != user_id:
        raise NotFoundError("Simulation session not found")

    stmt = (
        select(SimulationLog)
        .where(SimulationLog.session_id == session.id)
        .order_by(SimulationLog.turn_order.asc())
    )
    logs = db.execute(stmt).scalars().all()
    context = _build_context(session, logs)
    user_prompt = f"{context}\n\n누적 점수: {session.total_score or {}}\nJSON으로 리포트를 작성해라."

    gemini = GeminiClient()
    report_payload = gemini.generate_json(REPORT_PROMPT, user_prompt)

    report = SimulationReport(
        archetype=str(report_payload.get("archetype", "분석형 인재")),
        radar_scores=_extract_score(report_payload, "radar_scores") or {},
        best_moment=str(report_payload.get("best_moment", "기록 없음")),
        worst_moment=str(report_payload.get("worst_moment", "기록 없음")),
        summary=str(report_payload.get("summary", "요약 없음")),
        resume_snippet=str(report_payload.get("resume_snippet", "추천 문구 없음")),
    )

    return SimulationAnalyzeResponse(
        session_id=session.id,
        total_score=session.total_score or {},
        report=report,
    )
