from functools import lru_cache
from pydantic import BaseModel


class Settings(BaseModel):
    project_name: str = "AB Planner API"
    api_prefix: str = "/api/v1"
    default_user_id: int = 1


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
