from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.schemas.notifications import Notification, NotificationCreate, NotificationUpdate
from app.api import deps
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[Notification])
def list_notifications(
    user_id: int | None = Query(default=None, description="Filter by user id"),
    status: str | None = Query(default=None, description="Filter by notification status"),
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    target_id = user_id or actor.user.id
    if user_id is not None and actor.role != "admin" and user_id != actor.user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return notification_service.list_notifications(db, user_id=target_id, status=status)


@router.post("", response_model=Notification, status_code=201)
def create_notification(
    payload: NotificationCreate,
    db: Session = Depends(deps.get_db),
    _admin: deps.CurrentActor = Depends(deps.require_admin),
):
    return notification_service.create_notification(
        db,
        user_id=payload.user_id,
        payload=payload.payload,
        status_value=payload.status,
    )


@router.patch("/{notification_id}", response_model=Notification)
def update_notification(
    payload: NotificationUpdate,
    notification_id: int = Path(..., description="Notification identifier"),
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    record = notification_service.get_notification(db, notification_id)
    if actor.role != "admin" and record.user_id != actor.user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return notification_service.update_notification(db, notification_id, status_value=payload.status)
