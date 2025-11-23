from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models import User


def get_user_profile(db: Session, user_id: int) -> User:
    """Fetch a user with their role for profile payloads."""
    stmt = select(User).options(joinedload(User.role)).where(User.id == user_id)
    user = db.execute(stmt).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
