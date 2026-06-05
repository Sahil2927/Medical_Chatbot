import os
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.db.base import Base


def normalize_database_url(url: str) -> str:
    """Accept Render/Heroku ``postgres://`` URLs for SQLAlchemy + psycopg2."""
    normalized = url.strip()
    if normalized.startswith("postgres://"):
        return "postgresql+psycopg2://" + normalized[len("postgres://") :]
    if normalized.startswith("postgresql://") and "+psycopg2" not in normalized:
        return "postgresql+psycopg2://" + normalized[len("postgresql://") :]
    return normalized


def get_database_url() -> str:
    raw = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/mediassist",
    )
    return normalize_database_url(raw)


@lru_cache
def get_engine():
    url = get_database_url()
    kwargs: dict = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        if url.endswith(":memory:") or url == "sqlite://":
            kwargs["poolclass"] = StaticPool
    return create_engine(url, **kwargs)


def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)


def _ensure_message_metadata_column() -> None:
    from sqlalchemy import inspect, text

    engine = get_engine()
    inspector = inspect(engine)
    if "messages" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("messages")}
    if "metadata_json" in columns:
        return
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE messages ADD COLUMN metadata_json TEXT"))


def init_db() -> None:
    Base.metadata.create_all(bind=get_engine())
    _ensure_message_metadata_column()
    from src.db.seed import seed_providers

    seed_providers(get_session_factory())


def reset_engine_cache() -> None:
    get_engine.cache_clear()
