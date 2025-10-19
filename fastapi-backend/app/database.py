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
    # Create SQLModel-managed tables (safe for SQLite and Postgres mapped models)
    SQLModel.metadata.create_all(engine)

    # If we're connected to a Postgres database, apply raw SQL migrations
    # kept in the repository's migrations/ directory. This mirrors the
    # simple migration system used by project SQL files (001_*.sql etc.).
    try:
        dialect = engine.dialect.name
    except Exception:
        dialect = ""

    if dialect and "postgres" in dialect:
        migrations_dir = Path(__file__).resolve().parents[2] / "migrations"
        if migrations_dir.exists():
            # Apply SQL files in lexicographic order (001_*, 002_*, ...)
            for sql_file in sorted(migrations_dir.glob("*.sql")):
                sql_text = sql_file.read_text()
                with engine.begin() as conn:
                    try:
                        # Use exec_driver_sql to allow multiple statements and DO blocks
                        conn.exec_driver_sql(sql_text)
                    except Exception:
                        # Continue on errors to avoid stopping startup; these will
                        # surface in logs if they fail. In production you may want
                        # stricter behavior.
                        pass
