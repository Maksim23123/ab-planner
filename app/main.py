from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import ensure_database

from app.scripts.check_db import check_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_database()
    yield

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
