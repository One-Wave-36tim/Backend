import uuid

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.db.entities.project import Project
from app.db.repositories.project_repository import (
    count_projects_by_user,
    create_project,
    get_project_by_id,
    list_projects_by_user,
    update_project,
)
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectResponse,
    ProjectStatus,
    ProjectUpdateRequest,
)


def _to_response(project: Project) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        user_id=project.user_id,
        company_name=project.company_name,
        role_title=project.role_title,
        status=ProjectStatus(project.status),
        started_at=project.started_at,
        deadline_at=project.deadline_at,
        progress_percent=project.progress_percent,
        last_activity_at=project.last_activity_at,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def create_user_project(
    db: Session, user_id: int, payload: ProjectCreateRequest
) -> ProjectResponse:
    project = create_project(
        db=db,
        user_id=user_id,
        company_name=payload.company_name,
        role_title=payload.role_title,
        started_at=payload.started_at,
        deadline_at=payload.deadline_at,
    )
    return _to_response(project)


def list_user_projects(db: Session, user_id: int, limit: int, offset: int) -> ProjectListResponse:
    projects = list_projects_by_user(db=db, user_id=user_id, limit=limit, offset=offset)
    total = count_projects_by_user(db=db, user_id=user_id)
    return ProjectListResponse(items=[_to_response(project) for project in projects], total=total)


def get_user_project(db: Session, user_id: int, project_id: uuid.UUID) -> ProjectResponse:
    project = get_project_by_id(db=db, project_id=project_id, user_id=user_id)
    if not project:
        raise NotFoundError("Project not found")
    return _to_response(project)


def patch_user_project(
    db: Session,
    user_id: int,
    project_id: uuid.UUID,
    payload: ProjectUpdateRequest,
) -> ProjectResponse:
    project = get_project_by_id(db=db, project_id=project_id, user_id=user_id)
    if not project:
        raise NotFoundError("Project not found")

    if payload.company_name is not None:
        project.company_name = payload.company_name
    if payload.role_title is not None:
        project.role_title = payload.role_title
    if payload.status is not None:
        project.status = payload.status.value
    if payload.started_at is not None:
        project.started_at = payload.started_at
    if payload.deadline_at is not None:
        project.deadline_at = payload.deadline_at
    if payload.progress_percent is not None:
        project.progress_percent = payload.progress_percent

    updated = update_project(db=db, project=project)
    return _to_response(updated)
