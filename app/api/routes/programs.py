from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.schemas.programs import Group, Program
from app.api import deps
from app.services import program_service
from app.models.users import User

router = APIRouter(prefix="/programs", tags=["programs"])


@router.get("", response_model=list[Program])
def list_programs(
    db: Session = Depends(deps.get_db),
    _current_user: User = Depends(deps.get_current_user),
):
    return program_service.list_programs(db)


@router.get("/{program_id}/groups", response_model=list[Group])
def list_program_groups(
    program_id: int = Path(..., description="Program identifier"),
    program_year_id: int | None = Query(default=None, description="Filter by program year"),
    specialization_id: int | None = Query(default=None, description="Filter by specialization"),
    group_type: str | None = Query(default=None, description="Filter by group type"),
    db: Session = Depends(deps.get_db),
    _current_user: User = Depends(deps.get_current_user),
):
    return program_service.list_groups(
        db,
        program_id=program_id,
        program_year_id=program_year_id,
        specialization_id=specialization_id,
        group_type=group_type,
    )
