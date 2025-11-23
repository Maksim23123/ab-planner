from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.schemas.users import UserProfile
from app.api import deps
from app.services import user_service
from app.models.users import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfile)
def read_current_user(
    user_id: int | None = Query(default=None, description="Override user id"),
    db: Session = Depends(deps.get_db),
    _current_user: User = Depends(deps.get_current_user),
):
    target_id = user_id or _current_user.id
    return user_service.get_user_profile(db, target_id)
