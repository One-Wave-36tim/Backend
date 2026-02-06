from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import CurrentUserId
from app.core.errors import NotFoundError
from app.db.session import get_db
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdateRequest,
)
from app.services.project_service import (
    create_user_project,
    get_user_project,
    list_user_projects,
    patch_user_project,
)

router = APIRouter(prefix="/v2/projects", tags=["projects-v2"])


@router.post("", response_model=ProjectResponse)
def create_project_endpoint(
    payload: ProjectCreateRequest,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> ProjectResponse:
    return create_user_project(db=db, user_id=user_id, payload=payload)


@router.get("", response_model=ProjectListResponse)
def list_projects_endpoint(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> ProjectListResponse:
    return list_user_projects(db=db, user_id=user_id, limit=limit, offset=offset)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project_endpoint(
    project_id: UUID,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> ProjectResponse:
    try:
        return get_user_project(db=db, user_id=user_id, project_id=project_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{project_id}", response_model=ProjectResponse)
def patch_project_endpoint(
    project_id: UUID,
    payload: ProjectUpdateRequest,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> ProjectResponse:
    try:
        return patch_user_project(
            db=db,
            user_id=user_id,
            project_id=project_id,
            payload=payload,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
