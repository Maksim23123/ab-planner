from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Iterable

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Group, Lesson, Room, StudentGroupSelection, Subject, User
from app.services.audit_service import record_change, serialize_model
from app.services import notification_service

LessonModel = Lesson


def _with_relations() -> Iterable:
    """Common relationship loading for consistent API payloads."""
    return (
        joinedload(LessonModel.subject),
        joinedload(LessonModel.room),
        joinedload(LessonModel.group).joinedload(Group.program),
        joinedload(LessonModel.group).joinedload(Group.program_year),
        joinedload(LessonModel.group).joinedload(Group.specialization),
        joinedload(LessonModel.group).joinedload(Group.group_type),
        joinedload(LessonModel.lecturer),
    )


def _validate_time_window(starts_at: datetime, ends_at: datetime) -> None:
    if ends_at <= starts_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ends_at must be after starts_at",
        )


def _ensure_fk(db: Session, model, pk: int | None, label: str) -> None:
    if pk is None:
        return
    exists = db.get(model, pk)
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found")


def _format_dt(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return value
    return str(value)


def _time_window_str(lesson_data: dict[str, Any]) -> str:
    start = lesson_data.get("starts_at")
    end = lesson_data.get("ends_at")
    if start and end:
        return f"{_format_dt(start)} - {_format_dt(end)}"
    if start:
        return _format_dt(start)
    return ""


def _lesson_context(db: Session, lesson_data: dict[str, Any]) -> tuple[str, str]:
    subject = db.get(Subject, lesson_data.get("subject_id"))
    room = db.get(Room, lesson_data.get("room_id"))
    subject_name = subject.name if subject else "Lesson"
    room_label = (
        f"{room.building} {room.number}" if room else f"Room {lesson_data.get('room_id')}"
    )
    return subject_name, room_label


def _lesson_recipients(db: Session, lesson_data: dict[str, Any]) -> list[int]:
    user_ids: set[int] = set()
    lecturer_id = lesson_data.get("lecturer_user_id")
    group_id = lesson_data.get("group_id")
    if lecturer_id:
        user_ids.add(int(lecturer_id))
    if group_id:
        stmt = select(StudentGroupSelection.user_id).where(
            StudentGroupSelection.group_id == group_id
        )
        user_ids.update(db.scalars(stmt).all())
    return list(user_ids)


def _lesson_notification_payload(
    action: str,
    lesson_data: dict[str, Any],
    before: dict[str, Any] | None,
    subject_name: str,
    room_label: str,
) -> dict[str, Any]:
    title_map = {
        "created": "New lesson scheduled",
        "updated": "Lesson updated",
        "deleted": "Lesson canceled",
    }
    title = title_map.get(action, "Lesson update")
    time_window = _time_window_str(lesson_data)
    place = f"{time_window} @ {room_label}" if time_window else room_label

    changes: list[str] = []
    if before:
        for field, label in (
            ("starts_at", "time"),
            ("ends_at", "time"),
            ("room_id", "room"),
            ("status", "status"),
            ("lesson_type", "type"),
        ):
            if before.get(field) != lesson_data.get(field):
                changes.append(label)
    change_text = ", ".join(changes) if changes else "details updated"

    if action == "created":
        body = f"{subject_name} at {place}"
    elif action == "deleted":
        body = f"{subject_name} at {place} was canceled"
    else:
        body = f"{subject_name}: {change_text}. {place}"

    data_payload = {
        "lesson_id": lesson_data.get("id"),
        "group_id": lesson_data.get("group_id"),
        "subject_id": lesson_data.get("subject_id"),
        "room_id": lesson_data.get("room_id"),
        "action": action,
        "starts_at": lesson_data.get("starts_at"),
        "ends_at": lesson_data.get("ends_at"),
        "status": lesson_data.get("status"),
        "lesson_type": lesson_data.get("lesson_type"),
    }
    if before:
        data_payload["previous"] = {
            key: before.get(key)
            for key in ("starts_at", "ends_at", "room_id", "status", "lesson_type")
            if before.get(key) is not None
        }

    return {"title": title, "body": body, "data": data_payload}


def _enqueue_lesson_notifications(
    db: Session,
    *,
    action: str,
    lesson_snapshot: dict[str, Any],
    before_snapshot: dict[str, Any] | None = None,
) -> None:
    recipients = _lesson_recipients(db, lesson_snapshot)
    if not recipients:
        return
    subject_name, room_label = _lesson_context(db, lesson_snapshot)
    payload = _lesson_notification_payload(
        action, lesson_snapshot, before_snapshot, subject_name, room_label
    )
    notification_service.enqueue_notifications(
        db,
        user_ids=recipients,
        payload=payload,
        delivery_status="queued",
        read_status="unread",
        commit=False,
    )


def list_lessons(
    db: Session,
    *,
    group_id: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[LessonModel]:
    stmt = select(LessonModel).options(*_with_relations())
    if group_id is not None:
        stmt = stmt.where(LessonModel.group_id == group_id)
    if date_from is not None:
        stmt = stmt.where(LessonModel.starts_at >= date_from)
    if date_to is not None:
        stmt = stmt.where(LessonModel.starts_at <= date_to)
    return list(db.scalars(stmt).all())


def get_lesson(db: Session, lesson_id: int) -> LessonModel:
    stmt = select(LessonModel).options(*_with_relations()).where(LessonModel.id == lesson_id)
    lesson = db.execute(stmt).scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    return lesson


def create_lesson(db: Session, data: Dict[str, Any], *, actor_user_id: int) -> LessonModel:
    _ensure_fk(db, Subject, data.get("subject_id"), "Subject")
    _ensure_fk(db, User, data.get("lecturer_user_id"), "Lecturer")
    _ensure_fk(db, Room, data.get("room_id"), "Room")
    _ensure_fk(db, Group, data.get("group_id"), "Group")
    _validate_time_window(data["starts_at"], data["ends_at"])

    lesson = LessonModel(**data)
    db.add(lesson)
    db.flush()
    lesson_snapshot = serialize_model(lesson)
    record_change(
        db,
        actor_user_id=actor_user_id,
        entity=LessonModel.__tablename__,
        entity_id=lesson.id,
        action="create",
        old_data=None,
        new_data=lesson_snapshot,
    )
    _enqueue_lesson_notifications(db, action="created", lesson_snapshot=lesson_snapshot)
    db.commit()
    db.refresh(lesson)
    return get_lesson(db, lesson.id)


def create_lesson_series(
    db: Session,
    data: Dict[str, Any],
    *,
    occurrences: int,
    repeat_every_days: int,
    actor_user_id: int,
) -> list[LessonModel]:
    if occurrences < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="occurrences must be at least 1"
        )
    if repeat_every_days < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="repeat_every_days must be at least 1"
        )

    _ensure_fk(db, Subject, data.get("subject_id"), "Subject")
    _ensure_fk(db, User, data.get("lecturer_user_id"), "Lecturer")
    _ensure_fk(db, Room, data.get("room_id"), "Room")
    _ensure_fk(db, Group, data.get("group_id"), "Group")
    _validate_time_window(data["starts_at"], data["ends_at"])

    interval = timedelta(days=repeat_every_days)
    starts_at = data["starts_at"]
    ends_at = data["ends_at"]

    created: list[LessonModel] = []
    for index in range(occurrences):
        offset = interval * index
        occurrence_data = {
            **data,
            "starts_at": starts_at + offset,
            "ends_at": ends_at + offset,
        }
        lesson = LessonModel(**occurrence_data)
        db.add(lesson)
        created.append(lesson)

    db.flush()

    for lesson in created:
        lesson_snapshot = serialize_model(lesson)
        record_change(
            db,
            actor_user_id=actor_user_id,
            entity=LessonModel.__tablename__,
            entity_id=lesson.id,
            action="create",
            old_data=None,
            new_data=lesson_snapshot,
        )
        _enqueue_lesson_notifications(db, action="created", lesson_snapshot=lesson_snapshot)

    db.commit()

    ids = [lesson.id for lesson in created]
    if not ids:
        return []

    stmt = (
        select(LessonModel)
        .options(*_with_relations())
        .where(LessonModel.id.in_(ids))
        .order_by(LessonModel.starts_at, LessonModel.id)
    )
    return list(db.scalars(stmt).all())


