import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
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
from app.schemas.session import SessionRole
from app.schemas.simulation_v1 import (
    SimulationMessage,
    SimulationPreviewResponse,
    SimulationResultResponse,
    SimulationTurnResponse,
    SimulationV1SessionResponse,
    SimulationV1StartRequest,
    SimulationV1StartResponse,
)
from app.services.gemini_client import GeminiClient

SCENARIO_SYSTEM_PROMPT = """너는 직무 시뮬레이션 시나리오 생성기다.
사용자가 직무 적합성을 검증할 수 있도록 긴장감 있는 업무 상황을 만든다.
기획자/디자이너/백엔드/고객 중 최소 2명이 갈등을 만든다.
반드시 JSON으로만 응답:
{
  "headline": "문자열",
  "bullets": ["문자열", "..."],
  "expectedMinutes": 12,
  "scenario": {
    "roleLabel": "문자열",
    "difficulty": "중급",
    "description": "문자열",
    "goals": ["시간 관리","의사소통","위기 대처"]
  },
  "openingMessages": [
    {"speaker":"기획자","text":"...","intent":"..."},
    {"speaker":"디자이너","text":"...","intent":"..."}
  ]
}
"""

TURN_SYSTEM_PROMPT = """너는 직무 시뮬레이션 진행 엔진이다.
사용자 답변을 보고 압박 상황을 이어간다.
기획자/디자이너/백엔드/고객/PM 중 상황에 맞는 화자를 선택해라.
출력은 JSON만:
{
  "messages": [
    {"speaker":"기획자","text":"...","intent":"..."},
    {"speaker":"백엔드","text":"...","intent":"..."}
  ],
  "scoreDelta": {"communication":1,"stress":-1,"problemSolving":1},
  "tags": ["우선순위 명확", "근거 보강 필요"],
  "shouldFinish": false
}
"""

RESULT_SYSTEM_PROMPT = """너는 시뮬레이션 결과 리포트 생성기다.
대화 로그와 누적 점수를 보고 결과 JSON을 작성한다.
출력은 JSON만:
{
  "fitScorePercent": 0~100,
  "rankLabel": "상위 8%",
  "bestMomentText": "...",
  "worstMomentText": "...",
  "recommendText": "...",
  "durability": {"stress":0~1,"focus":0~1,"feedback":0~1}
}
"""


def _message_from_turn(turn) -> SimulationMessage:
    content = turn.message or turn.user_answer or turn.prompt or ""
    return SimulationMessage(
        messageId=str(turn.id),
        role=turn.role,
        speaker=turn.speaker or turn.role,
        text=content,
    )


def _user_turn_count(turns: list[Any]) -> int:
    return sum(
        1
        for turn in turns
        if turn.role == SessionRole.USER.value and (turn.message or turn.user_answer)
    )


def _call_gemini_json(system_prompt: str, user_prompt: str) -> dict[str, Any] | None:
    settings = get_settings()
    if not settings.gemini_api_key:
        return None
    try:
        gemini = GeminiClient()
        return gemini.generate_json(system_prompt=system_prompt, user_prompt=user_prompt)
    except Exception:
        return None


def _fallback_opening(role: str) -> dict[str, Any]:
    return {
        "headline": "멀티 페르소나 압박 시뮬레이션",
        "bullets": [
            "기획자/디자이너/백엔드가 동시에 요구사항을 제시합니다.",
            "당신은 우선순위와 커뮤니케이션 전략으로 상황을 풀어야 합니다.",
            "답변 흐름을 기반으로 커뮤니케이션 적합도를 평가합니다.",
        ],
        "expectedMinutes": 12,
        "scenario": {
            "roleLabel": role,
            "difficulty": "중급",
            "description": "런칭 당일, 디자인 변경/기획 요구/백엔드 제약이 동시에 발생했습니다.",
            "goals": ["시간 관리", "의사소통", "위기 대처"],
        },
        "openingMessages": [
            {
                "speaker": "기획자",
                "text": "핵심 KPI 때문에 오늘 안에 기능 우선순위를 바꿔야 해요.",
                "intent": "우선순위 재조정 압박",
            },
            {
                "speaker": "디자이너",
                "text": "새 브랜딩 가이드 반영이 필요해요. 지금 수정 가능해요?",
                "intent": "디자인 변경 협상",
            },
            {
                "speaker": "백엔드",
                "text": "API 응답이 느려서 프론트 단에서 완충 전략이 필요합니다.",
                "intent": "기술 제약 공유",
            },
        ],
    }


