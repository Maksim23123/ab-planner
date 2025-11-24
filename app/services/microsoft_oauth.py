from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import HTTPException, status
import jwt
from jwt import algorithms

from app.core.config import get_settings


@dataclass
class MicrosoftTokenResult:
    access_token: str
    refresh_token: str | None
    expires_in: int
    id_token: str
    claims: dict[str, Any]


class MicrosoftOAuthClient:
    """Handles exchanging authorization codes for Microsoft tokens."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._jwks_cache: list[dict[str, Any]] = []
        self._jwks_expires_at: float = 0.0

    @property
    def _token_url(self) -> str:
        tenant = self._settings.ms_tenant
        return f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"

    @property
    def _jwks_url(self) -> str:
        tenant = self._settings.ms_tenant
        return f"https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys"

    async def exchange_code(self, *, code: str, code_verifier: str, redirect_uri: str) -> MicrosoftTokenResult:
        self._validate_redirect_uri(redirect_uri)
        data = {
            "client_id": self._settings.ms_client_id,
            "scope": self._settings.ms_scope,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
            "client_secret": self._settings.ms_client_secret,
            "code_verifier": code_verifier,
        }

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(self._token_url, data=data)

        try:
            payload = response.json()
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Invalid Microsoft response") from exc
        if response.status_code >= 400:
            detail = payload.get("error_description") or payload.get("error") or "Microsoft auth failed"
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

        id_token = payload.get("id_token")
        if not id_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing id_token in Microsoft response")

        claims = await self._decode_id_token(id_token)
        return MicrosoftTokenResult(
            access_token=payload.get("access_token", ""),
            refresh_token=payload.get("refresh_token"),
            expires_in=int(payload.get("expires_in", 0) or 0),
            id_token=id_token,
            claims=claims,
        )

    def _validate_redirect_uri(self, redirect_uri: str) -> None:
        if redirect_uri != self._settings.ms_redirect_uri:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Redirect URI not allowed")

    async def _decode_id_token(self, id_token: str) -> dict[str, Any]:
        header = jwt.get_unverified_header(id_token)
        kid = header.get("kid")
        if not kid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing key id in token header")

        public_key = await self._get_public_key(kid)
        try:
            return jwt.decode(
                id_token,
                public_key,
                algorithms=[header.get("alg", "RS256")],
                audience=self._settings.ms_client_id,
                options={"verify_signature": True, "verify_iss": False},
            )
        except jwt.PyJWTError as exc:  # pragma: no cover - library exceptions are numerous
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id_token") from exc

    async def _get_public_key(self, kid: str):
        jwks = await self._get_jwks()
        for jwk_key in jwks:
            if jwk_key.get("kid") == kid:
                return algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk_key))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to find signing key")

    async def _get_jwks(self) -> list[dict[str, Any]]:
        now = time.time()
        if self._jwks_cache and now < self._jwks_expires_at:
            return self._jwks_cache

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(self._jwks_url)
            response.raise_for_status()
            try:
                data = response.json()
            except ValueError as exc:
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Invalid Microsoft JWKS response") from exc

        keys = data.get("keys") or []
        if not keys:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Microsoft JWKS unavailable")

        self._jwks_cache = keys
        self._jwks_expires_at = now + self._settings.ms_jwks_cache_seconds
        return keys


oauth_client = MicrosoftOAuthClient()
