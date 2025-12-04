from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FcmToken(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    token: str
    platform: str
    created_at: datetime


class FcmTokenCreate(BaseModel):
    token: str
    platform: str
    user_id: int | None = None
