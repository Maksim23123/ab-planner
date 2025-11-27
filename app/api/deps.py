from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import NamedTuple

from app.core.database import SessionLocal
from app.core import security
from app.models import AuthSession
from app.models.users import User


ALLOWED_ROLES = {"student", "lecturer", "admin"}
auth_scheme = HTTPBearer(auto_error=False)


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
    credentials: HTTPAuthorizationCredentials | None = Depends(auth_scheme),
) -> CurrentActor:
    """Resolve the current actor from a bearer access token."""

    if credentials is None:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    try:
        payload = security.decode_token(credentials.credentials, security.ACCESS_TOKEN_TYPE)
    except security.AuthTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid access token") from exc

    user_id = payload.get("user_id")
    session_jti = payload.get("session_jti")
    if not isinstance(user_id, int):
        raise HTTPException(status_code=401, detail="Invalid token payload")
    if not isinstance(session_jti, str):
        raise HTTPException(status_code=401, detail="Invalid token payload")

    session = db.scalar(select(AuthSession).where(AuthSession.jti == session_jti))
    now = datetime.now(timezone.utc)
    if (
        session is None
        or session.user_id != user_id
        or session.revoked_at is not None
        or session.expires_at <= now
    ):
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    role = (getattr(user.role, "code", None) or "").lower()
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
