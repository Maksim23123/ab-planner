import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import SessionLocal, ensure_database
from app.core.run_migrations import ensure_schema_up_to_date
from app.services.push_service import process_outbox
from app.scripts.check_db import check_db
from app.scripts.cleanup_auth_sessions import cleanup_auth_sessions
from app.scripts.cleanup_change_logs import cleanup_change_logs


async def _run_periodic_cleanup(
    stop_event: asyncio.Event,
    interval_hours: int = 24,
    grace_days: int = 7,
    audit_retention_days: int = 90,
) -> None:
    """Background task to prune expired auth sessions and stale audit logs on a fixed interval."""
    interval = interval_hours * 3600
    while not stop_event.is_set():
        try:
            cleanup_auth_sessions(grace_days=grace_days)
        except Exception:
            # Swallow exceptions to avoid crashing the app; could add logging here.
            pass
        try:
            cleanup_change_logs(max_age_days=audit_retention_days)
        except Exception:
            # Swallow exceptions to avoid crashing the app; could add logging here.
            pass
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
        except asyncio.TimeoutError:
            continue


def _process_outbox_batch(
    *,
    server_key: str,
    service_account_json: str,
    project_id: str,
    batch_size: int,
    retry_failed: bool,
    max_attempts: int,
    retry_backoff_seconds: int,
) -> None:
    """Run a single outbox batch in a worker thread to avoid blocking the event loop."""
    if not server_key and not service_account_json:
        return
    with SessionLocal() as session:
        process_outbox(
            session,
            server_key=server_key,
            service_account_json=service_account_json,
            project_id=project_id,
            limit=batch_size,
            retry_failed=retry_failed,
            max_attempts=max_attempts,
            retry_backoff_seconds=retry_backoff_seconds,
        )


async def _run_notification_sender(
    stop_event: asyncio.Event,
    *,
    server_key: str,
    service_account_json: str,
    project_id: str,
    interval_seconds: int = 60,
    batch_size: int = 50,
    retry_failed: bool = True,
    max_attempts: int = 3,
    retry_backoff_seconds: int = 300,
) -> None:
    if not server_key and not service_account_json:
        return

    while not stop_event.is_set():
        try:
            await asyncio.to_thread(
                _process_outbox_batch,
                server_key=server_key,
                service_account_json=service_account_json,
                project_id=project_id,
                batch_size=batch_size,
                retry_failed=retry_failed,
                max_attempts=max_attempts,
                retry_backoff_seconds=retry_backoff_seconds,
            )
        except Exception:
            # Swallow exceptions to keep the sender loop alive; add logging if needed.
            pass
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
        except asyncio.TimeoutError:
            continue


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_database()
    ensure_schema_up_to_date()

    try:
        cleanup_auth_sessions()
        cleanup_change_logs()
    except Exception:
        # Swallow exceptions to avoid blocking startup; could add logging.
        pass

    settings = get_settings()
    stop_event = asyncio.Event()
    cleanup_task = asyncio.create_task(_run_periodic_cleanup(stop_event))
    sender_task = asyncio.create_task(
        _run_notification_sender(
            stop_event,
            server_key=settings.fcm_server_key,
            service_account_json=settings.fcm_service_account_json,
            project_id=settings.fcm_project_id,
            interval_seconds=60,
            batch_size=50,
        )
    )
    try:
        yield
    finally:
        stop_event.set()
        await asyncio.gather(cleanup_task, sender_task)


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title=settings.project_name, lifespan=lifespan)
    application.include_router(api_router, prefix=settings.api_prefix)

    check_db()

    @application.get("/")
    def read_root() -> dict[str, str]:
        return {"service": settings.project_name, "status": "ok"}

    return application


app = create_app()
