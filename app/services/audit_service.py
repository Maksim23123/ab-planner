from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session

from app.models import ChangeLog


def _serialize_value(value: Any) -> Any:
    """Make ORM values JSON-serializable for the audit trail."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.isoformat()
        return value.astimezone(timezone.utc).isoformat()
    return value


def serialize_model(instance: Any, *, fields: Iterable[str] | None = None) -> dict[str, Any]:
    """Take a shallow snapshot of a model's column values."""
    if instance is None:
        return {}

    allowed = set(fields) if fields is not None else None
    mapper = inspect(instance).mapper

    snapshot: dict[str, Any] = {}
    for column in mapper.column_attrs:
        key = column.key
        if allowed is not None and key not in allowed:
            continue
        snapshot[key] = _serialize_value(getattr(instance, key))
    return snapshot


def record_change(
    db: Session,
    *,
    actor_user_id: int,
    entity: str,
    entity_id: int,
    action: str,
    old_data: dict[str, Any] | None,
    new_data: dict[str, Any] | None,
) -> None:
    """Append a change log entry to the current transaction."""
    db.add(
        ChangeLog(
            actor_user_id=actor_user_id,
            entity=entity,
            entity_id=entity_id,
            action=action,
            old_data=old_data,
            new_data=new_data,
            created_at=datetime.now(timezone.utc),
        )
    )
