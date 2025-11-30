from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.lessons import Room, RoomCreate, RoomUpdate
from app.services import catalog_service

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("", response_model=list[Room])
def list_rooms(
    db: Session = Depends(deps.get_db),
    _actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    return catalog_service.list_rooms(db)


@router.get("/{room_id}", response_model=Room)
def read_room(
    room_id: int = Path(..., description="Room identifier"),
    db: Session = Depends(deps.get_db),
    _actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    return catalog_service.get_room(db, room_id)


@router.post("", response_model=Room, status_code=201)
def create_room(
    payload: RoomCreate,
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.require_admin),
):
    return catalog_service.create_room(
        db,
        number=payload.number,
        building=payload.building,
        capacity=payload.capacity,
        actor_user_id=actor.user.id,
    )


@router.patch("/{room_id}", response_model=Room)
def update_room(
    payload: RoomUpdate,
    room_id: int = Path(..., description="Room identifier"),
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.require_admin),
):
    return catalog_service.update_room(
        db,
        room_id,
        number=payload.number,
        building=payload.building,
        capacity=payload.capacity,
        actor_user_id=actor.user.id,
    )


@router.delete("/{room_id}", status_code=204)
def delete_room(
    room_id: int = Path(..., description="Room identifier"),
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.require_admin),
):
    catalog_service.delete_room(db, room_id, actor_user_id=actor.user.id)
