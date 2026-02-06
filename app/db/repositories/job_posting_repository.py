import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.entities.project import ProjectJobPosting


def create_job_posting(
    db: Session,
    project_id: uuid.UUID,
    user_id: int,
    url: str | None,
    text: str = "",
    extracted: dict | None = None,
) -> ProjectJobPosting:
    posting = ProjectJobPosting(
        project_id=project_id,
        user_id=user_id,
        url=url,
        text=text,
        extracted=extracted,
    )
    db.add(posting)
    db.commit()
    db.refresh(posting)
    return posting


def get_latest_job_posting_by_project(
    db: Session,
    project_id: uuid.UUID,
    user_id: int,
) -> ProjectJobPosting | None:
    stmt = (
        select(ProjectJobPosting)
        .where(ProjectJobPosting.project_id == project_id, ProjectJobPosting.user_id == user_id)
        .order_by(ProjectJobPosting.created_at.desc())
        .limit(1)
    )
    return db.execute(stmt).scalars().first()

