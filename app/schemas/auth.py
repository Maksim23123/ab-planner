from __future__ import annotations

from pydantic import AnyHttpUrl, BaseModel

from app.schemas.users import UserProfile


class MicrosoftAuthRequest(BaseModel):
    code: str
    code_verifier: str
    redirect_uri: AnyHttpUrl


class RefreshRequest(BaseModel):
    refresh_token: str


class AuthTokens(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: UserProfile


class MicrosoftLoginUrlResponse(BaseModel):
    authorization_url: AnyHttpUrl
