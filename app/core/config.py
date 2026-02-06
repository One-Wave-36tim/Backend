from functools import lru_cache

from pydantic import Field
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
