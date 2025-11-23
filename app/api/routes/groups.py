from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.schemas.programs import Group
from app.api import deps
from app.services import program_service
from app.models.users import User

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("", response_model=list[Group])
def list_groups(
    program_id: int | None = Query(default=None),
    program_year_id: int | None = Query(default=None),
    specialization_id: int | None = Query(default=None),
    group_type: str | None = Query(default=None),
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


@router.get("/{group_id}", response_model=Group)
def read_group(
    group_id: int = Path(..., description="Group identifier"),
    db: Session = Depends(deps.get_db),
    _current_user: User = Depends(deps.get_current_user),
):
    return program_service.get_group(db, group_id)
