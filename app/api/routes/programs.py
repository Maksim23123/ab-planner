from fastapi import APIRouter, Path, Query

from app.schemas.programs import Group, Program
from app.services import mock_store

router = APIRouter(prefix="/programs", tags=["programs"])


@router.get("", response_model=list[Program])
def list_programs():
    return mock_store.list_programs()


@router.get("/{program_id}/groups", response_model=list[Group])
def list_program_groups(
    program_id: int = Path(..., description="Program identifier"),
    program_year_id: int | None = Query(default=None, description="Filter by program year"),
    specialization_id: int | None = Query(default=None, description="Filter by specialization"),
    group_type: str | None = Query(default=None, description="Filter by group type"),
):
    return mock_store.list_groups(
        program_id=program_id,
        program_year_id=program_year_id,
        specialization_id=specialization_id,
        group_type=group_type,
    )
