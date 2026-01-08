from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models import Group, NotificationOutbox, StudentGroupSelection, User


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


def broadcast_group_notification(
    db: Session,
    *,
    group_ids: list[int],
    title: str,
    body: str,
    data: dict | None = None,
) -> dict:
    normalized_group_ids = sorted({int(group_id) for group_id in group_ids if group_id is not None})
    if not normalized_group_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="group_ids must include at least one group",
        )

    existing_ids = set(
        db.scalars(select(Group.id).where(Group.id.in_(normalized_group_ids))).all()
    )
    missing = [group_id for group_id in normalized_group_ids if group_id not in existing_ids]
    if missing:
        missing_str = ", ".join(str(group_id) for group_id in missing)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group not found: {missing_str}",
        )

    user_ids = db.scalars(
        select(StudentGroupSelection.user_id)
        .where(StudentGroupSelection.group_id.in_(normalized_group_ids))
        .distinct()
    ).all()
    unique_user_ids = sorted({user_id for user_id in user_ids if user_id is not None})

    payload_data = dict(data or {})
    payload_data.setdefault("group_ids", normalized_group_ids)
    payload = {"title": title, "body": body, "data": payload_data}
    records = enqueue_notifications(
        db,
        user_ids=unique_user_ids,
        payload=payload,
        delivery_status="queued",
        read_status="unread",
        commit=False,
    )
    if records:
        db.commit()

    return {
        "group_ids": normalized_group_ids,
        "user_count": len(unique_user_ids),
        "notification_count": len(records),
    }


def broadcast_all_notification(
    db: Session,
    *,
    title: str,
    body: str,
    data: dict | None = None,
) -> dict:
    user_ids = db.scalars(select(User.id)).all()
    unique_user_ids = sorted({user_id for user_id in user_ids if user_id is not None})

    payload_data = dict(data or {})
    payload_data.setdefault("audience", "all")
    payload = {"title": title, "body": body, "data": payload_data}
    records = enqueue_notifications(
        db,
        user_ids=unique_user_ids,
        payload=payload,
        delivery_status="queued",
        read_status="unread",
        commit=False,
    )
    if records:
        db.commit()

    return {
        "user_count": len(unique_user_ids),
        "notification_count": len(records),
    }
