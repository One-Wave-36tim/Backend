from uuid import UUID

from pydantic import BaseModel, Field

ScoreMap = dict[str, int]


class SimulationStartRequest(BaseModel):
    project_id: UUID | None = Field(None, description="지원 프로젝트 ID")
    job_role: str = Field(..., description="지원 직무")
    company_context: str | None = Field(None, description="기업 상황 요약")
    job_description: str | None = Field(None, description="채용 공고 요약")


class SimulationStartResponse(BaseModel):
    session_id: UUID
    initial_message: str
    persona: str | None = None
    current_score: ScoreMap | None = None


class SimulationChatRequest(BaseModel):
    session_id: UUID
    message: str


class SimulationChatResponse(BaseModel):
    response: str
    persona: str | None = None
    current_score: ScoreMap | None = None
    score_change: ScoreMap | None = None
    ai_thought: str | None = None


class SimulationAnalyzeRequest(BaseModel):
    session_id: UUID


class SimulationReport(BaseModel):
    archetype: str
    radar_scores: ScoreMap
    best_moment: str
    worst_moment: str
    summary: str
    resume_snippet: str


class SimulationAnalyzeResponse(BaseModel):
    session_id: UUID
    total_score: ScoreMap | None = None
    report: SimulationReport
