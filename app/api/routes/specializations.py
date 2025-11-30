from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.schemas.programs import Specialization, SpecializationCreate, SpecializationUpdate
from app.api import deps
from app.services import program_service

router = APIRouter(prefix="/specializations", tags=["specializations"])


@router.get("", response_model=list[Specialization])
def list_specializations(
    db: Session = Depends(deps.get_db),
    _actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    return program_service.list_specializations(db)


@router.get("/{spec_id}", response_model=Specialization)
def read_specialization(
    spec_id: int = Path(..., description="Specialization identifier"),
    db: Session = Depends(deps.get_db),
    _actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    return program_service.get_specialization(db, spec_id)


@router.post("", response_model=Specialization, status_code=201)
def create_specialization(
    payload: SpecializationCreate,
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.require_admin),
):
    return program_service.create_specialization(
        db, program_id=payload.program_id, name=payload.name, actor_user_id=actor.user.id
    )


@router.patch("/{spec_id}", response_model=Specialization)
def update_specialization(
    payload: SpecializationUpdate,
    spec_id: int = Path(..., description="Specialization identifier"),
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.require_admin),
):
    return program_service.update_specialization(
        db,
        spec_id,
        name=payload.name,
        program_id=payload.program_id,
        actor_user_id=actor.user.id,
    )


@router.delete("/{spec_id}", status_code=204)
def delete_specialization(
    spec_id: int = Path(..., description="Specialization identifier"),
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.require_admin),
):
    program_service.delete_specialization(db, spec_id, actor_user_id=actor.user.id)
