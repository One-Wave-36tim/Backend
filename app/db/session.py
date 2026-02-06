from collections.abc import Generator
from urllib.parse import quote_plus

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
_engine: Engine | None = None
_session_local: sessionmaker[Session] | None = None


def _resolve_database_url() -> str:
    if settings.database_url and "<db_user>" not in settings.database_url:
        return settings.database_url

    if (
        settings.supabase_db_host
        and settings.supabase_db_user
        and settings.supabase_db_password
        and settings.supabase_db_name
    ):
        encoded_password = quote_plus(settings.supabase_db_password)
        return (
            f"postgresql+psycopg://{settings.supabase_db_user}:{encoded_password}"
            f"@{settings.supabase_db_host}:{settings.supabase_db_port}/{settings.supabase_db_name}"
            "?sslmode=require"
        )

    raise RuntimeError("DB config is missing. Set DATABASE_URL or SUPABASE_DB_* values in .env.")


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(_resolve_database_url(), pool_pre_ping=True)
    return _engine


def get_session_local() -> sessionmaker[Session]:
    global _session_local
    if _session_local is None:
        _session_local = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
            class_=Session,
        )
    return _session_local


def get_db() -> Generator[Session, None, None]:
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()


engine = get_engine
SessionLocal = get_session_local
