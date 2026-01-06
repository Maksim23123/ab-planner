from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict


class Notification(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    payload: Dict[str, Any]
    delivery_status: str
    read_status: str
    read_at: datetime | None
    last_error: str | None = None
    attempts: int
    created_at: datetime
    last_attempt_at: datetime | None = None
    sent_at: datetime | None


class NotificationCreate(BaseModel):
    user_id: int
    payload: Dict[str, Any]
    delivery_status: str | None = "queued"
    read_status: str | None = None
    read: bool | None = None


class NotificationUpdate(BaseModel):
    read: bool | None = None
    read_status: str | None = None


class NotificationGroupBroadcast(BaseModel):
    group_ids: list[int]
    title: str
    content: str
    data: Dict[str, Any] | None = None


class NotificationGroupBroadcastResult(BaseModel):
    group_ids: list[int]
    user_count: int
    notification_count: int
