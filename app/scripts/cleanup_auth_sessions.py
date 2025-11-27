"""Prune expired auth sessions.

Run daily (e.g., via cron) to delete:
- revoked sessions that have passed expiry; and
- any session older than a grace window past expiry.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, delete, or_

from app.core.database import SessionLocal
from app.models import AuthSession


def cleanup_auth_sessions(grace_days: int = 7) -> int:
    """Delete expired or revoked auth sessions.

    - Revoked sessions are removed once expired.
    - All sessions are removed after an additional grace period.
    """
    now = datetime.now(timezone.utc)
    hard_cutoff = now - timedelta(days=grace_days)

    stmt = delete(AuthSession).where(
        or_(
            and_(AuthSession.expires_at < now, AuthSession.revoked_at.isnot(None)),
            AuthSession.expires_at < hard_cutoff,
        )
    )

    with SessionLocal() as session:
        result = session.execute(stmt)
        session.commit()
        deleted = result.rowcount or 0
    return deleted


def main() -> None:
    parser = argparse.ArgumentParser(description="Prune expired auth sessions")
    parser.add_argument(
        "--grace-days",
        type=int,
        default=7,
        help="Delete all sessions this many days after expiry (default: 7)",
    )
    args = parser.parse_args()
    deleted = cleanup_auth_sessions(grace_days=args.grace_days)
    print(f"Deleted {deleted} auth session(s).")


if __name__ == "__main__":
    main()
