from uuid import UUID

from pydantic import BaseModel, Field


class DeepInterviewQuestion(BaseModel):
    questionId: str
    prompt: str


class DeepInterviewStartRequest(BaseModel):
    projectId: UUID


class DeepInterviewStartResponse(BaseModel):
    sessionId: UUID
    totalQuestions: int
    currentIndex: int
    firstQuestion: DeepInterviewQuestion


class DeepInterviewAnswerRequest(BaseModel):
    sessionId: UUID
    questionId: str
    answer: str = Field(min_length=1)


class DeepInterviewProgress(BaseModel):
    current: int
    total: int


class DeepInterviewAnswerResponse(BaseModel):
    nextQuestion: DeepInterviewQuestion | None = None
    progress: DeepInterviewProgress | None = None
    completed: bool = False
    nextStep: str | None = None


class DeepInterviewSessionResponse(BaseModel):
    sessionId: UUID
    currentIndex: int
    totalQuestions: int
    currentQuestion: DeepInterviewQuestion | None = None


class GuideSection(BaseModel):
    type: str
    title: str
    items: list[str]


class DeepInterviewGuideResponse(BaseModel):
    guideSections: list[GuideSection]


class DeepInterviewGuideRequest(BaseModel):
    sessionId: UUID


class InsightDocResponse(BaseModel):
    summary: str
    strengthPoints: list[str]
    weakPoints: list[str]
    evidenceQuotes: list[str]
    actionChecklist: list[str]
