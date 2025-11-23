from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException

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


def create_notification(db: Session, *, user_id: int, payload: dict, status_value: str) -> NotificationOutbox:
    record = NotificationOutbox(
        user_id=user_id,
        payload=payload,
        status=status_value,
        attempts=0,
        created_at=datetime.now(timezone.utc),
        sent_at=None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
