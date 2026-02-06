from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectPortfolioInput(BaseModel):
    notionUrl: str | None = Field(default=None, description="노션 포트폴리오 링크")
    blogUrl: str | None = Field(default=None, description="기술 블로그 링크")
    pdfFileUrl: str | None = Field(default=None, description="업로드된 PDF 파일 URL")
    representativeDescription: str | None = Field(
        default=None,
        description="대표 포트폴리오 설명(기술 스택, 구현 기능, 기여도)",
    )
    developerMode: bool = Field(default=False, description="개발자 모드 활성화 여부")
    githubRepoUrl: str | None = Field(default=None, description="GitHub 저장소 링크")


class ProjectCreateV1Request(BaseModel):
    companyName: str = Field(min_length=1, max_length=100)
    roleTitle: str = Field(min_length=1, max_length=120)
    jobPostingUrl: str | None = None
    deadlineAt: date | None = None
    portfolio: ProjectPortfolioInput | None = Field(
        default=None,
        description="프로젝트 생성 시 함께 등록할 포트폴리오 입력값",
    )


class ProjectCreateV1Response(BaseModel):
    projectId: UUID
    status: str
    portfolioIds: list[int] = Field(default_factory=list)
    representativePortfolioId: int | None = None


class RoutineToggleRequest(BaseModel):
    checked: bool


class RoutineToggleResponse(BaseModel):
    routineItemId: UUID
    checked: bool
    updatedAt: datetime


class DashboardProjectInfo(BaseModel):
    projectId: UUID
    companyName: str
    roleTitle: str
    createdAt: date
    deadlineAt: date | None = None
    dDay: int | None = None


class DashboardStep(BaseModel):
    key: str
    label: str
    completed: bool


class DashboardPrepStage(BaseModel):
    status: str
    steps: list[DashboardStep]


class DashboardResume(BaseModel):
    resumeId: UUID | None = None
    title: str | None = None
    exists: bool
    lastEditedAt: datetime | None = None


class DashboardMockInterview(BaseModel):
    latestSessionId: UUID | None = None
    latestTitle: str | None = None
    latestScore: float | None = None
    sessionCount: int


class DashboardMyProjectItem(BaseModel):
    myProjectId: UUID
    title: str
    techStack: list[str] = Field(default_factory=list)
    period: str | None = None
    roleType: str
    isRepresentative: bool


class DashboardSimpleState(BaseModel):
    available: bool
    completed: bool


class ProjectDashboardResponse(BaseModel):
    projectInfo: DashboardProjectInfo
    prepStage: DashboardPrepStage
    resume: DashboardResume
    mockInterview: DashboardMockInterview
    myProjects: list[DashboardMyProjectItem]
    simulation: DashboardSimpleState
    finalFeedback: DashboardSimpleState


class MyProjectCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    techStack: list[str] = Field(default_factory=list)
    periodStart: str | None = Field(
        default=None, description="YYYY-MM 형식. 예: 2025-01"
    )
    periodEnd: str | None = Field(
        default=None, description="YYYY-MM 형식. 예: 2025-02"
    )
    projectId: UUID | None = None


class MyProjectCreateResponse(BaseModel):
    myProjectId: UUID
    linkedProjectId: UUID | None = None


class ProjectMyProjectPatchRequest(BaseModel):
    isRepresentative: bool


class ProjectMyProjectPatchResponse(BaseModel):
    projectId: UUID
    myProjectId: UUID
    isRepresentative: bool
    updatedAt: datetime
