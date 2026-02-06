from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SessionType(StrEnum):
    DEEP_INTERVIEW = "DEEP_INTERVIEW"
    MOCK_INTERVIEW = "MOCK_INTERVIEW"
    JOB_SIMULATION = "JOB_SIMULATION"


class SessionStatus(StrEnum):
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"


class SessionRole(StrEnum):
    SYSTEM = "system"
    NPC = "npc"
    USER = "user"
    AI = "ai"


class SessionStartRequest(BaseModel):
    project_id: UUID
    session_type: SessionType
    total_items: int | None = Field(default=None, ge=1)
    meta: dict[str, Any] | None = None


class SessionTurnCreateRequest(BaseModel):
    role: SessionRole = SessionRole.USER
    speaker: str | None = Field(default=None, max_length=50)
    prompt: str | None = None
    user_answer: str | None = None
    message: str | None = None
    intent: str | None = None
    feedback: str | None = None
    score: float | None = None
    score_delta: dict[str, int] | None = None
    meta: dict[str, Any] | None = None
    auto_reply: bool = False


class SessionTurnResponse(BaseModel):
    id: UUID
    session_id: UUID
    project_id: UUID
    user_id: int
    turn_index: int
    role: SessionRole
    speaker: str | None = None
    prompt: str | None = None
    user_answer: str | None = None
    message: str | None = None
    intent: str | None = None
    feedback: str | None = None
    score: float | None = None
    score_delta: dict[str, int] | None = None
    meta: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class SessionResponse(BaseModel):
    id: UUID
    project_id: UUID
    user_id: int
    session_type: SessionType
    status: SessionStatus
    total_items: int | None = None
    current_index: int
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_sec: int | None = None
    meta: dict[str, Any] | None = None
    result_json: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class SessionStartResponse(BaseModel):
    session: SessionResponse
    initial_turn: SessionTurnResponse | None = None


class SessionAppendTurnResponse(BaseModel):
    session: SessionResponse
    created_turn: SessionTurnResponse
    generated_turn: SessionTurnResponse | None = None


class SessionAnalyzeResponse(BaseModel):
    session: SessionResponse
    result_json: dict[str, Any]


class SessionDetailResponse(BaseModel):
    session: SessionResponse
    turns: list[SessionTurnResponse]
