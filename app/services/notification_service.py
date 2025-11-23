from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

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
