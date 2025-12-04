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
    delivery_status: str | None = None,
    read_status: str | None = None,
) -> list[NotificationOutbox]:
    stmt = select(NotificationOutbox).where(NotificationOutbox.user_id == user_id)
    if delivery_status is not None:
        stmt = stmt.where(NotificationOutbox.delivery_status == delivery_status)
    if read_status is not None:
        stmt = stmt.where(NotificationOutbox.read_status == read_status)
    stmt = stmt.order_by(NotificationOutbox.created_at.desc())
    return list(db.scalars(stmt).all())


def get_notification(db: Session, notification_id: int) -> NotificationOutbox:
    record = db.get(NotificationOutbox, notification_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return record


def update_notification(
    db: Session,
    notification_id: int,
    *,
    read: bool | None = None,
    read_status_value: str | None = None,
) -> NotificationOutbox:
    record = get_notification(db, notification_id)
    target_read_status: str | None = None
    if read is not None:
        target_read_status = "read" if read else "unread"
    elif read_status_value is not None:
        target_read_status = read_status_value

    if target_read_status is not None:
        record.read_status = target_read_status
        record.read_at = datetime.now(timezone.utc) if target_read_status == "read" else None

    db.commit()
    db.refresh(record)
    return record


def enqueue_notifications(
    db: Session,
    *,
    user_ids: Iterable[int],
    payload: dict,
    delivery_status: str = "queued",
    read_status: str = "unread",
    commit: bool = False,
) -> list[NotificationOutbox]:
    """Queue notifications for multiple users. Optionally commits the transaction."""
    now = datetime.now(timezone.utc)
    records: list[NotificationOutbox] = []
    for user_id in {uid for uid in user_ids if uid is not None}:
        record = NotificationOutbox(
            user_id=user_id,
            payload=payload,
            delivery_status=delivery_status,
            read_status=read_status,
            read_at=now if read_status == "read" else None,
            attempts=0,
            created_at=now,
            last_attempt_at=None,
            last_error=None,
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


def create_notification(
    db: Session,
    *,
    user_id: int,
    payload: dict,
    delivery_status: str = "queued",
    read: bool | None = None,
    read_status: str | None = None,
) -> NotificationOutbox:
    target_read_status = read_status
    if target_read_status is None and read is not None:
        target_read_status = "read" if read else "unread"
    target_read_status = target_read_status or "unread"
    created = enqueue_notifications(
        db,
        user_ids=[user_id],
        payload=payload,
        delivery_status=delivery_status,
        read_status=target_read_status,
        commit=True,
    )
    return created[0]
