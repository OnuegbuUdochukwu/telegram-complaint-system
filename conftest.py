import os
import sys
import socket
import subprocess
import time
import asyncio
from pathlib import Path
from typing import Callable, Tuple
from urllib.parse import urlparse

import pytest
import pytest_asyncio
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker

REPO_ROOT = Path(__file__).parent

# Set environment variables BEFORE importing app modules to bypass strict checks
os.environ["JWT_SECRET"] = "test-secret-key-for-pytest-only-12345"
# Use aiosqlite for async SQLite testing
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["STORAGE_PROVIDER"] = "local"

# Add the backend directory to sys.path so imports work
BACKEND_PATH = Path(__file__).parent / "fastapi-backend"
sys.path.append(str(BACKEND_PATH))

# For test isolation, allow dev registration during pytest runs.
os.environ.setdefault("ALLOW_DEV_REGISTER", "1")
os.environ.setdefault("TEST_BACKEND_URL", "http://127.0.0.1:8000")
os.environ.setdefault("TEST_ADMIN_EMAIL", "admin@test.local")
os.environ.setdefault("TEST_ADMIN_PASSWORD", "testpass123")
os.environ.setdefault("TEST_ADMIN_ALT_PASSWORD", "adminpassword")
os.environ.setdefault("AUTO_ADMIN_EMAILS", "admin@test.local,admin-purge@test.com")

db_url = os.environ["DATABASE_URL"]
if db_url.startswith("sqlite+aiosqlite:///"):
    raw_path = db_url.split("sqlite+aiosqlite:///", 1)[1]
    abs_path = (REPO_ROOT / raw_path).resolve()
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{abs_path}"

import app.database as database
import app.auth as auth


def _sqlite_path_from_url(url: str) -> Path | None:
    if not url.startswith("sqlite+aiosqlite:///"):
        return None
    raw = url.split("sqlite+aiosqlite:///", 1)[1]
    return (REPO_ROOT / raw).resolve()


def _wait_for_port(host: str, port: int, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError(f"Backend server did not start on {host}:{port} within {timeout}s")


async def _ensure_seed_users():
    admin_email = os.environ.get("TEST_ADMIN_EMAIL", "admin@test.local")
    admin_password = os.environ.get("TEST_ADMIN_PASSWORD", "testpass123")
    
    # Create a dedicated async engine for seeding to avoid event loop issues
    seed_engine = create_async_engine(os.environ["DATABASE_URL"])
    async_session = sessionmaker(seed_engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        await auth.create_porter(session, full_name="Test Admin", email=admin_email, password=admin_password, role="admin")
        await auth.create_porter(session, full_name="Purge Admin", email="admin-purge@test.com", password="adminpass123", role="admin")
    
    await seed_engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def backend_server():
    """Start a uvicorn server once for integration tests and tear it down afterwards."""
    # Clean up old DB
    db_path = _sqlite_path_from_url(os.environ["DATABASE_URL"])
    if db_path:
        db_path.unlink(missing_ok=True)

    # Initialize DB schema synchronously for the test session
    # We use a sync engine just for the initial CREATE TABLE
    from sqlmodel import create_engine
    sync_db_url = os.environ["DATABASE_URL"].replace("sqlite+aiosqlite", "sqlite")
    sync_engine = create_engine(sync_db_url)
    SQLModel.metadata.create_all(sync_engine)
    
    # Seed users using async
    asyncio.run(_ensure_seed_users())

    parsed = urlparse(os.environ["TEST_BACKEND_URL"])
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    env = os.environ.copy()
    env.setdefault("BACKEND_SERVICE_TOKEN", "test-service-token")
    env.setdefault("APP_ENV", "test")

    def _start_instance(bind_host: str, bind_port: int) -> subprocess.Popen:
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            bind_host,
            "--port",
            str(bind_port),
        ]
        proc = subprocess.Popen(
            cmd,
            cwd=str(BACKEND_PATH),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _wait_for_port(bind_host, bind_port, timeout=30)
        return proc

    ports_to_start = {(host, port), ("127.0.0.1", 8001)}
    servers = []
    try:
        for bind_host, bind_port in sorted(ports_to_start):
            servers.append(_start_instance(bind_host, bind_port))
        yield
    finally:
        for proc in servers:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    # Return the app's async engine
    return database.engine


@pytest_asyncio.fixture(scope="function")
async def make_porter(db_engine) -> Callable[[str, str], Tuple[str, str]]:
    """Return a factory that creates a porter directly in the DB and returns (id, token)."""

    async def _create(email: str, role: str = "porter"):
        async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            porter = await auth.create_porter(
                session,
                full_name=email.split("@")[0],
                password="testpass",
                email=email,
                role=role,
            )
            token = auth.create_access_token(subject=porter.id, role=(porter.role or "porter"))
            return porter.id, token

    return _create


@pytest_asyncio.fixture(scope="function")
async def admin_token(make_porter):
    pid, token = await make_porter("admin-in-tests@example.com", role="admin")
    return token
