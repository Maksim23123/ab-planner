from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.lessons import Lesson, LessonCreate, LessonSeriesCreate, LessonUpdate
from app.services import lesson_service
from app.models.selections import StudentGroupSelection

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("", response_model=list[Lesson])
def list_lessons(
    group_id: int | None = Query(default=None, description="Filter by group"),
    date_from: datetime | None = Query(default=None, description="Start date filter"),
    date_to: datetime | None = Query(default=None, description="End date filter"),
    db: Session = Depends(deps.get_db),
    _actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    return lesson_service.list_lessons(db, group_id=group_id, date_from=date_from, date_to=date_to)


@router.post("", response_model=Lesson, status_code=status.HTTP_201_CREATED)
def create_lesson(
    payload: LessonCreate,
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    if actor.role == "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if actor.role == "lecturer" and payload.lecturer_user_id != actor.user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return lesson_service.create_lesson(
        db, payload.model_dump(), actor_user_id=actor.user.id
    )


@router.post("/series", response_model=list[Lesson], status_code=status.HTTP_201_CREATED)
def create_lesson_series(
    payload: LessonSeriesCreate,
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    base = payload.lesson
    if actor.role == "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if actor.role == "lecturer" and base.lecturer_user_id != actor.user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    return lesson_service.create_lesson_series(
        db,
        base.model_dump(),
        occurrences=payload.occurrences,
        repeat_every_days=payload.repeat_every_days,
        actor_user_id=actor.user.id,
    )


@router.get("/{lesson_id}", response_model=Lesson)
def read_lesson(
    lesson_id: int = Path(..., description="Lesson identifier"),
    db: Session = Depends(deps.get_db),
    _actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    return lesson_service.get_lesson(db, lesson_id)


@router.patch("/{lesson_id}", response_model=Lesson)
def update_lesson(
    payload: LessonUpdate,
    lesson_id: int = Path(..., description="Lesson identifier"),
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    data = payload.model_dump(exclude_unset=True)
    lesson = lesson_service.get_lesson(db, lesson_id)

    if actor.role == "student":
        selection = db.execute(
            select(StudentGroupSelection).where(
                StudentGroupSelection.user_id == actor.user.id,
                StudentGroupSelection.group_id == lesson.group_id,
            )
        ).scalar_one_or_none()
        if selection is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        scope = data.pop("scope", "occurrence")
        if scope != "occurrence":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        allowed_fields = {"starts_at", "ends_at", "status", "room_id"}
        disallowed = set(data.keys()) - allowed_fields
        if disallowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    elif actor.role == "lecturer":
        if lesson.lecturer_user_id != actor.user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        forbidden_identity_fields = {"lecturer_user_id", "group_id", "subject_id"}
        if forbidden_identity_fields.intersection(data):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        data.pop("scope", None)
    else:
        data.pop("scope", None)

    return lesson_service.update_lesson(db, lesson_id, data, actor_user_id=actor.user.id)


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson(
    lesson_id: int = Path(..., description="Lesson identifier"),
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    lesson = lesson_service.get_lesson(db, lesson_id)
    if actor.role == "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if actor.role == "lecturer" and lesson.lecturer_user_id != actor.user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    lesson_service.delete_lesson(db, lesson_id, actor_user_id=actor.user.id)
