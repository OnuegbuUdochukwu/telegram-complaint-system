from typing import Generator
from sqlmodel import SQLModel, create_engine, Session
from dotenv import dotenv_values
from pathlib import Path
import os
from sqlalchemy import text as sa_text

_env_path = Path(__file__).resolve().parents[2] / ".env"
# Load .env but allow explicit environment variable to override it. Tests set
# DATABASE_URL in os.environ to force a local SQLite DB for isolation.
config = dotenv_values(str(_env_path))
DATABASE_URL = os.environ.get("DATABASE_URL") or config.get("DATABASE_URL") or "sqlite:///./test.db"

engine = create_engine(DATABASE_URL, echo=False)

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
