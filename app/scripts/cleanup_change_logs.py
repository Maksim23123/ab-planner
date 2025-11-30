"""Prune old audit change logs.

Run periodically (e.g., via cron) to delete entries older than a retention window.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

from app.core.database import SessionLocal
from app.models import ChangeLog


def cleanup_change_logs(max_age_days: int = 90) -> int:
    """Delete audit entries older than the retention window."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    stmt = delete(ChangeLog).where(ChangeLog.created_at < cutoff)

    with SessionLocal() as session:
        result = session.execute(stmt)
        session.commit()
        deleted = result.rowcount or 0
    return deleted


def main() -> None:
    parser = argparse.ArgumentParser(description="Prune audit change logs")
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=90,
        help="Delete logs older than this many days (default: 90)",
    )
    args = parser.parse_args()
    deleted = cleanup_change_logs(max_age_days=args.max_age_days)
    print(f"Deleted {deleted} change log record(s).")


if __name__ == "__main__":
    main()
