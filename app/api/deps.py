from __future__ import annotations

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.users import User


def get_db():
    """Yield a database session tied to the request lifecycle."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db),
    x_user_id: int | None = Header(default=None),
) -> User:
    """
    Temporary auth stub. Uses the `X-User-Id` header when present,
    otherwise falls back to the default user from settings.
    """
    settings = get_settings()
    user_id = x_user_id or settings.default_user_id
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
