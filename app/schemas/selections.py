from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class SelectionCreate(BaseModel):
    group_id: int
    user_id: int | None = None


class SelectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    group_id: int
    selected_at: datetime
