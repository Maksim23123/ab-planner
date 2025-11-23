from __future__ import annotations

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
from typing import NamedTuple

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.users import User


ALLOWED_ROLES = {"student", "lecturer", "admin"}


class CurrentActor(NamedTuple):
    user: User
    role: str


def get_db():
    """Yield a database session tied to the request lifecycle."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_actor(
    db: Session = Depends(get_db),
    x_user_id: int | None = Header(default=None),
    x_user_role: str | None = Header(default=None),
) -> CurrentActor:
    """
    Temporary auth stub. Uses `X-User-Id` and `X-User-Role` headers when present,
    otherwise falls back to the default user and their role.
    """
    settings = get_settings()
    user_id = x_user_id or settings.default_user_id
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    role = (x_user_role or getattr(user.role, "code", None) or "").lower()
    if role not in ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="Role not permitted")

    return CurrentActor(user=user, role=role)


def require_admin(actor: CurrentActor = Depends(get_current_actor)) -> CurrentActor:
    if actor.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return actor


def get_current_user(actor: CurrentActor = Depends(get_current_actor)) -> User:
    """Compatibility helper where only the user object is needed."""
    return actor.user
