from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Optional

import httpx
import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import FcmToken, NotificationOutbox

FCM_SEND_URL_V1 = "https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
GOOGLE_OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
FCM_SCOPE = "https://www.googleapis.com/auth/firebase.messaging"


def _load_service_account(raw: str) -> dict:
    """Parse service account JSON from inline content or a filesystem path."""
    if not raw:
        return {}
    raw = raw.strip()
    if raw.startswith("{"):
        return json.loads(raw)
    path = Path(raw)
    if not path.exists():
        raise FileNotFoundError(f"Service account file not found: {raw}")
    return json.loads(path.read_text())


class FcmV1Client:
    """Minimal FCM HTTP v1 client using a service account."""

    def __init__(self, service_account: dict, project_id: str | None = None):
        if not service_account:
            raise ValueError("Service account is required for FCM v1 client")
        self.service_account = service_account
        self.project_id = project_id or service_account.get("project_id")
        if not self.project_id:
            raise ValueError("project_id missing; set FCM_PROJECT_ID or include in service account")
        self._access_token: Optional[str] = None
        self._token_exp: datetime | None = None

    def _ensure_access_token(self) -> str:
        now = datetime.now(timezone.utc)
        if self._access_token and self._token_exp and now < self._token_exp - timedelta(seconds=60):
            return self._access_token

        sa = self.service_account
        private_key = sa.get("private_key")
        client_email = sa.get("client_email")
        if not private_key or not client_email:
            raise ValueError("Service account missing private_key or client_email")

        claims = {
            "iss": client_email,
            "scope": FCM_SCOPE,
            "aud": GOOGLE_OAUTH_TOKEN_URL,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=55)).timestamp()),
        }
        assertion = jwt.encode(
            claims,
            private_key,
            algorithm="RS256",
            headers={"kid": sa.get("private_key_id")},
        )

        response = httpx.post(
            GOOGLE_OAUTH_TOKEN_URL,
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": assertion,
            },
            timeout=10.0,
        )
        if response.status_code != 200:
            raise RuntimeError(f"Failed to obtain FCM access token: {response.text}")

        body = response.json()
        self._access_token = body.get("access_token")
        expires_in = int(body.get("expires_in", 3600))
        self._token_exp = now + timedelta(seconds=expires_in)
        return self._access_token

    def send(self, token: str, payload: dict) -> tuple[bool, Optional[str]]:
        """Send push to a single token. Returns (success, error_code_if_any)."""
        access_token = self._ensure_access_token()
        url = FCM_SEND_URL_V1.format(project_id=self.project_id)

        def _stringify(data: dict | None) -> dict[str, str]:
            result: dict[str, str] = {}
            if not data:
                return result
            for key, value in data.items():
                if value is None:
                    continue
                if isinstance(value, (dict, list)):
                    result[key] = json.dumps(value, default=str)
                elif isinstance(value, (datetime,)):
                    result[key] = value.isoformat()
                else:
                    result[key] = str(value)
            return result

        message = {
            "token": token,
            "notification": {
                "title": payload.get("title") or "Notification",
                "body": payload.get("body") or "",
            },
            "data": _stringify(payload.get("data")),
        }
        response = httpx.post(
            url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={"message": message},
            timeout=10.0,
        )
        if response.status_code == 200:
            return True, None

        try:
            body = response.json()
            error_status = (body.get("error") or {}).get("status")
        except Exception:
            error_status = None
        return False, error_status or f"http_{response.status_code}"


def _send_to_token(server_key: str | None, client: FcmV1Client | None, token: str, payload: dict) -> tuple[bool, Optional[str]]:
    """Send push via either legacy server key or FCM HTTP v1 client."""
    if client:
        return client.send(token, payload)
    if not server_key:
        return False, "missing_credentials"

    def _stringify(data: dict | None) -> dict[str, str]:
        result: dict[str, str] = {}
        if not data:
            return result
        for key, value in data.items():
            if value is None:
                continue
            if isinstance(value, (dict, list)):
                result[key] = json.dumps(value, default=str)
            elif isinstance(value, (datetime,)):
                result[key] = value.isoformat()
            else:
                result[key] = str(value)
        return result

    headers = {
        "Authorization": f"key={server_key}",
        "Content-Type": "application/json",
    }
    message = {
        "to": token,
        "priority": "high",
        "notification": {
            "title": payload.get("title") or "Notification",
            "body": payload.get("body") or "",
        },
        "data": _stringify(payload.get("data")),
    }
    response = httpx.post("https://fcm.googleapis.com/fcm/send", headers=headers, json=message, timeout=10.0)
    if response.status_code != 200:
        return False, f"http_{response.status_code}"

    body = response.json()
    results = body.get("results") or []
    if not results:
        return body.get("failure", 0) == 0, None

    first = results[0]
    if "error" in first:
        return False, first.get("error")
    return True, None


def _load_tokens(db: Session, user_id: int) -> list[FcmToken]:
    stmt = select(FcmToken).where(FcmToken.user_id == user_id)
    return list(db.scalars(stmt).all())


def process_outbox(
    db: Session,
    *,
    server_key: str | None = None,
    service_account_json: str | None = None,
    project_id: str | None = None,
    limit: int = 50,
    retry_failed: bool = False,
) -> dict[str, int]:
    """Send queued notification outbox items via FCM.

    Marks notifications as sent/failed and prunes invalid tokens.
    """
    sa = _load_service_account(service_account_json or "")
    client = None
    if sa:
        try:
            client = FcmV1Client(sa, project_id=project_id or sa.get("project_id"))
        except Exception:
            # Fail back to server key if provided.
            client = None
    if not client and not server_key:
        return {"processed": 0, "sent": 0, "failed": 0, "skipped": 0}

    target_statuses: Iterable[str] = ("queued",)
    if retry_failed:
        target_statuses = ("queued", "failed")

    stmt = (
        select(NotificationOutbox)
        .where(NotificationOutbox.status.in_(target_statuses))
        .order_by(NotificationOutbox.created_at)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    notifications = list(db.scalars(stmt).all())

    summary = {"processed": 0, "sent": 0, "failed": 0, "skipped": 0}
    if not notifications:
        return summary

    now = datetime.now(timezone.utc)
    for record in notifications:
        summary["processed"] += 1
        tokens = _load_tokens(db, record.user_id)
        record.attempts = (record.attempts or 0) + 1

        if not tokens:
            record.status = "sent"
            record.sent_at = now
            summary["sent"] += 1
            continue

        payload = record.payload or {}
        successes = 0
        failures = 0
        invalid_tokens: list[FcmToken] = []

        for token in tokens:
            ok, error = _send_to_token(server_key, client, token.token, payload)
            if ok:
                successes += 1
                continue

            failures += 1
            if error in {"NotRegistered", "InvalidRegistration", "UNREGISTERED"}:
                invalid_tokens.append(token)

        for token in invalid_tokens:
            db.delete(token)

        if successes > 0 and failures == 0:
            record.status = "sent"
            record.sent_at = now
            summary["sent"] += 1
        elif successes > 0:
            # Partial success: keep status as sent to avoid reprocessing, but note failure count.
            record.status = "sent"
            record.sent_at = now
            summary["sent"] += 1
        else:
            record.status = "failed"
            summary["failed"] += 1

    db.commit()
    return summary
