from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models import NotificationOutbox


def list_notifications(
    db: Session,
    *,
    user_id: int,
    status: str | None = None,
) -> list[NotificationOutbox]:
    stmt = select(NotificationOutbox).where(NotificationOutbox.user_id == user_id)
    if status is not None:
        stmt = stmt.where(NotificationOutbox.status == status)
    stmt = stmt.order_by(NotificationOutbox.created_at.desc())
    return list(db.scalars(stmt).all())


def get_notification(db: Session, notification_id: int) -> NotificationOutbox:
    record = db.get(NotificationOutbox, notification_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return record


def update_notification(db: Session, notification_id: int, *, status_value: str | None = None) -> NotificationOutbox:
    record = get_notification(db, notification_id)
    if status_value is not None:
        record.status = status_value
    db.commit()
    db.refresh(record)
    return record


def enqueue_notifications(
    db: Session,
    *,
    user_ids: Iterable[int],
    payload: dict,
    status_value: str = "queued",
    commit: bool = False,
) -> list[NotificationOutbox]:
    """Queue notifications for multiple users. Optionally commits the transaction."""
    now = datetime.now(timezone.utc)
    records: list[NotificationOutbox] = []
    for user_id in {uid for uid in user_ids if uid is not None}:
        record = NotificationOutbox(
            user_id=user_id,
            payload=payload,
            status=status_value,
            attempts=0,
            created_at=now,
            sent_at=None,
        )
        db.add(record)
        records.append(record)
    if not records:
        return []

    if commit:
        db.commit()
        for record in records:
            db.refresh(record)
    else:
        db.flush()
    return records


def create_notification(db: Session, *, user_id: int, payload: dict, status_value: str) -> NotificationOutbox:
    created = enqueue_notifications(
        db,
        user_ids=[user_id],
        payload=payload,
        status_value=status_value,
        commit=True,
    )
    return created[0]