def update_lesson(db: Session, lesson_id: int, data: Dict[str, Any], *, actor_user_id: int) -> LessonModel:
    lesson = db.get(LessonModel, lesson_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    _ensure_fk(db, Subject, data.get("subject_id"), "Subject")
    _ensure_fk(db, User, data.get("lecturer_user_id"), "Lecturer")
    _ensure_fk(db, Room, data.get("room_id"), "Room")
    _ensure_fk(db, Group, data.get("group_id"), "Group")

    starts_at = data.get("starts_at", lesson.starts_at)
    ends_at = data.get("ends_at", lesson.ends_at)
    _validate_time_window(starts_at, ends_at)

    before = serialize_model(lesson)
    for field, value in data.items():
        setattr(lesson, field, value)

    db.flush()
    after = serialize_model(lesson)
    record_change(
        db,
        actor_user_id=actor_user_id,
        entity=LessonModel.__tablename__,
        entity_id=lesson.id,
        action="update",
        old_data=before,
        new_data=after,
    )
    _enqueue_lesson_notifications(
        db,
        action="updated",
        lesson_snapshot=after,
        before_snapshot=before,
    )
    db.commit()
    db.refresh(lesson)
    return get_lesson(db, lesson.id)


def delete_lesson(db: Session, lesson_id: int, *, actor_user_id: int) -> None:
    lesson = db.get(LessonModel, lesson_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    before = serialize_model(lesson)
    db.delete(lesson)
    record_change(
        db,
        actor_user_id=actor_user_id,
        entity=LessonModel.__tablename__,
        entity_id=lesson.id,
        action="delete",
        old_data=before,
        new_data=None,
    )
    _enqueue_lesson_notifications(
        db,
        action="deleted",
        lesson_snapshot=before,
        before_snapshot=before,
    )
    db.commit()
