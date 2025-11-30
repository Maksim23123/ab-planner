from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Group, StudentGroupSelection, User
from app.services.audit_service import record_change, serialize_model


def list_selections(db: Session, *, user_id: int) -> list[StudentGroupSelection]:
    stmt = (
        select(StudentGroupSelection)
        .where(StudentGroupSelection.user_id == user_id)
        .order_by(StudentGroupSelection.selected_at.desc())
    )
    return list(db.scalars(stmt).all())


def create_selection(
    db: Session, *, user_id: int, group_id: int, actor_user_id: int
) -> StudentGroupSelection:
    if db.get(Group, group_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    if db.get(User, user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    existing = db.execute(
        select(StudentGroupSelection).where(StudentGroupSelection.user_id == user_id)
    ).scalar_one_or_none()
    old_snapshot = serialize_model(existing) if existing else None

    db.execute(delete(StudentGroupSelection).where(StudentGroupSelection.user_id == user_id))
    selection = StudentGroupSelection(
        user_id=user_id,
        group_id=group_id,
        selected_at=datetime.now(timezone.utc),
    )
    db.add(selection)
    db.flush()

    record_change(
        db,
        actor_user_id=actor_user_id,
        entity=StudentGroupSelection.__tablename__,
        entity_id=selection.id,
        action="update" if existing else "create",
        old_data=old_snapshot,
        new_data=serialize_model(selection),
    )

    db.commit()
    db.refresh(selection)
    return selection


def delete_selection(db: Session, *, user_id: int, actor_user_id: int) -> None:
    existing = db.execute(
        select(StudentGroupSelection).where(StudentGroupSelection.user_id == user_id)
    ).scalar_one_or_none()
    db.execute(delete(StudentGroupSelection).where(StudentGroupSelection.user_id == user_id))
    if existing:
        record_change(
            db,
            actor_user_id=actor_user_id,
            entity=StudentGroupSelection.__tablename__,
            entity_id=existing.id,
            action="delete",
            old_data=serialize_model(existing),
            new_data=None,
        )
    db.commit()
