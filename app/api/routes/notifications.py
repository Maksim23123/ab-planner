from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.schemas.notifications import (
    Notification,
    NotificationCreate,
    NotificationGroupBroadcast,
    NotificationGroupBroadcastResult,
    NotificationUpdate,
)
from app.api import deps
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[Notification])
def list_notifications(
    user_id: int | None = Query(default=None, description="Filter by user id"),
    delivery_status: str | None = Query(default=None, description="Filter by delivery status"),
    read_status: str | None = Query(default=None, description="Filter by read status"),
    status: str | None = Query(
        default=None,
        description="Deprecated: legacy status filter (uses delivery status)",
        include_in_schema=False,
    ),
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    target_id = deps.resolve_user_scope(actor, user_id)
    effective_delivery = delivery_status or status
    return notification_service.list_notifications(
        db,
        user_id=target_id,
        delivery_status=effective_delivery,
        read_status=read_status,
    )


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
        delivery_status=payload.delivery_status or "queued",
        read_status=payload.read_status,
        read=payload.read,
    )


@router.post("/group-broadcast", response_model=NotificationGroupBroadcastResult, status_code=201)
def broadcast_group_notification(
    payload: NotificationGroupBroadcast,
    db: Session = Depends(deps.get_db),
    _admin: deps.CurrentActor = Depends(deps.require_admin),
):
    return notification_service.broadcast_group_notification(
        db,
        group_ids=payload.group_ids,
        title=payload.title,
        body=payload.content,
        data=payload.data,
    )


@router.patch("/{notification_id}", response_model=Notification)
def update_notification(
    payload: NotificationUpdate,
    notification_id: int = Path(..., description="Notification identifier"),
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    record = notification_service.get_notification(db, notification_id)
    deps.resolve_user_scope(actor, record.user_id)
    return notification_service.update_notification(
        db,
        notification_id,
        read=payload.read,
        read_status_value=payload.read_status,
    )
