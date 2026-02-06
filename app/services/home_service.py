from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from app.db.repositories.project_repository import list_projects_by_user
from app.db.repositories.routine_repository import list_routine_items_by_user_date
from app.db.repositories.user_repository import get_user_by_pk
from app.schemas.home import (
    CoachStatus,
    HomeProjectItem,
    HomeResponse,
    HomeRoutine,
    HomeRoutineItem,
    HomeUserCard,
)


def _compute_dday(deadline_at: date | None) -> int | None:
    if deadline_at is None:
        return None
    return (date.today() - deadline_at).days


def _relative_time_label(value: datetime | None) -> str | None:
    if value is None:
        return None
    now = datetime.now(tz=UTC)
    target = value if value.tzinfo else value.replace(tzinfo=UTC)
    delta_seconds = int((now - target).total_seconds())
    if delta_seconds < 60:
        return "방금 전"
    if delta_seconds < 3600:
        return f"{delta_seconds // 60}분 전"
    if delta_seconds < 86400:
        return f"{delta_seconds // 3600}시간 전"
    if delta_seconds < 604800:
        return f"{delta_seconds // 86400}일 전"
    return f"{delta_seconds // 604800}주 전"


def get_home_data(db: Session, user_id: int) -> HomeResponse:
    user = get_user_by_pk(db=db, user_pk=user_id)
    if user is None:
        raise ValueError("User not found")

    projects = list_projects_by_user(db=db, user_id=user_id, limit=50, offset=0)
    routines = list_routine_items_by_user_date(db=db, user_id=user_id, routine_date=date.today())

    return HomeResponse(
        userCard=HomeUserCard(
            userId=user.id,
            name=user.name or user.user_id,
            targetRole=user.target_role,
            coachStatus=CoachStatus(user.coach_status),
            avatarUrl=user.avatar_url,
        ),
        projects=[
            HomeProjectItem(
                projectId=project.id,
                companyName=project.company_name,
                roleTitle=project.role_title,
                status=project.status,
                startedAt=project.started_at,
                progressPercent=project.progress_percent,
                deadlineAt=project.deadline_at,
                dDay=_compute_dday(project.deadline_at),
                lastActivityAt=project.last_activity_at,
                lastActivityLabel=_relative_time_label(project.last_activity_at),
            )
            for project in projects
        ],
        routine=HomeRoutine(
            items=[
                HomeRoutineItem(
                    routineItemId=item.id,
                    label=item.label,
                    checked=item.checked,
                    source=item.source,
                )
                for item in routines
            ]
        ),
    )

