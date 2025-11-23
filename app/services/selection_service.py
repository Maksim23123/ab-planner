from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from app.models import Group, StudentGroupSelection, User


def list_selections(db: Session, *, user_id: int) -> list[StudentGroupSelection]:
    stmt = (
        select(StudentGroupSelection)
        .where(StudentGroupSelection.user_id == user_id)
        .order_by(StudentGroupSelection.selected_at.desc())
    )
    return list(db.scalars(stmt).all())


def create_selection(db: Session, *, user_id: int, group_id: int) -> StudentGroupSelection:
    if db.get(Group, group_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    if db.get(User, user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Replace previous selection for the user
    db.execute(delete(StudentGroupSelection).where(StudentGroupSelection.user_id == user_id))
    selection = StudentGroupSelection(
        user_id=user_id,
        group_id=group_id,
        selected_at=datetime.now(timezone.utc),
    )
    db.add(selection)
    db.commit()
    db.refresh(selection)
    return selection


def delete_selection(db: Session, *, user_id: int) -> None:
    db.execute(delete(StudentGroupSelection).where(StudentGroupSelection.user_id == user_id))
    db.commit()
