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

    ms_client_id: str = Field("change_me", alias="MS_CLIENT_ID")
    ms_client_secret: str = Field("change_me", alias="MS_CLIENT_SECRET")
    ms_tenant: str = Field("common", alias="MS_TENANT")
    ms_redirect_uri: str = Field("http://localhost:8000/docs", alias="MS_REDIRECT_URI")
    ms_scope: str = Field("openid profile email offline_access", alias="MS_SCOPE")
    ms_jwks_cache_seconds: int = Field(3600, alias="MS_JWKS_CACHE_SECONDS")

    auth_secret_key: str = Field("change_me_auth", alias="AUTH_SECRET_KEY")
    auth_access_token_exp_minutes: int = Field(60, alias="AUTH_ACCESS_TOKEN_EXPIRES_MINUTES")
    auth_refresh_token_exp_minutes: int = Field(60 * 24 * 30, alias="AUTH_REFRESH_TOKEN_EXPIRES_MINUTES")
    auth_default_role_code: str = Field("student", alias="AUTH_DEFAULT_ROLE")

    # Seeder options (optional)
    seed_admin: bool = Field(False, alias="SEED_ADMIN")
    admin_email: str = Field("admin@example.edu", alias="ADMIN_EMAIL")
    admin_name: str = Field("Admin User", alias="ADMIN_NAME")

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow",  # ignore unrelated env vars (e.g., seeding toggles)
    )
    


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings() # type: ignore
