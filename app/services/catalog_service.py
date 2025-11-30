from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Room, Subject
from app.services.audit_service import record_change, serialize_model


def _safe_delete(
    db: Session, record, *, detail: str, audit_log: dict[str, Any] | None = None
) -> None:
    try:
        db.delete(record)
        if audit_log:
            record_change(db, **audit_log)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


def list_subjects(db: Session) -> list[Subject]:
    stmt = select(Subject).order_by(Subject.id)
    return list(db.scalars(stmt).all())


def get_subject(db: Session, subject_id: int) -> Subject:
    subject = db.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    return subject


def create_subject(db: Session, *, name: str, code: str, actor_user_id: int) -> Subject:
    subject = Subject(name=name, code=code)
    db.add(subject)
    db.flush()
    record_change(
        db,
        actor_user_id=actor_user_id,
        entity=Subject.__tablename__,
        entity_id=subject.id,
        action="create",
        old_data=None,
        new_data=serialize_model(subject),
    )
    db.commit()
    db.refresh(subject)
    return subject


def update_subject(
    db: Session, subject_id: int, *, name: str | None = None, code: str | None = None, actor_user_id: int
) -> Subject:
    subject = db.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    before = serialize_model(subject)
    if name is not None:
        subject.name = name
    if code is not None:
        subject.code = code
    db.flush()
    record_change(
        db,
        actor_user_id=actor_user_id,
        entity=Subject.__tablename__,
        entity_id=subject.id,
        action="update",
        old_data=before,
        new_data=serialize_model(subject),
    )
    db.commit()
    db.refresh(subject)
    return subject


def delete_subject(db: Session, subject_id: int, *, actor_user_id: int) -> None:
    subject = db.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    before = serialize_model(subject)
    _safe_delete(
        db,
        subject,
        detail="Subject is still in use",
        audit_log={
            "actor_user_id": actor_user_id,
            "entity": Subject.__tablename__,
            "entity_id": subject.id,
            "action": "delete",
            "old_data": before,
            "new_data": None,
        },
    )


def list_rooms(db: Session) -> list[Room]:
    stmt = select(Room).order_by(Room.id)
    return list(db.scalars(stmt).all())


def get_room(db: Session, room_id: int) -> Room:
    room = db.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return room


def create_room(
    db: Session, *, number: str, building: str, capacity: int, actor_user_id: int
) -> Room:
    room = Room(number=number, building=building, capacity=capacity)
    db.add(room)
    db.flush()
    record_change(
        db,
        actor_user_id=actor_user_id,
        entity=Room.__tablename__,
        entity_id=room.id,
        action="create",
        old_data=None,
        new_data=serialize_model(room),
    )
    db.commit()
    db.refresh(room)
    return room


def update_room(
    db: Session,
    room_id: int,
    *,
    number: str | None = None,
    building: str | None = None,
    capacity: int | None = None,
    actor_user_id: int,
) -> Room:
    room = db.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    before = serialize_model(room)
    if number is not None:
        room.number = number
    if building is not None:
        room.building = building
    if capacity is not None:
        room.capacity = capacity
    db.flush()
    record_change(
        db,
        actor_user_id=actor_user_id,
        entity=Room.__tablename__,
        entity_id=room.id,
        action="update",
        old_data=before,
        new_data=serialize_model(room),
    )
    db.commit()
    db.refresh(room)
    return room


def delete_room(db: Session, room_id: int, *, actor_user_id: int) -> None:
    room = db.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    before = serialize_model(room)
    _safe_delete(
        db,
        room,
        detail="Room is still in use",
        audit_log={
            "actor_user_id": actor_user_id,
            "entity": Room.__tablename__,
            "entity_id": room.id,
            "action": "delete",
            "old_data": before,
            "new_data": None,
        },
    )
