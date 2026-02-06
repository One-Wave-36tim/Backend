import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.entities.session_v2 import SessionTurn, UnifiedSession


def create_session(
    db: Session,
    project_id: uuid.UUID,
    user_id: int,
    session_type: str,
    total_items: int | None,
    meta: dict | None,
) -> UnifiedSession:
    session = UnifiedSession(
        project_id=project_id,
        user_id=user_id,
        session_type=session_type,
        status="IN_PROGRESS",
        total_items=total_items,
        current_index=1,
        started_at=datetime.now(tz=UTC),
        meta=meta,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session_by_id(db: Session, session_id: uuid.UUID, user_id: int) -> UnifiedSession | None:
    stmt = select(UnifiedSession).where(
        UnifiedSession.id == session_id, UnifiedSession.user_id == user_id
    )
    return db.execute(stmt).scalars().first()


def create_turn(
    db: Session,
    session: UnifiedSession,
    role: str,
    speaker: str | None,
    prompt: str | None,
    user_answer: str | None,
    message: str | None,
    intent: str | None,
    feedback: str | None,
    score: float | None,
    score_delta: dict | None,
    meta: dict | None,
    turn_index: int,
) -> SessionTurn:
    turn = SessionTurn(
        session_id=session.id,
        project_id=session.project_id,
        user_id=session.user_id,
        turn_index=turn_index,
        role=role,
        speaker=speaker,
        prompt=prompt,
        user_answer=user_answer,
        message=message,
        intent=intent,
        feedback=feedback,
        score=score,
        score_delta=score_delta,
        meta=meta,
    )
    db.add(turn)
    db.commit()
    db.refresh(turn)
    return turn


def get_next_turn_index(db: Session, session_id: uuid.UUID) -> int:
    stmt = select(func.max(SessionTurn.turn_index)).where(SessionTurn.session_id == session_id)
    last_turn = db.execute(stmt).scalar()
    return int(last_turn or 0) + 1


def list_turns_by_session(
    db: Session,
    session_id: uuid.UUID,
    limit: int | None = None,
    desc: bool = False,
) -> list[SessionTurn]:
    order_column = SessionTurn.turn_index.desc() if desc else SessionTurn.turn_index.asc()
    stmt = select(SessionTurn).where(SessionTurn.session_id == session_id).order_by(order_column)
    if limit is not None:
        stmt = stmt.limit(limit)
    return list(db.execute(stmt).scalars().all())


def update_session(db: Session, session: UnifiedSession) -> UnifiedSession:
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def list_sessions_by_project_type(
    db: Session,
    user_id: int,
    project_id: uuid.UUID,
    session_type: str,
    limit: int = 20,
) -> list[UnifiedSession]:
    stmt = (
        select(UnifiedSession)
        .where(
            UnifiedSession.user_id == user_id,
            UnifiedSession.project_id == project_id,
            UnifiedSession.session_type == session_type,
        )
        .order_by(UnifiedSession.created_at.desc())
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())


def get_latest_session_by_project_type(
    db: Session,
    user_id: int,
    project_id: uuid.UUID,
    session_type: str,
) -> UnifiedSession | None:
    rows = list_sessions_by_project_type(
        db=db,
        user_id=user_id,
        project_id=project_id,
        session_type=session_type,
        limit=1,
    )
    return rows[0] if rows else None


def count_sessions_by_project_type(
    db: Session,
    user_id: int,
    project_id: uuid.UUID,
    session_type: str,
) -> int:
    stmt = select(func.count(UnifiedSession.id)).where(
        UnifiedSession.user_id == user_id,
        UnifiedSession.project_id == project_id,
        UnifiedSession.session_type == session_type,
    )
    return int(db.execute(stmt).scalar_one())


def list_sessions_by_user_type(
    db: Session,
    user_id: int,
    session_type: str,
    limit: int = 20,
) -> list[UnifiedSession]:
    stmt = (
        select(UnifiedSession)
        .where(UnifiedSession.user_id == user_id, UnifiedSession.session_type == session_type)
        .order_by(UnifiedSession.created_at.desc())
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())
