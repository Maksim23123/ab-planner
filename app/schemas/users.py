from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Role(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    label: str


class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str


class UserProfile(UserSummary):
    role: Role
    created_at: datetime


class UserRoleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role_id: int
