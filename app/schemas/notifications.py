from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict


class Notification(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    payload: Dict[str, Any]
    status: str
    attempts: int
    created_at: datetime
    sent_at: datetime | None


class NotificationCreate(BaseModel):
    user_id: int
    payload: Dict[str, Any]
    status: str = "queued"


class NotificationUpdate(BaseModel):
    status: str | None = None
