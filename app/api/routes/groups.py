from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.schemas.programs import Group, GroupCreate, GroupUpdate
from app.api import deps
from app.services import program_service

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("", response_model=list[Group])
def list_groups(
    program_id: int | None = Query(default=None),
    program_year_id: int | None = Query(default=None),
    specialization_id: int | None = Query(default=None),
    group_type: str | None = Query(default=None),
    db: Session = Depends(deps.get_db),
    _actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    return program_service.list_groups(
        db,
        program_id=program_id,
        program_year_id=program_year_id,
        specialization_id=specialization_id,
        group_type=group_type,
    )


@router.get("/{group_id}", response_model=Group)
def read_group(
    group_id: int = Path(..., description="Group identifier"),
    db: Session = Depends(deps.get_db),
    _actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    return program_service.get_group(db, group_id)


@router.post("", response_model=Group, status_code=201)
def create_group(
    payload: GroupCreate,
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.require_admin),
):
    return program_service.create_group(
        db,
        program_id=payload.program_id,
        program_year_id=payload.program_year_id,
        specialization_id=payload.specialization_id,
        group_type_code=payload.group_type,
        code=payload.code,
        actor_user_id=actor.user.id,
    )


@router.patch("/{group_id}", response_model=Group)
def update_group(
    payload: GroupUpdate,
    group_id: int = Path(..., description="Group identifier"),
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.require_admin),
):
    return program_service.update_group(
        db,
        group_id,
        program_id=payload.program_id,
        program_year_id=payload.program_year_id,
        specialization_id=payload.specialization_id,
        group_type_code=payload.group_type,
        code=payload.code,
        actor_user_id=actor.user.id,
    )


@router.delete("/{group_id}", status_code=204)
def delete_group(
    group_id: int = Path(..., description="Group identifier"),
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.require_admin),
):
    program_service.delete_group(db, group_id, actor_user_id=actor.user.id)
