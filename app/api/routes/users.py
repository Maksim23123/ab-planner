from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.schemas.users import UserProfile, UserProfileWithGroups, UserRoleUpdate
from app.api import deps
from app.services import selection_service, user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfileWithGroups)
def read_current_user(
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    user = user_service.get_user_profile(db, actor.user.id)
    selected_groups = selection_service.list_selected_groups(db, user_id=actor.user.id)
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "created_at": user.created_at,
        "selected_groups": selected_groups,
    }


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


@router.patch("/{user_id}/role", response_model=UserProfile)
def set_user_role(
    payload: UserRoleUpdate,
    user_id: int = Path(..., description="User identifier"),
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.require_admin),
):
    return user_service.set_user_role(
        db, user_id, payload.role_id, actor_user_id=actor.user.id
    )
