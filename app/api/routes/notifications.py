from fastapi import APIRouter, Query

from app.schemas.notifications import Notification
from app.services import mock_store

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[Notification])
def list_notifications(
    user_id: int | None = Query(default=None, description="Filter by user id"),
    status: str | None = Query(default=None, description="Filter by notification status"),
):
    return mock_store.list_notifications(user_id=user_id, status=status)
