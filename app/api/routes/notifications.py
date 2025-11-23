from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.schemas.notifications import Notification
from app.api import deps
from app.services import notification_service
from app.models.users import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[Notification])
def list_notifications(
    user_id: int | None = Query(default=None, description="Filter by user id"),
    status: str | None = Query(default=None, description="Filter by notification status"),
    db: Session = Depends(deps.get_db),
    _current_user: User = Depends(deps.get_current_user),
):
    target_id = user_id or _current_user.id
    return notification_service.list_notifications(db, user_id=target_id, status=status)
