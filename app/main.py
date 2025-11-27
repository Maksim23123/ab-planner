import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import ensure_database
from app.core.run_migrations import ensure_schema_up_to_date
from app.scripts.check_db import check_db
from app.scripts.cleanup_auth_sessions import cleanup_auth_sessions


async def _run_periodic_cleanup(stop_event: asyncio.Event, interval_hours: int = 24, grace_days: int = 7) -> None:
    """Background task to prune expired auth sessions on a fixed interval."""
    interval = interval_hours * 3600
    while not stop_event.is_set():
        try:
            cleanup_auth_sessions(grace_days=grace_days)
        except Exception:
            # Swallow exceptions to avoid crashing the app; could add logging here.
            pass
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
        except asyncio.TimeoutError:
            continue


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_database()
    ensure_schema_up_to_date()

    try:
        cleanup_auth_sessions()
    except Exception:
        # Swallow exceptions to avoid blocking startup; could add logging.
        pass

    stop_event = asyncio.Event()
    cleanup_task = asyncio.create_task(_run_periodic_cleanup(stop_event))
    try:
        yield
    finally:
        stop_event.set()
        await cleanup_task


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
