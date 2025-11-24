from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import jwt

from app.core.config import get_settings


ALGORITHM = "HS256"
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


class AuthTokenError(Exception):
    """Raised when creating or decoding auth tokens fails."""


def _create_token(data: dict[str, Any], expires_delta: timedelta, token_type: Literal["access", "refresh"]) -> str:
    payload = data.copy()
    payload.update(
        {
            "exp": datetime.now(timezone.utc) + expires_delta,
            "type": token_type,
        }
    )
    settings = get_settings()
    return jwt.encode(payload, settings.auth_secret_key, algorithm=ALGORITHM)


def create_access_token(user_id: int, role: str) -> str:
    settings = get_settings()
    expires_delta = timedelta(minutes=settings.auth_access_token_exp_minutes)
    return _create_token({"sub": str(user_id), "user_id": user_id, "role": role}, expires_delta, ACCESS_TOKEN_TYPE)


def create_refresh_token(user_id: int) -> str:
    settings = get_settings()
    expires_delta = timedelta(minutes=settings.auth_refresh_token_exp_minutes)
    return _create_token({"sub": str(user_id), "user_id": user_id}, expires_delta, REFRESH_TOKEN_TYPE)


def decode_token(token: str, expected_type: Literal["access", "refresh"]) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, get_settings().auth_secret_key, algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:  # pragma: no cover - library raises many subclasses
        raise AuthTokenError("Token decoding failed") from exc

    token_type = payload.get("type")
    if token_type != expected_type:
        raise AuthTokenError("Invalid token type")

    return payload