def _build_preview(project_id: uuid.UUID) -> SimulationPreviewResponse:
    return SimulationPreviewResponse(
        projectId=project_id,
        title="직무별 시뮬레이션",
        intro={
            "headline": "AI 시뮬레이션 체험",
            "bullets": [
                "기획자/디자이너/백엔드 등 다중 이해관계자와 대화합니다.",
                "갈등 상황에서 우선순위와 커뮤니케이션 역량을 검증합니다.",
                "종료 후 직무 적합도 리포트를 제공합니다.",
            ],
            "expectedMinutes": 12,
        },
        scenarioPreview={
            "step": 1,
            "totalSteps": 5,
            "roleLabel": "프로젝트 관리자 역할",
            "difficulty": "중급",
            "description": "런칭 직전 다수 이해관계자 요구가 충돌하는 상황입니다.",
            "goals": ["시간 관리", "의사소통", "위기 대처"],
        },
        cta={"enabled": True, "label": "시뮬레이션 시작하기"},
    )


def _extract_score_delta(payload: dict[str, Any]) -> dict[str, int]:
    value = payload.get("scoreDelta")
    if not isinstance(value, dict):
        return {"communication": 0, "stress": 0, "problemSolving": 0}
    result = {"communication": 0, "stress": 0, "problemSolving": 0}
    for key in result:
        raw = value.get(key)
        if isinstance(raw, (int, float)):
            result[key] = int(raw)
    return result


def _fallback_turn_reply(text: str, turn: int) -> dict[str, Any]:
    lower = text.lower()
    tags: list[str] = []
    delta = {"communication": 0, "stress": 0, "problemSolving": 0}
    if "우선" in text or "priority" in lower:
        tags.append("우선순위 명확")
        delta["problemSolving"] += 1
    if any(token in text for token in ["공유", "협업", "소통"]):
        tags.append("소통 시도")
        delta["communication"] += 1
    if any(token in text for token in ["리스크", "위험", "대응"]):
        tags.append("리스크 인지")
        delta["stress"] += 1
    if not tags:
        tags.append("근거 보강 필요")

    speakers = ["기획자", "디자이너", "백엔드", "고객"]
    speaker = speakers[(turn - 1) % len(speakers)]
    prompts = [
        "좋아요, 근데 오늘 안에 절대 필요한 항목 2개만 선택해보세요.",
        "변경 요구를 반영하면 QA 일정이 밀려요. 어떤 기준으로 자를 건가요?",
        "API 한계가 있어요. 프론트에서 어떤 완충 UX를 제안할 수 있죠?",
        "고객 클레임이 들어왔어요. 지금 팀에 어떤 메시지를 먼저 공유하죠?",
    ]
    return {
        "messages": [
            {
                "speaker": speaker,
                "text": prompts[(turn - 1) % len(prompts)],
                "intent": "압박 질문",
            }
        ],
        "scoreDelta": delta,
        "tags": tags,
        "shouldFinish": False,
    }


def _build_result_fallback(session, turns: list[Any]) -> dict[str, Any]:
    score = 65
    for turn in turns:
        if isinstance(turn.score_delta, dict):
            score += sum(int(v) for v in turn.score_delta.values() if isinstance(v, (int, float)))
    fit = max(1, min(100, score))
    role_label = str((session.meta or {}).get("role", "직무"))
    return {
        "sessionId": str(session.id),
        "fitScorePercent": fit,
        "roleLabel": role_label,
        "rankLabel": "상위 8%" if fit >= 85 else ("상위 20%" if fit >= 70 else "상위 45%"),
        "summaryMetrics": {
            "tech": round(fit / 10, 1),
            "analysisCount": len(turns),
            "spentTimeHours": 48,
        },
        "bestMoment": {
            "title": "Best 순간",
            "text": "이해관계자 요구를 분리하고 우선순위를 제시한 답변이 강점이었습니다.",
            "dateLabel": "2025.03",
            "impactLabel": "+15% 영향력",
        },
        "worstMoment": {
            "title": "Worst 순간",
            "text": "근거 없이 단답형으로 응답한 구간에서 설득력이 낮아졌습니다.",
            "dateLabel": "2025.02",
            "tag": "개선 필요",
        },
        "durability": [
            {"key": "stress", "label": "스트레스 내성", "level": 0.72},
            {"key": "focus", "label": "업무 집중력", "level": 0.69},
            {"key": "feedback", "label": "피드백 수용", "level": 0.8},
        ],
        "recommendations": [
            {
                "title": "보완점 추천",
                "text": "결론→근거→리스크→대안 순으로 답변하면 이해관계자 설득력이 올라갑니다.",
                "tags": ["커뮤니케이션", "우선순위"],
            }
        ],
        "cta": {"label": "메타인지 리포트 상세 보기", "deepLink": f"app://simulation-report/{session.id}"},
    }


def _build_transcript(turns: list[Any]) -> str:
    lines: list[str] = []
    for turn in turns:
        speaker = turn.speaker or turn.role
        content = turn.message or turn.user_answer or turn.prompt or ""
        lines.append(f"[{speaker}] {content}")
    return "\n".join(lines)


