from fastapi import APIRouter, Query

from app.schemas.selections import SelectionCreate, SelectionOut
from app.services import mock_store

router = APIRouter(prefix="/student-group-selection", tags=["student-selection"])


@router.get("", response_model=list[SelectionOut])
def list_selections(user_id: int | None = Query(default=None, description="Filter by user id")):
    return mock_store.list_group_selections(user_id=user_id)


@router.post("", response_model=SelectionOut, status_code=201)
def create_selection(payload: SelectionCreate):
    return mock_store.create_group_selection(group_id=payload.group_id, user_id=payload.user_id)
