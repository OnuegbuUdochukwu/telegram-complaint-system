from typing import Generator
from sqlmodel import SQLModel, create_engine, Session
from dotenv import dotenv_values
from pathlib import Path
import os
from sqlalchemy import text as sa_text
from sqlalchemy.pool import NullPool, StaticPool

_env_path = Path(__file__).resolve().parents[2] / ".env"
# Load .env but allow explicit environment variable to override it. Tests set
# DATABASE_URL in os.environ to force a local SQLite DB for isolation.
config = dotenv_values(str(_env_path))
DATABASE_URL = os.environ.get("DATABASE_URL") or config.get("DATABASE_URL") or "sqlite:///./test.db"

# Configure sqlite to be usable from multiple threads in this local/dev setup.
# For production (Postgres) these options are ignored.
engine_kwargs = {"echo": False}
if DATABASE_URL.startswith("sqlite"):
    # Allow connections to be used across threads (useful for uvicorn worker threads)
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    
    if ":memory:" in DATABASE_URL or "mode=memory" in DATABASE_URL or DATABASE_URL == "sqlite://":
        # For in-memory DBs, we need StaticPool to share the same connection/DB across threads
        # and prevent it from being dropped when the connection closes.
        engine_kwargs["poolclass"] = StaticPool
    else:
        # Use NullPool to avoid reusing connections across threads in a way that
        # can lead to 'SQLite objects created in a thread can only be used in that same thread.'
        engine_kwargs["poolclass"] = NullPool

engine = create_engine(DATABASE_URL, **engine_kwargs)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

def init_db() -> None:
    # Decide whether to run Alembic migrations (Postgres) or create tables
    # directly (SQLite/local dev). Running create_all against an existing
    # Postgres database whose columns use native UUIDs can emit incompatible
    # DDL (mismatched types). Therefore, for Postgres we prefer Alembic.
    try:
        dialect = engine.dialect.name
    except Exception:
        dialect = ""

    if dialect and "postgres" in dialect:
        # Run Alembic programmatically to bring DB to latest revision.
        try:
            from alembic.config import Config
            from alembic import command

            alembic_cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
            # Ensure alembic.ini uses the same DB URL as our .env
            from dotenv import dotenv_values
            env = dotenv_values("../.env")
            if env.get("DATABASE_URL"):
                alembic_cfg.set_main_option("sqlalchemy.url", env.get("DATABASE_URL"))

            command.upgrade(alembic_cfg, "head")
        except Exception:
            # If Alembic fails for some reason, fall back to create_all as a last resort.
            SQLModel.metadata.create_all(engine)
    else:
        # Non-Postgres (e.g., SQLite tests/dev) — create tables directly.
        SQLModel.metadata.create_all(engine)