def get_simulation_preview(project_id: uuid.UUID) -> SimulationPreviewResponse:
    return _build_preview(project_id)


def start_simulation_v1(
    db: Session,
    user_id: int,
    project_id: uuid.UUID,
    payload: SimulationV1StartRequest,
) -> SimulationV1StartResponse:
    project = get_project_by_id(db=db, project_id=project_id, user_id=user_id)
    if project is None:
        raise NotFoundError("Project not found")

    opening = _fallback_opening(payload.role)
    ai_payload = _call_gemini_json(
        system_prompt=SCENARIO_SYSTEM_PROMPT,
        user_prompt=(
            f"직무: {payload.role}\n"
            f"회사: {project.company_name}\n"
            f"지원 포지션: {project.role_title}\n"
            f"scenarioId: {payload.scenarioId}\n"
            "서로 충돌하는 요구가 나타나는 상황을 만들어라."
        ),
    )
    if isinstance(ai_payload, dict) and "openingMessages" in ai_payload:
        opening = ai_payload

    session = create_session(
        db=db,
        project_id=project_id,
        user_id=user_id,
        session_type="JOB_SIMULATION",
        total_items=payload.maxTurns,
        meta={
            "role": payload.role,
            "scenarioId": payload.scenarioId,
            "maxTurns": payload.maxTurns,
            "scenario": opening.get("scenario", {}),
            "headline": opening.get("headline"),
        },
    )

    system_turn = create_turn(
        db=db,
        session=session,
        role=SessionRole.SYSTEM.value,
        speaker="시스템",
        prompt=None,
        user_answer=None,
        message=str(opening.get("headline") or "직무 시뮬레이션을 시작합니다."),
        intent="시뮬레이션 시작 안내",
        feedback=None,
        score=None,
        score_delta=None,
        meta={"scenario": opening.get("scenario", {})},
        turn_index=1,
    )

    opening_messages = opening.get("openingMessages") or []
    created_messages = [_message_from_turn(system_turn)]
    next_index = 2
    for row in opening_messages[:3]:
        npc_turn = create_turn(
            db=db,
            session=session,
            role=SessionRole.NPC.value,
            speaker=str(row.get("speaker", "기획자")),
            prompt=None,
            user_answer=None,
            message=str(row.get("text", "")),
            intent=str(row.get("intent", "압박 상황 제시")),
            feedback=None,
            score=None,
            score_delta={"communication": 0, "stress": 0, "problemSolving": 0},
            meta=None,
            turn_index=next_index,
        )
        created_messages.append(_message_from_turn(npc_turn))
        next_index += 1

    session.current_index = 1
    update_session(db=db, session=session)
    return SimulationV1StartResponse(
        sessionId=session.id,
        projectId=session.project_id,
        status=session.status,
        maxTurns=payload.maxTurns,
        turn=1,
        messages=created_messages,
    )


def get_simulation_session_v1(
    db: Session,
    user_id: int,
    session_id: uuid.UUID,
) -> SimulationV1SessionResponse:
    session = get_session_by_id(db=db, session_id=session_id, user_id=user_id)
    if session is None or session.session_type != "JOB_SIMULATION":
        raise NotFoundError("Simulation session not found")
    turns = list_turns_by_session(db=db, session_id=session.id, desc=False)
    messages = [_message_from_turn(turn) for turn in turns if (turn.message or turn.user_answer)]
    return SimulationV1SessionResponse(
        sessionId=session.id,
        status=session.status,
        maxTurns=session.total_items or 10,
        turn=_user_turn_count(turns) + 1,
        messages=messages,
    )


