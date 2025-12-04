"""Send queued notification outbox items via FCM."""
from __future__ import annotations

import argparse

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.push_service import process_outbox


def send_queued_notifications(limit: int, retry_failed: bool) -> dict[str, int]:
    settings = get_settings()
    server_key = settings.fcm_server_key
    service_account_json = settings.fcm_service_account_json
    project_id = settings.fcm_project_id
    if not server_key and not service_account_json:
        print("FCM credentials not configured; set FCM_SERVICE_ACCOUNT_JSON or FCM_SERVER_KEY.")
        return {"processed": 0, "sent": 0, "failed": 0, "skipped": 0}

    with SessionLocal() as session:
        summary = process_outbox(
            session,
            server_key=server_key,
            service_account_json=service_account_json,
            project_id=project_id,
            limit=limit,
            retry_failed=retry_failed,
        )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Send queued notification outbox items via FCM")
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Max number of notifications to process in one run (default: 50)",
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Include previously failed notifications in this run",
    )
    args = parser.parse_args()
    summary = send_queued_notifications(limit=args.limit, retry_failed=args.retry_failed)
    print(
        f"Processed {summary.get('processed', 0)} notification(s): "
        f"sent={summary.get('sent', 0)}, failed={summary.get('failed', 0)}, "
        f"skipped={summary.get('skipped', 0)}."
    )


if __name__ == "__main__":
    main()
