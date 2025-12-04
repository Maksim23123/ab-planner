from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.schemas.selections import SelectionCreate, SelectionOut
from app.services import selection_service, program_service
from app.api import deps

router = APIRouter(prefix="/student-group-selection", tags=["student-selection"])


@router.get("", response_model=list[SelectionOut])
def list_selections(
    user_id: int | None = Query(default=None, description="Filter by user id"),
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    target_id = deps.resolve_user_scope(actor, user_id)
    return selection_service.list_selections(db, user_id=target_id)


@router.put("", response_model=SelectionOut, status_code=201)
def upsert_selection(
    payload: SelectionCreate,
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    target_id = deps.resolve_user_scope(actor, payload.user_id)
    if any([payload.program_id, payload.program_year_id, payload.specialization_id]):
        group = program_service.get_group(db, payload.group_id)
        if payload.program_id is not None and group.program_id != payload.program_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Group does not match program")
        if payload.program_year_id is not None and group.program_year_id != payload.program_year_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Group does not match program year")
        if payload.specialization_id is not None and group.specialization_id != payload.specialization_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Group does not match specialization")
    return selection_service.create_selection(
        db, group_id=payload.group_id, user_id=target_id, actor_user_id=actor.user.id
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_selection(
    user_id: int | None = Query(default=None, description="Target user id"),
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    target_id = deps.resolve_user_scope(actor, user_id)
    selection_service.delete_selection(db, user_id=target_id, actor_user_id=actor.user.id)
