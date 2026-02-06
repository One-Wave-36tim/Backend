from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectStatus(StrEnum):
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW = "REVIEW"
    DONE = "DONE"


class ProjectCreateRequest(BaseModel):
    company_name: str = Field(min_length=1, max_length=100)
    role_title: str = Field(min_length=1, max_length=120)
    started_at: date | None = None
    deadline_at: date | None = None


class ProjectUpdateRequest(BaseModel):
    company_name: str | None = Field(default=None, min_length=1, max_length=100)
    role_title: str | None = Field(default=None, min_length=1, max_length=120)
    status: ProjectStatus | None = None
    started_at: date | None = None
    deadline_at: date | None = None
    progress_percent: int | None = Field(default=None, ge=0, le=100)


class ProjectResponse(BaseModel):
    id: UUID
    user_id: int
    company_name: str
    role_title: str
    status: ProjectStatus
    started_at: date | None = None
    deadline_at: date | None = None
    progress_percent: int
    last_activity_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
