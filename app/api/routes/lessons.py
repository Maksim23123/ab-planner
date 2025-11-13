from datetime import datetime

from fastapi import APIRouter, Query

from app.schemas.lessons import Lesson
from app.services import mock_store

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("", response_model=list[Lesson])
def list_lessons(
    group_id: int | None = Query(default=None, description="Filter by group"),
    date_from: datetime | None = Query(default=None, description="Start date filter"),
    date_to: datetime | None = Query(default=None, description="End date filter"),
):
    return mock_store.list_lessons(group_id=group_id, date_from=date_from, date_to=date_to)
