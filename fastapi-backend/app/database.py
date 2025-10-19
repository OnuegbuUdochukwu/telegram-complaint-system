from typing import Generator
from sqlmodel import SQLModel, create_engine, Session
from dotenv import dotenv_values
from pathlib import Path
from sqlalchemy import text as sa_text

config = dotenv_values("../.env")
DATABASE_URL = config.get("DATABASE_URL") or "sqlite:///./test.db"

engine = create_engine(DATABASE_URL, echo=False)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

def init_db() -> None:
    # For SQLite/local dev, create tables directly
    SQLModel.metadata.create_all(engine)

    # For Postgres, prefer running Alembic migrations so schema is managed.
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
            # If Alembic fails, fall back to create_all (safer for dev).
            SQLModel.metadata.create_all(engine)
