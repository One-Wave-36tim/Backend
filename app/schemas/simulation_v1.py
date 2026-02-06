from uuid import UUID

from pydantic import BaseModel, Field


class SimulationPreviewResponse(BaseModel):
    projectId: UUID
    title: str
    intro: dict
    scenarioPreview: dict
    cta: dict


class SimulationV1StartRequest(BaseModel):
    role: str
    scenarioId: str
    maxTurns: int = Field(default=10, ge=3, le=30)


class SimulationMessage(BaseModel):
    messageId: str
    role: str
    speaker: str
    text: str


class SimulationV1StartResponse(BaseModel):
    sessionId: UUID
    projectId: UUID
    status: str
    maxTurns: int
    turn: int
    messages: list[SimulationMessage]


class SimulationV1SessionResponse(BaseModel):
    sessionId: UUID
    status: str
    maxTurns: int
    turn: int
    messages: list[SimulationMessage]


class SimulationTurnRequest(BaseModel):
    text: str


class SimulationTurnResponse(BaseModel):
    turn: int
    messagesAppended: list[SimulationMessage]
    lightFeedback: dict | None = None
    done: bool
    next: dict | None = None


class SimulationResultResponse(BaseModel):
    sessionId: UUID
    fitScorePercent: int
    roleLabel: str
    rankLabel: str
    summaryMetrics: dict
    bestMoment: dict
    worstMoment: dict
    durability: list[dict]
    recommendations: list[dict]
    cta: dict

