from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.schemas.users import UserProfile
from app.api import deps
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfile)
def read_current_user(
    user_id: int | None = Query(default=None, description="Override user id"),
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    target_id = user_id or actor.user.id
    return user_service.get_user_profile(db, target_id)


@router.get("", response_model=list[UserProfile])
def list_users(
    db: Session = Depends(deps.get_db),
    _admin: deps.CurrentActor = Depends(deps.require_admin),
):
    return user_service.list_users(db)


@router.get("/{user_id}", response_model=UserProfile)
def read_user(
    user_id: int = Path(..., description="User identifier"),
    db: Session = Depends(deps.get_db),
    _admin: deps.CurrentActor = Depends(deps.require_admin),
):
    return user_service.get_user(db, user_id)
