from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MockInterviewQuestion(BaseModel):
    questionId: str
    prompt: str
    prepSeconds: int | None = None
    answerSeconds: int | None = None


class MockInterviewStartRequest(BaseModel):
    mode: str = "WEB_CAM"
    questionCount: int = Field(default=8, ge=1, le=20)


class MockInterviewStartResponse(BaseModel):
    sessionId: UUID
    totalQuestions: int
    currentIndex: int
    firstQuestion: MockInterviewQuestion


class MockInterviewAnswerRequest(BaseModel):
    questionId: str
    answer: str


class MockInterviewAnswerResponse(BaseModel):
    nextQuestion: MockInterviewQuestion | None = None
    progress: dict[str, int] | None = None
    completed: bool = False
    resultUrl: str | None = None


class MockSessionInfo(BaseModel):
    sessionId: UUID
    projectId: UUID
    title: str
    startedAt: datetime | None = None
    durationSec: int | None = None


class MockScoreItem(BaseModel):
    key: str
    label: str
    percent: int


class MockOverall(BaseModel):
    score: int
    subScores: list[MockScoreItem]


class MockFinding(BaseModel):
    code: str
    title: str
    detail: str


class MockQuestionResult(BaseModel):
    index: int
    questionId: str
    prompt: str
    intent: str
    userAnswer: str
    feedback: str
    modelAnswer: str
    score: float


class MockInterviewResultResponse(BaseModel):
    sessionInfo: MockSessionInfo
    overall: MockOverall
    keyFindings: list[MockFinding]
    questions: list[MockQuestionResult]


class MockInterviewSaveResponse(BaseModel):
    sessionId: UUID
    saved: bool
    savedAt: datetime

