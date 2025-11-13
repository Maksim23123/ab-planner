from fastapi import APIRouter, Query

from app.schemas.users import UserProfile
from app.services import mock_store

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfile)
def read_current_user(user_id: int | None = Query(default=None, description="Override user id")):
    return mock_store.get_user(user_id)
