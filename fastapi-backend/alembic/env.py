import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

sys.path.insert(0, "./")

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Allow alembic CLI to read DATABASE_URL from project's .env so
# the user doesn't have to manually edit alembic.ini.
from dotenv import dotenv_values
from pathlib import Path
_env_path = Path(__file__).resolve().parents[1] / ".env"
env = dotenv_values(str(_env_path))
DATABASE_URL = env.get("DATABASE_URL") or ""
if DATABASE_URL:
    print(f"DEBUG: Alembic using DATABASE_URL: {DATABASE_URL}")
    config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Interpret the config file for Python logging.
fileConfig(config.config_file_name)

# Import the app's metadata
from app.database import engine
from app.models import SQLModel
target_metadata = SQLModel.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


import asyncio

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    connectable = engine
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

def run_migrations_online():
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
