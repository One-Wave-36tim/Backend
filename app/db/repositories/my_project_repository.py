import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.entities.project import MyProject, ProjectMyProject


def create_my_project(
    db: Session,
    user_id: int,
    title: str,
    tech_stack: list[str] | None,
    period_start: date | None,
    period_end: date | None,
    summary: str | None = None,
) -> MyProject:
    row = MyProject(
        user_id=user_id,
        title=title,
        tech_stack=tech_stack,
        period_start=period_start,
        period_end=period_end,
        summary=summary,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_my_project_by_id(db: Session, user_id: int, my_project_id: uuid.UUID) -> MyProject | None:
    stmt = select(MyProject).where(MyProject.id == my_project_id, MyProject.user_id == user_id)
    return db.execute(stmt).scalars().first()


def get_project_my_project_link(
    db: Session,
    project_id: uuid.UUID,
    my_project_id: uuid.UUID,
) -> ProjectMyProject | None:
    stmt = select(ProjectMyProject).where(
        ProjectMyProject.project_id == project_id,
        ProjectMyProject.my_project_id == my_project_id,
    )
    return db.execute(stmt).scalars().first()


def create_project_my_project_link(
    db: Session,
    project_id: uuid.UUID,
    my_project_id: uuid.UUID,
    role_type: str = "SUB",
    is_representative: bool = False,
) -> ProjectMyProject:
    row = ProjectMyProject(
        project_id=project_id,
        my_project_id=my_project_id,
        role_type=role_type,
        is_representative=is_representative,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_project_my_projects(
    db: Session,
    project_id: uuid.UUID,
    user_id: int,
) -> list[tuple[ProjectMyProject, MyProject]]:
    stmt = (
        select(ProjectMyProject, MyProject)
        .join(MyProject, MyProject.id == ProjectMyProject.my_project_id)
        .where(ProjectMyProject.project_id == project_id, MyProject.user_id == user_id)
        .order_by(ProjectMyProject.created_at.asc())
    )
    return list(db.execute(stmt).all())


def set_representative(
    db: Session,
    project_id: uuid.UUID,
    my_project_id: uuid.UUID,
    is_representative: bool,
) -> ProjectMyProject:
    target = get_project_my_project_link(db=db, project_id=project_id, my_project_id=my_project_id)
    if target is None:
        target = create_project_my_project_link(
            db=db,
            project_id=project_id,
            my_project_id=my_project_id,
            is_representative=is_representative,
        )
        if not is_representative:
            return target

    if is_representative:
        stmt = select(ProjectMyProject).where(ProjectMyProject.project_id == project_id)
        rows = list(db.execute(stmt).scalars().all())
        for row in rows:
            row.is_representative = row.my_project_id == my_project_id
            db.add(row)
        db.commit()
    else:
        target.is_representative = False
        db.add(target)
        db.commit()

    db.refresh(target)
    return target

