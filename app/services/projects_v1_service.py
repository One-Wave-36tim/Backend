import re
import uuid
from datetime import date
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.db.repositories.job_posting_repository import create_job_posting
from app.db.repositories.portfolio_repository import create_portfolio, get_portfolios_by_ids
from app.db.repositories.project_portfolio_repository import (
    create_portfolio_item,
    create_project_portfolio_link,
    get_portfolio_item_by_id,
    list_project_portfolios,
    set_representative_portfolio,
)
from app.db.repositories.project_repository import create_project, get_project_by_id
from app.db.repositories.resume_repository import get_latest_resume_by_project
from app.db.repositories.routine_repository import get_routine_item, update_routine_checked
from app.db.repositories.session_repository import (
    count_sessions_by_project_type,
    get_latest_session_by_project_type,
)
from app.schemas.projects_v1 import (
    DashboardMockInterview,
    DashboardPortfolioItem,
    DashboardPrepStage,
    DashboardProjectInfo,
    DashboardResume,
    DashboardSimpleState,
    DashboardStep,
    PortfolioCreateRequest,
    PortfolioCreateResponse,
    ProjectCreateV1Request,
    ProjectCreateV1Response,
    ProjectDashboardResponse,
    ProjectPortfolioPatchResponse,
    RoutineToggleResponse,
)

_YYYY_MM_PATTERN = re.compile(r"^\d{4}-\d{2}$")


def _parse_yyyy_mm(value: str | None) -> date | None:
    if value is None or value == "":
        return None
    if not _YYYY_MM_PATTERN.match(value):
        raise ValueError("periodStart/periodEnd must be YYYY-MM format")
    year = int(value[:4])
    month = int(value[5:7])
    if month < 1 or month > 12:
        raise ValueError("month must be between 01 and 12")
    return date(year, month, 1)


def _compute_dday(deadline_at: date | None) -> int | None:
    if deadline_at is None:
        return None
    return (date.today() - deadline_at).days


def _extract_mock_score(result_json: dict | None) -> float | None:
    if not result_json:
        return None
    overall = result_json.get("overall")
    if isinstance(overall, dict):
        value = overall.get("score")
        if isinstance(value, (int, float)):
            return float(value)
    value = result_json.get("average_score")
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _format_period(start: date | None, end: date | None) -> str | None:
    if start is None and end is None:
        return None
    left = f"{start.year}.{start.month:02d}" if start else "?"
    right = f"{end.year}.{end.month:02d}" if end else "현재"
    return f"{left} - {right}"


