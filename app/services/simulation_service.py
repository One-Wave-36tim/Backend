from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import NotFoundError
from app.db.repositories.project_repository import get_latest_project_by_user, get_project_by_id
from app.db.repositories.session_repository import (
    create_session,
    create_turn,
    get_next_turn_index,
    get_session_by_id,
    list_turns_by_session,
)
from app.schemas.session import SessionRole
from app.schemas.simulation import (
    SimulationAnalyzeResponse,
    SimulationChatRequest,
    SimulationChatResponse,
    SimulationReport,
    SimulationStartRequest,
    SimulationStartResponse,
)
from app.services.gemini_client import GeminiClient

LEGACY_START_SYSTEM_PROMPT = """너는 직무 시뮬레이션 챗봇이다.
사용자에게 스트레스를 주는 현실적 상황을 만든다.
반드시 JSON:
{
  "persona":"기획자",
  "response":"첫 압박 메시지",
  "score_change":{"logic":0,"mental":0,"responsibility":0,"collaboration":0}
}
"""

LEGACY_TURN_SYSTEM_PROMPT = """너는 직무 시뮬레이션 챗봇이다.
기획자/디자이너/백엔드/고객 중 상황에 맞는 페르소나로 답한다.
스트레스를 주되 현실적인 업무 대화여야 한다.
반드시 JSON:
{
  "persona":"백엔드",
  "response":"압박 메시지",
  "score_change":{"logic":1,"mental":-1,"responsibility":0,"collaboration":1}
}
"""

LEGACY_ANALYZE_SYSTEM_PROMPT = """너는 시뮬레이션 코치다.
대화와 누적 점수로 리포트를 작성한다.
반드시 JSON:
{
  "archetype":"문자열",
  "radar_scores":{"logic":0,"mental":0,"responsibility":0,"collaboration":0},
  "best_moment":"문자열",
  "worst_moment":"문자열",
  "summary":"문자열",
  "resume_snippet":"문자열"
}
"""


def _call_gemini_json(system_prompt: str, user_prompt: str) -> dict[str, Any] | None:
    settings = get_settings()
    if not settings.gemini_api_key:
        return None
    try:
        gemini = GeminiClient()
        return gemini.generate_json(system_prompt=system_prompt, user_prompt=user_prompt)
    except Exception:
        return None


def _resolve_project_id(db: Session, user_id: int, project_id: uuid.UUID | None) -> uuid.UUID:
    if project_id is not None:
        project = get_project_by_id(db=db, project_id=project_id, user_id=user_id)
        if project is None:
            raise NotFoundError("Project not found")
        return project.id
    latest = get_latest_project_by_user(db=db, user_id=user_id)
    if latest is None:
        raise NotFoundError("Project not found")
    return latest.id


def _extract_score(payload: dict[str, Any], key: str) -> dict[str, int] | None:
    value = payload.get(key)
    if not isinstance(value, dict):
        return None
    score: dict[str, int] = {}
    for k in ["logic", "mental", "responsibility", "collaboration"]:
        raw = value.get(k)
        if isinstance(raw, (int, float)):
            score[k] = int(raw)
    return score or None


def _merge_scores(base: dict[str, int], delta: dict[str, int] | None) -> dict[str, int]:
    merged = dict(base)
    if not delta:
        return merged
    for key, value in delta.items():
        merged[key] = merged.get(key, 0) + int(value)
    return merged


def _build_context(session, logs) -> str:
    lines = [
        f"직무: {(session.meta or {}).get('role', '미지정')}",
        f"회사 상황: {(session.meta or {}).get('company_context', '미지정')}",
        f"공고 요약: {(session.meta or {}).get('job_description', '미지정')}",
        "대화 로그:",
    ]
    for log in logs:
        speaker = log.speaker or log.role
        content = log.message or log.user_answer or log.prompt or ""
        lines.append(f"[{speaker}] {content}")
    return "\n".join(lines)


def start_simulation(
    db: Session,
    user_id: int,
    payload: SimulationStartRequest,
) -> SimulationStartResponse:
    project_id = _resolve_project_id(db=db, user_id=user_id, project_id=payload.project_id)
    session = create_session(
        db=db,
        project_id=project_id,
        user_id=user_id,
        session_type="JOB_SIMULATION",
        total_items=10,
        meta={
            "legacy": True,
            "role": payload.job_role,
            "company_context": payload.company_context,
            "job_description": payload.job_description,
        },
    )

    first_message = "런칭 D-1입니다. 요구사항 충돌이 발생했어요. 우선순위를 말해보세요."
    persona = "기획자"
    delta = {"logic": 0, "mental": 0, "responsibility": 0, "collaboration": 0}
    ai = _call_gemini_json(
        system_prompt=LEGACY_START_SYSTEM_PROMPT,
        user_prompt=(
            f"직무={payload.job_role}\n"
            f"회사상황={payload.company_context or '미지정'}\n"
            f"공고={payload.job_description or '미지정'}"
        ),
    )
    if isinstance(ai, dict):
        first_message = str(ai.get("response") or first_message)
        persona = str(ai.get("persona") or persona)
        delta = _extract_score(ai, "score_change") or delta

    create_turn(
        db=db,
        session=session,
        role=SessionRole.AI.value,
        speaker=persona,
        prompt=None,
        user_answer=None,
        message=first_message,
        intent="초기 압박 상황 제시",
        feedback=None,
        score=None,
        score_delta=delta,
        meta=None,
        turn_index=1,
    )
    return SimulationStartResponse(
        session_id=session.id,
        initial_message=first_message,
        persona=persona,
        current_score=delta,
    )