def append_simulation_turn_v1(
    db: Session,
    user_id: int,
    session_id: uuid.UUID,
    text: str,
) -> SimulationTurnResponse:
    session = get_session_by_id(db=db, session_id=session_id, user_id=user_id)
    if session is None or session.session_type != "JOB_SIMULATION":
        raise NotFoundError("Simulation session not found")
    if session.status == "COMPLETED":
        raise ValueError("Simulation already completed")

    turns = list_turns_by_session(db=db, session_id=session.id, desc=False)
    current_user_turn = _user_turn_count(turns) + 1
    turn_index = get_next_turn_index(db=db, session_id=session.id)
    create_turn(
        db=db,
        session=session,
        role=SessionRole.USER.value,
        speaker="나",
        prompt=None,
        user_answer=text,
        message=text,
        intent=None,
        feedback=None,
        score=None,
        score_delta=None,
        meta=None,
        turn_index=turn_index,
    )

    pseudo_turn = {
        "speaker": "나",
        "role": "user",
        "message": text,
        "user_answer": text,
        "prompt": None,
    }
    transcript_turns: list[Any] = list(turns) + [type("PseudoTurn", (), pseudo_turn)]
    transcript = _build_transcript(transcript_turns)
    ai_payload = _call_gemini_json(
        system_prompt=TURN_SYSTEM_PROMPT,
        user_prompt=(
            f"시나리오: {(session.meta or {}).get('scenario', {})}\n"
            f"현재 사용자 턴: {current_user_turn}\n"
            f"대화 로그:\n{transcript}\n"
            "사용자에게 스트레스를 주되 현실적인 업무 상황으로 메시지를 생성해라."
        ),
    )
    response_payload = (
        ai_payload
        if isinstance(ai_payload, dict) and isinstance(ai_payload.get("messages"), list)
        else _fallback_turn_reply(text=text, turn=current_user_turn)
    )

    tags = [str(item) for item in response_payload.get("tags", [])]
    delta = _extract_score_delta(response_payload)
    created_messages: list[SimulationMessage] = []
    next_turn_index = turn_index + 1
    for row in response_payload.get("messages", [])[:2]:
        npc_turn = create_turn(
            db=db,
            session=session,
            role=SessionRole.NPC.value,
            speaker=str(row.get("speaker", "기획자")),
            prompt=None,
            user_answer=None,
            message=str(row.get("text", "")),
            intent=str(row.get("intent", "압박 질의")),
            feedback=", ".join(tags),
            score=None,
            score_delta=delta,
            meta=None,
            turn_index=next_turn_index,
        )
        created_messages.append(_message_from_turn(npc_turn))
        next_turn_index += 1

    max_turns = session.total_items or 10
    done = current_user_turn >= max_turns or bool(response_payload.get("shouldFinish"))
    session.current_index = current_user_turn + 1
    if done:
        session.status = "COMPLETED"
        session.ended_at = datetime.now(tz=UTC)
        if session.started_at:
            session.duration_sec = int((session.ended_at - session.started_at).total_seconds())
        final_turns = list_turns_by_session(db=db, session_id=session.id, desc=False)
        session.result_json = _build_result_fallback(session=session, turns=final_turns)
    update_session(db=db, session=session)

    return SimulationTurnResponse(
        turn=current_user_turn,
        messagesAppended=created_messages,
        lightFeedback={"tags": tags, "delta": delta},
        done=done,
        next=(
            {"type": "RESULT", "resultUrl": f"/v1/simulations/sessions/{session.id}/result"}
            if done
            else None
        ),
    )


def get_simulation_result_v1(
    db: Session,
    user_id: int,
    session_id: uuid.UUID,
) -> SimulationResultResponse:
    session = get_session_by_id(db=db, session_id=session_id, user_id=user_id)
    if session is None or session.session_type != "JOB_SIMULATION":
        raise NotFoundError("Simulation session not found")
    if not session.result_json:
        turns = list_turns_by_session(db=db, session_id=session.id, desc=False)
        session.result_json = _build_result_fallback(session=session, turns=turns)
        update_session(db=db, session=session)

    turns = list_turns_by_session(db=db, session_id=session.id, desc=False)
    transcript = _build_transcript(turns)
    ai_payload = _call_gemini_json(
        system_prompt=RESULT_SYSTEM_PROMPT,
        user_prompt=(
            f"시나리오: {(session.meta or {}).get('scenario', {})}\n"
            f"대화 로그:\n{transcript}\n"
            f"기본결과: {session.result_json}\n"
            "기본결과를 참고해 더 정확한 리포트 값으로 보정해라."
        ),
    )
    if isinstance(ai_payload, dict):
        base = dict(session.result_json)
        fit = ai_payload.get("fitScorePercent")
        if isinstance(fit, (int, float)):
            base["fitScorePercent"] = max(1, min(100, int(fit)))
        rank = ai_payload.get("rankLabel")
        if isinstance(rank, str):
            base["rankLabel"] = rank
        best = ai_payload.get("bestMomentText")
        if isinstance(best, str):
            base["bestMoment"]["text"] = best
        worst = ai_payload.get("worstMomentText")
        if isinstance(worst, str):
            base["worstMoment"]["text"] = worst
        recommend = ai_payload.get("recommendText")
        if isinstance(recommend, str):
            base["recommendations"][0]["text"] = recommend
        durability = ai_payload.get("durability")
        if isinstance(durability, dict):
            base["durability"] = [
                {
                    "key": "stress",
                    "label": "스트레스 내성",
                    "level": float(durability.get("stress", 0.7)),
                },
                {
                    "key": "focus",
                    "label": "업무 집중력",
                    "level": float(durability.get("focus", 0.7)),
                },
                {
                    "key": "feedback",
                    "label": "피드백 수용",
                    "level": float(durability.get("feedback", 0.7)),
                },
            ]
        session.result_json = base
        update_session(db=db, session=session)

    return SimulationResultResponse(**session.result_json)
