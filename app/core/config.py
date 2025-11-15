from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "AB Planner API"
    api_prefix: str = "/api/v1"
    default_user_id: int = 1
    
    db_host: str = Field("db", alias="POSTGRES_HOST")
    db_port: int = Field(5432, alias="POSTGRES_PORT")
    db_name: str = Field("ab_planner", alias="POSTGRES_DB")
    db_user: str = Field("postgres", alias="POSTGRES_USER")
    db_password: str = Field("change_me", alias="POSTGRES_PASSWORD")
    
    model_config = SettingsConfigDict(env_file=".env")
    


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings() # type: ignore
