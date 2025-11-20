from datetime import datetime

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.lessons import Lesson, LessonCreate, LessonUpdate
from app.services import lesson_service
from app.models.users import User

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("", response_model=list[Lesson])
def list_lessons(
    group_id: int | None = Query(default=None, description="Filter by group"),
    date_from: datetime | None = Query(default=None, description="Start date filter"),
    date_to: datetime | None = Query(default=None, description="End date filter"),
    db: Session = Depends(deps.get_db),
    _current_user: User = Depends(deps.get_current_user),
):
    return lesson_service.list_lessons(db, group_id=group_id, date_from=date_from, date_to=date_to)


@router.get("/{lesson_id}", response_model=Lesson)
def read_lesson(
    lesson_id: int = Path(..., description="Lesson identifier"),
    db: Session = Depends(deps.get_db),
    _current_user: User = Depends(deps.get_current_user),
):
    return lesson_service.get_lesson(db, lesson_id)


@router.post("", response_model=Lesson, status_code=status.HTTP_201_CREATED)
def create_lesson(
    payload: LessonCreate,
    db: Session = Depends(deps.get_db),
    _current_user: User = Depends(deps.get_current_user),
):
    return lesson_service.create_lesson(db, payload.model_dump())


@router.patch("/{lesson_id}", response_model=Lesson)
def update_lesson(
    payload: LessonUpdate,
    lesson_id: int = Path(..., description="Lesson identifier"),
    db: Session = Depends(deps.get_db),
    _current_user: User = Depends(deps.get_current_user),
):
    data = payload.model_dump(exclude_unset=True)
    return lesson_service.update_lesson(db, lesson_id, data)


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson(
    lesson_id: int = Path(..., description="Lesson identifier"),
    db: Session = Depends(deps.get_db),
    _current_user: User = Depends(deps.get_current_user),
):
    lesson_service.delete_lesson(db, lesson_id)
