from typing import AsyncGenerator
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import dotenv_values
from pathlib import Path
import os
from sqlalchemy.pool import NullPool, StaticPool

_env_path = Path(__file__).resolve().parents[2] / ".env"
# Load .env but allow explicit environment variable to override it. Tests set
# DATABASE_URL in os.environ to force a local SQLite DB for isolation.
config = dotenv_values(str(_env_path))
DATABASE_URL = (
    os.environ.get("DATABASE_URL")
    or config.get("DATABASE_URL")
    or "sqlite+aiosqlite:///./test.db"
)

# Ensure we use the async driver for postgres
if DATABASE_URL:
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    elif DATABASE_URL.startswith("postgresql+psycopg2://"):
        DATABASE_URL = DATABASE_URL.replace(
            "postgresql+psycopg2://", "postgresql+asyncpg://"
        )

# Configure sqlite to be usable from multiple threads in this local/dev setup.
# For production (Postgres) these options are ignored.
engine_kwargs = {"echo": False, "future": True}
if DATABASE_URL.startswith("sqlite"):
    # Allow connections to be used across threads (useful for uvicorn worker threads)
    engine_kwargs["connect_args"] = {"check_same_thread": False}

    if (
        ":memory:" in DATABASE_URL
        or "mode=memory" in DATABASE_URL
        or DATABASE_URL == "sqlite+aiosqlite://"
    ):
        # For in-memory DBs, we need StaticPool to share the same connection/DB across threads
        # and prevent it from being dropped when the connection closes.
        engine_kwargs["poolclass"] = StaticPool
    else:
        # Use NullPool to avoid reusing connections across threads in a way that
        # can lead to 'SQLite objects created in a thread can only be used in that same thread.'
        engine_kwargs["poolclass"] = NullPool
elif "asyncpg" in DATABASE_URL or "postgresql" in DATABASE_URL:
    # Use NullPool for asyncpg to avoid connection pool issues with uvicorn's async handling.
    # QueuePool (default) can cause async connection deadlocks in certain edge cases.
    engine_kwargs["poolclass"] = NullPool

engine = create_async_engine(DATABASE_URL, **engine_kwargs)

# Create session factory at module level for proper initialization
async_session_factory = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


async def init_db() -> None:
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
        # Note: Alembic commands are typically sync, so we might need to run them in a thread
        # or just rely on external migration scripts for production.
        # For now, we'll skip auto-migration in async init_db for postgres and assume
        # the deployment pipeline handles `alembic upgrade head`.
        pass
    else:
        # Non-Postgres (e.g., SQLite tests/dev) — create tables directly.
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
