from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import FcmToken, User


def list_tokens(db: Session, *, user_id: int) -> list[FcmToken]:
    stmt = (
        select(FcmToken)
        .where(FcmToken.user_id == user_id)
        .order_by(FcmToken.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def register_token(
    db: Session, *, user_id: int, token: str, platform: str
) -> FcmToken:
    token = token.strip()
    platform = platform.strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="token is required"
        )
    if not platform:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="platform is required"
        )

    if db.get(User, user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    existing = db.execute(
        select(FcmToken).where(FcmToken.user_id == user_id, FcmToken.token == token)
    ).scalar_one_or_none()
    if existing:
        existing.platform = platform  # refresh platform if it changed
        db.commit()
        db.refresh(existing)
        return existing

    # Drop any stale duplicates of the same token for other users to avoid noisy pushes.
    db.execute(delete(FcmToken).where(FcmToken.token == token, FcmToken.user_id != user_id))

    record = FcmToken(
        user_id=user_id,
        token=token,
        platform=platform,
        created_at=datetime.now(timezone.utc),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def delete_token(db: Session, token_id: int) -> None:
    record = db.get(FcmToken, token_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")
    db.delete(record)
    db.commit()
