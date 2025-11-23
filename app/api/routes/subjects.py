from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.lessons import Subject, SubjectCreate, SubjectUpdate
from app.services import catalog_service

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("", response_model=list[Subject])
def list_subjects(
    db: Session = Depends(deps.get_db),
    _actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    return catalog_service.list_subjects(db)


@router.get("/{subject_id}", response_model=Subject)
def read_subject(
    subject_id: int = Path(..., description="Subject identifier"),
    db: Session = Depends(deps.get_db),
    _actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    return catalog_service.get_subject(db, subject_id)


@router.post("", response_model=Subject, status_code=201)
def create_subject(
    payload: SubjectCreate,
    db: Session = Depends(deps.get_db),
    _admin: deps.CurrentActor = Depends(deps.require_admin),
):
    return catalog_service.create_subject(db, name=payload.name, code=payload.code)


@router.patch("/{subject_id}", response_model=Subject)
def update_subject(
    payload: SubjectUpdate,
    subject_id: int = Path(..., description="Subject identifier"),
    db: Session = Depends(deps.get_db),
    _admin: deps.CurrentActor = Depends(deps.require_admin),
):
    return catalog_service.update_subject(db, subject_id, name=payload.name, code=payload.code)


@router.delete("/{subject_id}", status_code=204)
def delete_subject(
    subject_id: int = Path(..., description="Subject identifier"),
    db: Session = Depends(deps.get_db),
    _admin: deps.CurrentActor = Depends(deps.require_admin),
):
    catalog_service.delete_subject(db, subject_id)
