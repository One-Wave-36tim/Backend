import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.entities.project import RoutineItem


def list_routine_items_by_user_date(
    db: Session,
    user_id: int,
    routine_date: date,
) -> list[RoutineItem]:
    stmt = (
        select(RoutineItem)
        .where(RoutineItem.user_id == user_id, RoutineItem.routine_date == routine_date)
        .order_by(RoutineItem.created_at.asc())
    )
    return list(db.execute(stmt).scalars().all())


def get_routine_item(
    db: Session,
    user_id: int,
    routine_item_id: uuid.UUID,
) -> RoutineItem | None:
    stmt = select(RoutineItem).where(
        RoutineItem.id == routine_item_id,
        RoutineItem.user_id == user_id,
    )
    return db.execute(stmt).scalars().first()


def update_routine_checked(
    db: Session,
    routine: RoutineItem,
    checked: bool,
) -> RoutineItem:
    routine.checked = checked
    db.add(routine)
    db.commit()
    db.refresh(routine)
    return routine
