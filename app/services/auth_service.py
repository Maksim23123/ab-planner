from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core import security
from app.core.config import get_settings
from app.models.users import Role, User
from app.schemas.auth import AuthTokens, MicrosoftAuthRequest
from app.schemas.users import UserProfile
from app.services.microsoft_oauth import oauth_client


async def login_with_microsoft(db: Session, payload: MicrosoftAuthRequest) -> AuthTokens:
    token_result = await oauth_client.exchange_code(
        code=payload.code,
        code_verifier=payload.code_verifier,
        redirect_uri=str(payload.redirect_uri),
    )

    email = _extract_email(token_result.claims)
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Microsoft account missing email claim")

    name = token_result.claims.get("name") or email.split("@")[0]
    user = _get_or_create_user(db, email=email.lower(), name=name)

    access_token = security.create_access_token(user.id, user.role.code)
    refresh_token = security.create_refresh_token(user.id)
    settings = get_settings()

    return AuthTokens(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.auth_access_token_exp_minutes * 60,
        user=UserProfile.model_validate(user),
    )


def refresh_session(db: Session, refresh_token: str) -> AuthTokens:
    try:
        payload = security.decode_token(refresh_token, security.REFRESH_TOKEN_TYPE)
    except security.AuthTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

    user_id = payload.get("user_id")
    if not isinstance(user_id, int):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token payload")

    stmt = select(User).options(joinedload(User.role)).where(User.id == user_id)
    user = db.execute(stmt).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    access_token = security.create_access_token(user.id, user.role.code)
    next_refresh = security.create_refresh_token(user.id)
    settings = get_settings()

    return AuthTokens(
        access_token=access_token,
        refresh_token=next_refresh,
        token_type="bearer",
        expires_in=settings.auth_access_token_exp_minutes * 60,
        user=UserProfile.model_validate(user),
    )


def _extract_email(claims: dict[str, Any]) -> str | None:
    for key in ("preferred_username", "email", "upn"):
        value = claims.get(key)
        if value:
            return str(value)
    return None


def _get_or_create_user(db: Session, *, email: str, name: str) -> User:
    stmt = select(User).options(joinedload(User.role)).where(User.email == email)
    user = db.execute(stmt).scalar_one_or_none()
    if user:
        user.name = name
        db.commit()
        db.refresh(user)
        return user

    role = _get_default_role(db)
    user = User(
        email=email,
        name=name,
        role_id=role.id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    user.role = role
    return user


def _get_default_role(db: Session) -> Role:
    settings = get_settings()
    stmt = select(Role).where(Role.code == settings.auth_default_role_code)
    role = db.execute(stmt).scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Default role missing")
    return role
