from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Backend"

    supabase_url: str | None = Field(default=None, alias="SUPABASE_URL")
    supabase_publishable_key: str | None = Field(default=None, alias="SUPABASE_PUBLISHABLE_KEY")
    supabase_anon_key: str | None = Field(default=None, alias="SUPABASE_ANON_KEY")

    supabase_db_host: str | None = Field(default=None, alias="SUPABASE_DB_HOST")
    supabase_db_port: int = Field(default=6543, alias="SUPABASE_DB_PORT")
    supabase_db_name: str = Field(default="postgres", alias="SUPABASE_DB_NAME")
    supabase_db_user: str | None = Field(default=None, alias="SUPABASE_DB_USER")
    supabase_db_password: str | None = Field(default=None, alias="SUPABASE_DB_PASSWORD")

    database_url: str | None = Field(default=None, alias="DATABASE_URL")

    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="models/gemini-2.5-flash", alias="GEMINI_MODEL")

    jwt_secret_key: str = Field(default="dev-secret-change-me", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=60, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    @field_validator("gemini_api_key", mode="before")
    @classmethod
    def _strip_gemini_api_key(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = str(value).strip()
        return trimmed or None

    @field_validator("gemini_model", mode="before")
    @classmethod
    def _normalize_gemini_model(cls, value: str) -> str:
        raw = str(value).strip()
        if raw.startswith("models/"):
            return raw
        return f"models/{raw}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
