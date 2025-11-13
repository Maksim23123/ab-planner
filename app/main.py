from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title=settings.project_name)
    application.include_router(api_router, prefix=settings.api_prefix)

    @application.get("/")
    def read_root() -> dict[str, str]:
        return {"service": settings.project_name, "status": "ok"}

    return application


app = create_app()