def chat_simulation(
    db: Session,
    user_id: int,
    payload: SimulationChatRequest,
) -> SimulationChatResponse:
    session = get_session_by_id(db=db, session_id=payload.session_id, user_id=user_id)
    if session is None or session.session_type != "JOB_SIMULATION":
        raise NotFoundError("Simulation session not found")

    user_turn_index = get_next_turn_index(db=db, session_id=session.id)
    create_turn(
        db=db,
        session=session,
        role=SessionRole.USER.value,
        speaker="사용자",
        prompt=None,
        user_answer=payload.message,
        message=payload.message,
        intent=None,
        feedback=None,
        score=None,
        score_delta=None,
        meta=None,
        turn_index=user_turn_index,
    )
    logs = list_turns_by_session(db=db, session_id=session.id, desc=False)
    context = _build_context(session, logs)

    persona = "기획자"
    response = "근거는 좋은데 일정/리스크 관리 관점도 포함해 다시 답해보세요."
    score_change = {"logic": 0, "mental": 0, "responsibility": 0, "collaboration": 0}
    ai = _call_gemini_json(
        system_prompt=LEGACY_TURN_SYSTEM_PROMPT,
        user_prompt=f"{context}\n\n사용자 최신 답변: {payload.message}",
    )
    if isinstance(ai, dict):
        persona = str(ai.get("persona") or persona)
        response = str(ai.get("response") or response)
        score_change = _extract_score(ai, "score_change") or score_change

    create_turn(
        db=db,
        session=session,
        role=SessionRole.AI.value,
        speaker=persona,
        prompt=None,
        user_answer=None,
        message=response,
        intent="압박 꼬리 질문",
        feedback=None,
        score=None,
        score_delta=score_change,
        meta=None,
        turn_index=user_turn_index + 1,
    )

    all_logs = list_turns_by_session(db=db, session_id=session.id, desc=False)
    current_score: dict[str, int] = {}
    for row in all_logs:
        delta = row.score_delta if isinstance(row.score_delta, dict) else None
        current_score = _merge_scores(current_score, delta)
    return SimulationChatResponse(
        response=response,
        persona=persona,
        current_score=current_score,
        score_change=score_change,
        ai_thought="다중 이해관계자 압박 대응 점검",
    )


def analyze_simulation(
    db: Session,
    user_id: int,
    session_id: uuid.UUID,
) -> SimulationAnalyzeResponse:
    session = get_session_by_id(db=db, session_id=session_id, user_id=user_id)
    if session is None or session.session_type != "JOB_SIMULATION":
        raise NotFoundError("Simulation session not found")

    logs = list_turns_by_session(db=db, session_id=session.id, desc=False)
    total_score: dict[str, int] = {}
    for row in logs:
        delta = row.score_delta if isinstance(row.score_delta, dict) else None
        total_score = _merge_scores(total_score, delta)

    radar_scores = {
        "logic": max(0, min(100, 50 + total_score.get("logic", 0) * 5)),
        "mental": max(0, min(100, 50 + total_score.get("mental", 0) * 5)),
        "responsibility": max(0, min(100, 50 + total_score.get("responsibility", 0) * 5)),
        "collaboration": max(0, min(100, 50 + total_score.get("collaboration", 0) * 5)),
    }
    report = SimulationReport(
        archetype="실전형 인재",
        radar_scores=radar_scores,
        best_moment="다중 이해관계자 요구를 분리해 대응한 답변",
        worst_moment="근거 없이 즉답한 구간",
        summary="압박 상황에서도 커뮤니케이션은 유지됐지만, 우선순위 근거를 더 명확히 해야 합니다.",
        resume_snippet=(
            "다수 이해관계자의 충돌 요구를 우선순위 기준으로 조율해 "
            "실행 계획을 제시했습니다."
        ),
    )

    ai = _call_gemini_json(
        system_prompt=LEGACY_ANALYZE_SYSTEM_PROMPT,
        user_prompt=f"{_build_context(session, logs)}\n\n누적점수: {total_score}",
    )
    if isinstance(ai, dict):
        report = SimulationReport(
            archetype=str(ai.get("archetype", report.archetype)),
            radar_scores=_extract_score(ai, "radar_scores") or report.radar_scores,
            best_moment=str(ai.get("best_moment", report.best_moment)),
            worst_moment=str(ai.get("worst_moment", report.worst_moment)),
            summary=str(ai.get("summary", report.summary)),
            resume_snippet=str(ai.get("resume_snippet", report.resume_snippet)),
        )
    return SimulationAnalyzeResponse(session_id=session.id, total_score=total_score, report=report)
