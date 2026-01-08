from fastapi import APIRouter

from app.api.routes import (
    auth,
    fcm_tokens,
    groups,
    lessons,
    notifications,
    plans,
    programs,
    program_years,
    rooms,
    selections,
    specializations,
    subjects,
    users,
)


api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(programs.router)
api_router.include_router(program_years.router)
api_router.include_router(specializations.router)
api_router.include_router(groups.router)
api_router.include_router(subjects.router)
api_router.include_router(rooms.router)
api_router.include_router(lessons.router)
api_router.include_router(plans.router)
api_router.include_router(notifications.router)
api_router.include_router(fcm_tokens.router)
api_router.include_router(selections.router)
