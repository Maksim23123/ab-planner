from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import secrets
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload

from app.core import security
from app.core.config import get_settings
from app.models import AuthSession
from app.models.users import Role, User
from app.schemas.auth import AuthTokens, LogoutRequest, MicrosoftAuthRequest
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

    return _issue_tokens(db, user)


def refresh_session(db: Session, refresh_token: str) -> AuthTokens:
    payload = _decode_refresh(refresh_token)
    user_id = payload["user_id"]
    jti = payload["jti"]

    session = _get_session_by_token(db, refresh_token)
    now = _now()

    if session is None or session.user_id != user_id or session.jti != jti:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if session.revoked_at is not None:
        _revoke_all_sessions(db, user_id, reason="refresh token reuse detected")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if session.expires_at <= now:
        _revoke_session(db, session, reason="expired")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    user = _get_user_with_role(db, user_id)
    _revoke_session(db, session, reason="rotated")
    return _issue_tokens(db, user)


def logout(db: Session, actor: User, payload: Optional[LogoutRequest]) -> None:
    refresh_token = payload.refresh_token if payload else None
    if refresh_token is None:
        _revoke_all_sessions(db, actor.id, reason="logout all sessions")
        return

    data = _decode_refresh(refresh_token)
    if data["user_id"] != actor.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    session = _get_session_by_token(db, refresh_token)
    if session is None or session.user_id != actor.id:
        _revoke_all_sessions(db, actor.id, reason="logout token not found")
        return

    _revoke_session(db, session, reason="logout")


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


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_refresh_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def _decode_refresh(token: str) -> dict[str, Any]:
    try:
        payload = security.decode_token(token, security.REFRESH_TOKEN_TYPE)
    except security.AuthTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

    user_id = payload.get("user_id")
    jti = payload.get("jti")
    if not isinstance(user_id, int) or not isinstance(jti, str):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token payload")
    return {"user_id": user_id, "jti": jti}


def _get_user_with_role(db: Session, user_id: int) -> User:
    stmt = select(User).options(joinedload(User.role)).where(User.id == user_id)
    user = db.execute(stmt).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def _persist_session(db: Session, user_id: int, refresh_token: str, jti: str, expires_at: datetime) -> None:
    record = AuthSession(
        user_id=user_id,
        token_hash=_hash_refresh_token(refresh_token),
        jti=jti,
        created_at=_now(),
        expires_at=expires_at,
    )
    db.add(record)
    db.commit()


def _get_session_by_token(db: Session, refresh_token: str) -> AuthSession | None:
    token_hash = _hash_refresh_token(refresh_token)
    stmt = select(AuthSession).where(AuthSession.token_hash == token_hash)
    return db.execute(stmt).scalar_one_or_none()


def _revoke_session(db: Session, session: AuthSession, *, reason: str) -> None:
    if session.revoked_at is not None:
        return
    session.revoked_at = _now()
    session.revoked_reason = reason
    db.commit()


def _revoke_all_sessions(db: Session, user_id: int, *, reason: str) -> None:
    now = _now()
    db.execute(
        update(AuthSession)
        .where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
        .values(revoked_at=now, revoked_reason=reason)
    )
    db.commit()


def _issue_tokens(db: Session, user: User) -> AuthTokens:
    settings = get_settings()
    now = _now()
    refresh_expires_at = now + timedelta(minutes=settings.auth_refresh_token_exp_minutes)
    refresh_jti = secrets.token_hex(16)

    refresh_token = security.create_refresh_token(user.id, refresh_jti, expires_at=refresh_expires_at)
    _persist_session(db, user.id, refresh_token, refresh_jti, refresh_expires_at)

    access_token = security.create_access_token(user.id, user.role.code, refresh_jti)
    return AuthTokens(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.auth_access_token_exp_minutes * 60,
        user=UserProfile.model_validate(user),
    )
