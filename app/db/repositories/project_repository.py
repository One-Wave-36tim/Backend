import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.entities.project import Project


def create_project(
    db: Session,
    user_id: int,
    company_name: str,
    role_title: str,
    started_at,
    deadline_at,
) -> Project:
    project = Project(
        user_id=user_id,
        company_name=company_name,
        role_title=role_title,
        started_at=started_at,
        deadline_at=deadline_at,
        status="IN_PROGRESS",
        progress_percent=0,
        last_activity_at=datetime.now(tz=UTC),
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_project_by_id(db: Session, project_id: uuid.UUID, user_id: int) -> Project | None:
    stmt = select(Project).where(Project.id == project_id, Project.user_id == user_id)
    return db.execute(stmt).scalars().first()


def list_projects_by_user(
    db: Session,
    user_id: int,
    limit: int = 50,
    offset: int = 0,
) -> list[Project]:
    stmt = (
        select(Project)
        .where(Project.user_id == user_id)
        .order_by(Project.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(stmt).scalars().all())


def count_projects_by_user(db: Session, user_id: int) -> int:
    stmt = select(func.count(Project.id)).where(Project.user_id == user_id)
    return int(db.execute(stmt).scalar_one())


def get_latest_project_by_user(db: Session, user_id: int) -> Project | None:
    stmt = (
        select(Project)
        .where(Project.user_id == user_id)
        .order_by(Project.created_at.desc())
        .limit(1)
    )
    return db.execute(stmt).scalars().first()


def update_project(db: Session, project: Project) -> Project:
    project.last_activity_at = datetime.now(tz=UTC)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project
