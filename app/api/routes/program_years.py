from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.schemas.programs import ProgramYear, ProgramYearCreate, ProgramYearUpdate
from app.api import deps
from app.services import program_service

router = APIRouter(prefix="/program-years", tags=["program-years"])


@router.get("", response_model=list[ProgramYear])
def list_program_years(
    db: Session = Depends(deps.get_db),
    _actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    return program_service.list_program_years(db)


@router.get("/{year_id}", response_model=ProgramYear)
def read_program_year(
    year_id: int = Path(..., description="Program year identifier"),
    db: Session = Depends(deps.get_db),
    _actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    return program_service.get_program_year(db, year_id)


@router.post("", response_model=ProgramYear, status_code=201)
def create_program_year(
    payload: ProgramYearCreate,
    db: Session = Depends(deps.get_db),
    _admin: deps.CurrentActor = Depends(deps.require_admin),
):
    return program_service.create_program_year(db, program_id=payload.program_id, year=payload.year)


@router.patch("/{year_id}", response_model=ProgramYear)
def update_program_year(
    payload: ProgramYearUpdate,
    year_id: int = Path(..., description="Program year identifier"),
    db: Session = Depends(deps.get_db),
    _admin: deps.CurrentActor = Depends(deps.require_admin),
):
    return program_service.update_program_year(
        db, year_id, year=payload.year, program_id=payload.program_id
    )


@router.delete("/{year_id}", status_code=204)
def delete_program_year(
    year_id: int = Path(..., description="Program year identifier"),
    db: Session = Depends(deps.get_db),
    _admin: deps.CurrentActor = Depends(deps.require_admin),
):
    program_service.delete_program_year(db, year_id)
