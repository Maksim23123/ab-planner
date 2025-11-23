from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.schemas.selections import SelectionCreate, SelectionOut
from app.api import deps
from app.services import selection_service
from app.models.users import User

router = APIRouter(prefix="/student-group-selection", tags=["student-selection"])


@router.get("", response_model=list[SelectionOut])
def list_selections(
    user_id: int | None = Query(default=None, description="Filter by user id"),
    db: Session = Depends(deps.get_db),
    _current_user: User = Depends(deps.get_current_user),
):
    target_id = user_id or _current_user.id
    return selection_service.list_selections(db, user_id=target_id)


@router.post("", response_model=SelectionOut, status_code=201)
def create_selection(
    payload: SelectionCreate,
    db: Session = Depends(deps.get_db),
    _current_user: User = Depends(deps.get_current_user),
):
    target_id = payload.user_id or _current_user.id
    return selection_service.create_selection(db, group_id=payload.group_id, user_id=target_id)
