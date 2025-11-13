from fastapi import APIRouter

from app.api.routes import groups, lessons, notifications, programs, selections, users


api_router = APIRouter()
api_router.include_router(users.router)
api_router.include_router(programs.router)
api_router.include_router(groups.router)
api_router.include_router(lessons.router)
api_router.include_router(notifications.router)
api_router.include_router(selections.router)
