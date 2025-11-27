from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import get_settings
from app.schemas.auth import (
    AuthTokens,
    LogoutRequest,
    MicrosoftAuthRequest,
    MicrosoftLoginUrlResponse,
    RefreshRequest,
)
from app.services import auth_service


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/microsoft/token", response_model=AuthTokens)
async def microsoft_login(
    payload: MicrosoftAuthRequest,
    db: Session = Depends(deps.get_db),
):
    return await auth_service.login_with_microsoft(db, payload)


@router.get("/microsoft/login-url", response_model=MicrosoftLoginUrlResponse)
def microsoft_login_url(
    code_challenge: str = Query(..., description="PKCE code challenge"),
    state: str | None = Query(None, description="Optional state to echo back after login"),
):
    settings = get_settings()
    params = {
        "client_id": settings.ms_client_id,
        "response_type": "code",
        "redirect_uri": settings.ms_redirect_uri,
        "response_mode": "query",
        "scope": settings.ms_scope,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    if state:
        params["state"] = state

    base_url = f"https://login.microsoftonline.com/{settings.ms_tenant}/oauth2/v2.0/authorize"
    return MicrosoftLoginUrlResponse(authorization_url=f"{base_url}?{urlencode(params)}")


@router.post("/refresh", response_model=AuthTokens)
def refresh_tokens(
    payload: RefreshRequest,
    db: Session = Depends(deps.get_db),
):
    return auth_service.refresh_session(db, payload.refresh_token)


@router.post("/logout", status_code=204)
def logout(
    payload: LogoutRequest | None = None,
    db: Session = Depends(deps.get_db),
    actor: deps.CurrentActor = Depends(deps.get_current_actor),
):
    auth_service.logout(db, actor.user, payload)
