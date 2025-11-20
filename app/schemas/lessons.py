from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict

from app.schemas.programs import Group
from app.schemas.users import UserSummary


class LessonStatus(str, Enum):
    scheduled = "scheduled"
    rescheduled = "rescheduled"
    cancelled = "cancelled"


class Subject(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str


class Room(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    number: str
    building: str
    capacity: int


class LessonBase(BaseModel):
    subject_id: int
    lecturer_user_id: int
    room_id: int
    group_id: int
    starts_at: datetime
    ends_at: datetime
    status: LessonStatus
    lesson_type: str


class LessonCreate(LessonBase):
    pass


class LessonUpdate(BaseModel):
    subject_id: int | None = None
    lecturer_user_id: int | None = None
    room_id: int | None = None
    group_id: int | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    status: LessonStatus | None = None
    lesson_type: str | None = None


class Lesson(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    starts_at: datetime
    ends_at: datetime
    status: LessonStatus
    lesson_type: str
    subject: Subject
    room: Room
    group: Group
    lecturer: UserSummary