def _extract_filename_from_url(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlparse(value)
    if not parsed.path:
        return None
    candidate = parsed.path.rsplit("/", 1)[-1]
    return candidate or None


def create_project_v1(
    db: Session,
    user_id: int,
    payload: ProjectCreateV1Request,
) -> ProjectCreateV1Response:
    project = create_project(
        db=db,
        user_id=user_id,
        company_name=payload.companyName,
        role_title=payload.roleTitle,
        started_at=date.today(),
        deadline_at=payload.deadlineAt,
    )
    create_job_posting(
        db=db,
        project_id=project.id,
        user_id=user_id,
        url=payload.jobPostingUrl,
        text="",
    )
    portfolio_ids: list[int] = []
    representative_portfolio_id: int | None = None
    portfolio = payload.portfolio
    if portfolio is not None:
        source_rows: list[tuple[str, str | None, str | None]] = []
        if portfolio.notionUrl:
            source_rows.append(("notion", portfolio.notionUrl, None))
        if portfolio.blogUrl:
            source_rows.append(("blog", portfolio.blogUrl, None))
        if portfolio.pdfFileUrl:
            source_rows.append(
                ("pdf", portfolio.pdfFileUrl, _extract_filename_from_url(portfolio.pdfFileUrl))
            )

        common_meta = {
            "representativeDescription": portfolio.representativeDescription,
            "developerMode": portfolio.developerMode,
            "githubRepoUrl": portfolio.githubRepoUrl,
        }
        has_common_meta = any(v not in (None, "", False) for v in common_meta.values())
        if has_common_meta and not source_rows:
            source_rows.append(("blog", None, None))

        for idx, (source_type, source_url, original_filename) in enumerate(source_rows):
            row = create_portfolio(
                db=db,
                user_id=user_id,
                project_id=project.id,
                source_type=source_type,
                source_url=source_url,
                original_filename=original_filename,
                extracted_text="",
                is_representative=idx == 0,
                meta=common_meta,
            )
            portfolio_ids.append(row.id)
            if idx == 0:
                representative_portfolio_id = row.id

    return ProjectCreateV1Response(
        projectId=project.id,
        status=project.status,
        portfolioIds=portfolio_ids,
        representativePortfolioId=representative_portfolio_id,
    )


def pick_blog_portfolio_ids(
    db: Session,
    user_id: int,
    portfolio_ids: list[int],
) -> list[int]:
    rows = get_portfolios_by_ids(db=db, user_id=user_id, portfolio_ids=portfolio_ids)
    return [row.id for row in rows if row.source_type == "blog" and row.source_url]


def toggle_routine_item(
    db: Session,
    user_id: int,
    routine_item_id: uuid.UUID,
    checked: bool,
) -> RoutineToggleResponse:
    item = get_routine_item(db=db, user_id=user_id, routine_item_id=routine_item_id)
    if item is None:
        raise NotFoundError("Routine item not found")
    item = update_routine_checked(db=db, routine=item, checked=checked)
    return RoutineToggleResponse(
        routineItemId=item.id,
        checked=item.checked,
        updatedAt=item.updated_at,
    )


def create_portfolio_item_v1(
    db: Session,
    user_id: int,
    payload: PortfolioCreateRequest,
) -> PortfolioCreateResponse:
    row = create_portfolio_item(
        db=db,
        user_id=user_id,
        title=payload.title,
        tech_stack=payload.techStack,
        period_start=_parse_yyyy_mm(payload.periodStart),
        period_end=_parse_yyyy_mm(payload.periodEnd),
        summary=None,
    )
    if payload.projectId is not None:
        create_project_portfolio_link(
            db=db,
            project_id=payload.projectId,
            portfolio_item_id=row.id,
        )
    return PortfolioCreateResponse(portfolioId=row.id, linkedProjectId=payload.projectId)


def patch_project_portfolio(
    db: Session,
    user_id: int,
    project_id: uuid.UUID,
    portfolio_id: uuid.UUID,
    is_representative: bool,
) -> ProjectPortfolioPatchResponse:
    project = get_project_by_id(db=db, project_id=project_id, user_id=user_id)
    if project is None:
        raise NotFoundError("Project not found")
    portfolio_item = get_portfolio_item_by_id(
        db=db,
        user_id=user_id,
        portfolio_item_id=portfolio_id,
    )
    if portfolio_item is None:
        raise NotFoundError("Portfolio not found")

    row = set_representative_portfolio(
        db=db,
        project_id=project_id,
        portfolio_item_id=portfolio_id,
        is_representative=is_representative,
    )
    return ProjectPortfolioPatchResponse(
        projectId=project_id,
        portfolioId=portfolio_id,
        isRepresentative=row.is_representative,
        updatedAt=row.updated_at,
    )


def get_project_dashboard(
    db: Session,
    user_id: int,
    project_id: uuid.UUID,
) -> ProjectDashboardResponse:
    project = get_project_by_id(db=db, project_id=project_id, user_id=user_id)
    if project is None:
        raise NotFoundError("Project not found")

    resume = get_latest_resume_by_project(db=db, project_id=project.id, user_id=user_id)
    latest_mock = get_latest_session_by_project_type(
        db=db,
        user_id=user_id,
        project_id=project.id,
        session_type="MOCK_INTERVIEW",
    )
    mock_count = count_sessions_by_project_type(
        db=db,
        user_id=user_id,
        project_id=project.id,
        session_type="MOCK_INTERVIEW",
    )
    latest_sim = get_latest_session_by_project_type(
        db=db,
        user_id=user_id,
        project_id=project.id,
        session_type="JOB_SIMULATION",
    )
    project_rows = list_project_portfolios(db=db, project_id=project.id, user_id=user_id)

    resume_completed = bool(resume and resume.status == "COMPLETED")
    mock_completed = bool(latest_mock and latest_mock.status == "COMPLETED")
    sim_completed = bool(latest_sim and latest_sim.status == "COMPLETED")
    final_feedback_completed = mock_completed and sim_completed

    steps = [
        DashboardStep(key="resume", label="자소서", completed=resume_completed),
        DashboardStep(key="mockInterview", label="모의면접", completed=mock_completed),
        DashboardStep(key="simulation", label="직무 시뮬레이션", completed=sim_completed),
        DashboardStep(
            key="finalFeedback",
            label="최종 피드백",
            completed=final_feedback_completed,
        ),
    ]
    completed_count = sum(1 for step in steps if step.completed)
    stage_status = "DONE" if completed_count == len(steps) else "IN_PROGRESS"

    return ProjectDashboardResponse(
        projectInfo=DashboardProjectInfo(
            projectId=project.id,
            companyName=project.company_name,
            roleTitle=project.role_title,
            createdAt=project.created_at.date(),
            deadlineAt=project.deadline_at,
            dDay=_compute_dday(project.deadline_at),
        ),
        prepStage=DashboardPrepStage(status=stage_status, steps=steps),
        resume=DashboardResume(
            resumeId=resume.id if resume else None,
            title=resume.title if resume else None,
            exists=resume is not None,
            lastEditedAt=resume.updated_at if resume else None,
        ),
        mockInterview=DashboardMockInterview(
            latestSessionId=latest_mock.id if latest_mock else None,
            latestTitle="모의면접 결과" if latest_mock else None,
            latestScore=_extract_mock_score(latest_mock.result_json if latest_mock else None),
            sessionCount=mock_count,
        ),
        portfolios=[
            DashboardPortfolioItem(
                portfolioId=portfolio_item.id,
                title=portfolio_item.title,
                techStack=portfolio_item.tech_stack or [],
                period=_format_period(portfolio_item.period_start, portfolio_item.period_end),
                roleType=link.role_type,
                isRepresentative=link.is_representative,
            )
            for link, portfolio_item in project_rows
        ],
        simulation=DashboardSimpleState(
            available=True,
            completed=sim_completed,
        ),
        finalFeedback=DashboardSimpleState(
            available=True,
            completed=final_feedback_completed,
        ),
    )
