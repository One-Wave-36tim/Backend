from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class CoachStatus(StrEnum):
    COACHING = "COACHING"
    PAUSED = "PAUSED"


class HomeUserCard(BaseModel):
    userId: int
    name: str
    targetRole: str | None = None
    coachStatus: CoachStatus
    avatarUrl: str | None = None
    myPageDeepLink: str = "app://my-page"


class HomeProjectItem(BaseModel):
    projectId: UUID
    companyName: str
    roleTitle: str
    status: str
    startedAt: date | None = None
    progressPercent: int
    deadlineAt: date | None = None
    dDay: int | None = None
    lastActivityAt: datetime | None = None
    lastActivityLabel: str | None = None


class HomeRoutineItem(BaseModel):
    routineItemId: UUID
    label: str
    checked: bool
    source: str


class HomeRoutine(BaseModel):
    title: str = "오늘의 추천 행동"
    items: list[HomeRoutineItem]


class HomeResponse(BaseModel):
    userCard: HomeUserCard
    projects: list[HomeProjectItem]
    routine: HomeRoutine

