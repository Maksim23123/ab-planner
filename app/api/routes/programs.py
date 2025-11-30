from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.schemas.programs import (
    Group,
    Program,
    ProgramBrief,
    ProgramCreate,
    ProgramUpdate,
)
from app.api import deps
from app.services import program_service

router = APIRouter(prefix="/programs", tags=["programs"])


@router.get("", response_model=list[Program])
def list_programs(
    db: Session = Depends(deps.get_db),
    _actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    return program_service.list_programs(db)


@router.get("/{program_id}", response_model=Program)
def read_program(
    program_id: int = Path(..., description="Program identifier"),
    db: Session = Depends(deps.get_db),
    _actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    return program_service.get_program(db, program_id)


@router.post("", response_model=ProgramBrief, status_code=201)
def create_program(
    payload: ProgramCreate,
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.require_admin),
):
    return program_service.create_program(db, name=payload.name, actor_user_id=actor.user.id)


@router.patch("/{program_id}", response_model=ProgramBrief)
def update_program(
    payload: ProgramUpdate,
    program_id: int = Path(..., description="Program identifier"),
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.require_admin),
):
    return program_service.update_program(
        db, program_id, name=payload.name, actor_user_id=actor.user.id
    )


@router.delete("/{program_id}", status_code=204)
def delete_program(
    program_id: int = Path(..., description="Program identifier"),
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.require_admin),
):
    program_service.delete_program(db, program_id, actor_user_id=actor.user.id)


@router.get("/{program_id}/groups", response_model=list[Group])
def list_program_groups(
    program_id: int = Path(..., description="Program identifier"),
    program_year_id: int | None = Query(default=None, description="Filter by program year"),
    specialization_id: int | None = Query(default=None, description="Filter by specialization"),
    group_type: str | None = Query(default=None, description="Filter by group type"),
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
