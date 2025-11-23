from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Room, Subject


def list_subjects(db: Session) -> list[Subject]:
    stmt = select(Subject).order_by(Subject.id)
    return list(db.scalars(stmt).all())


def get_subject(db: Session, subject_id: int) -> Subject:
    subject = db.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    return subject


def create_subject(db: Session, *, name: str, code: str) -> Subject:
    subject = Subject(name=name, code=code)
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


def update_subject(db: Session, subject_id: int, *, name: str | None = None, code: str | None = None) -> Subject:
    subject = db.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    if name is not None:
        subject.name = name
    if code is not None:
        subject.code = code
    db.commit()
    db.refresh(subject)
    return subject


def delete_subject(db: Session, subject_id: int) -> None:
    subject = db.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    db.delete(subject)
    db.commit()


def list_rooms(db: Session) -> list[Room]:
    stmt = select(Room).order_by(Room.id)
    return list(db.scalars(stmt).all())


def get_room(db: Session, room_id: int) -> Room:
    room = db.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return room


def create_room(db: Session, *, number: str, building: str, capacity: int) -> Room:
    room = Room(number=number, building=building, capacity=capacity)
    db.add(room)
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
) -> Room:
    room = db.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    if number is not None:
        room.number = number
    if building is not None:
        room.building = building
    if capacity is not None:
        room.capacity = capacity
    db.commit()
    db.refresh(room)
    return room


def delete_room(db: Session, room_id: int) -> None:
    room = db.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    db.delete(room)
    db.commit()
