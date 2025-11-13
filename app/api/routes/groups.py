from fastapi import APIRouter, Path, Query

from app.schemas.programs import Group
from app.services import mock_store

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("", response_model=list[Group])
def list_groups(
    program_id: int | None = Query(default=None),
    program_year_id: int | None = Query(default=None),
    specialization_id: int | None = Query(default=None),
    group_type: str | None = Query(default=None),
):
    return mock_store.list_groups(
        program_id=program_id,
        program_year_id=program_year_id,
        specialization_id=specialization_id,
        group_type=group_type,
    )


@router.get("/{group_id}", response_model=Group)
def read_group(group_id: int = Path(..., description="Group identifier")):
    return mock_store.get_group(group_id)
