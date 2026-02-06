from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ResumeParagraphResponse(BaseModel):
    paragraphId: UUID
    title: str
    text: str
    charLimit: int
    updatedAt: datetime


class ResumeParagraphPatchRequest(BaseModel):
    text: str = Field(default="")


class ResumeParagraphPatchResponse(BaseModel):
    saved: bool
    updatedAt: datetime
    charCount: int


class ResumeParagraphCompleteResponse(BaseModel):
    paragraphId: UUID
    status: str
    completedAt: datetime


class ResumeCoachPolicy(BaseModel):
    noGhostwriting: bool = True


class ResumeCoachAskRequest(BaseModel):
    projectId: UUID
    resumeId: UUID
    paragraphId: UUID
    paragraphText: str
    userQuestion: str
    policy: ResumeCoachPolicy = ResumeCoachPolicy()


class ResumeCoachAnswer(BaseModel):
    type: str = "GUIDANCE"
    summary: str
    followUpQuestions: list[str]
    checklist: list[str]


class ResumeCoachAskResponse(BaseModel):
    coachAnswer: ResumeCoachAnswer

