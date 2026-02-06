import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.entities.project import Resume, ResumeParagraph


def get_resume_by_id(
    db: Session,
    resume_id: uuid.UUID,
    project_id: uuid.UUID,
    user_id: int,
) -> Resume | None:
    stmt = select(Resume).where(
        Resume.id == resume_id,
        Resume.project_id == project_id,
        Resume.user_id == user_id,
    )
    return db.execute(stmt).scalars().first()


def get_latest_resume_by_project(
    db: Session,
    project_id: uuid.UUID,
    user_id: int,
) -> Resume | None:
    stmt = (
        select(Resume)
        .where(Resume.project_id == project_id, Resume.user_id == user_id)
        .order_by(Resume.updated_at.desc())
        .limit(1)
    )
    return db.execute(stmt).scalars().first()


def get_paragraph_by_id(
    db: Session,
    paragraph_id: uuid.UUID,
    resume_id: uuid.UUID,
    project_id: uuid.UUID,
    user_id: int,
) -> ResumeParagraph | None:
    stmt = select(ResumeParagraph).where(
        ResumeParagraph.id == paragraph_id,
        ResumeParagraph.resume_id == resume_id,
        ResumeParagraph.project_id == project_id,
        ResumeParagraph.user_id == user_id,
    )
    return db.execute(stmt).scalars().first()


def update_paragraph_text(db: Session, paragraph: ResumeParagraph, text: str) -> ResumeParagraph:
    paragraph.text = text
    db.add(paragraph)
    db.commit()
    db.refresh(paragraph)
    return paragraph


def complete_paragraph(db: Session, paragraph: ResumeParagraph) -> ResumeParagraph:
    paragraph.status = "COMPLETED"
    db.add(paragraph)
    db.commit()
    db.refresh(paragraph)
    return paragraph


def count_completed_paragraphs(db: Session, resume_id: uuid.UUID) -> int:
    stmt = select(func.count(ResumeParagraph.id)).where(
        ResumeParagraph.resume_id == resume_id,
        ResumeParagraph.status == "COMPLETED",
    )
    return int(db.execute(stmt).scalar_one())


def count_total_paragraphs(db: Session, resume_id: uuid.UUID) -> int:
    stmt = select(func.count(ResumeParagraph.id)).where(ResumeParagraph.resume_id == resume_id)
    return int(db.execute(stmt).scalar_one())

