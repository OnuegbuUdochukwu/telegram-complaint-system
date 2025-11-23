import os
import sys
import socket
import subprocess
import time
from pathlib import Path
from typing import Callable, Tuple
from urllib.parse import urlparse

import pytest
from sqlmodel import Session, SQLModel

# Ensure we can import the backend package located under fastapi-backend/
REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = REPO_ROOT / "fastapi-backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

# For test isolation, force a SQLite DB and allow dev registration during pytest runs.
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("ALLOW_DEV_REGISTER", "1")
os.environ.setdefault("TEST_BACKEND_URL", "http://127.0.0.1:8000")
os.environ.setdefault("TEST_ADMIN_EMAIL", "admin@test.local")
os.environ.setdefault("TEST_ADMIN_PASSWORD", "testpass123")
os.environ.setdefault("TEST_ADMIN_ALT_PASSWORD", "adminpassword")
os.environ.setdefault("AUTO_ADMIN_EMAILS", "admin@test.local,admin-purge@test.com")

db_url = os.environ["DATABASE_URL"]
if db_url.startswith("sqlite:///"):
    raw_path = db_url.split("sqlite:///", 1)[1]
    abs_path = (REPO_ROOT / raw_path).resolve()
    os.environ["DATABASE_URL"] = f"sqlite:///{abs_path}"

import app.database as database
import app.auth as auth


def _sqlite_path_from_url(url: str) -> Path | None:
    if not url.startswith("sqlite:///"):
        return None
    raw = url.split("sqlite:///", 1)[1]
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


def _ensure_seed_users():
    admin_email = os.environ.get("TEST_ADMIN_EMAIL", "admin@test.local")
    admin_password = os.environ.get("TEST_ADMIN_PASSWORD", "testpass123")
    with Session(database.engine) as session:
        auth.create_porter(session, full_name="Test Admin", email=admin_email, password=admin_password, role="admin")
        auth.create_porter(session, full_name="Purge Admin", email="admin-purge@test.com", password="adminpass123", role="admin")


@pytest.fixture(scope="session", autouse=True)
def backend_server():
    """Start a uvicorn server once for integration tests and tear it down afterwards."""
    db_path = _sqlite_path_from_url(os.environ["DATABASE_URL"])
    if db_path:
        db_path.unlink(missing_ok=True)

    # Ensure schema + seed data exist before the server starts
    SQLModel.metadata.create_all(database.engine)
    _ensure_seed_users()

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


@pytest.fixture(scope="session")
def db_engine():
    # Ensure tables are created for the test database to avoid NOT NULL/PK issues
    engine = database.engine
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def make_porter(db_engine) -> Callable[[str, str], Tuple[str, str]]:
    """Return a factory that creates a porter directly in the DB and returns (id, token)."""

    def _create(email: str, role: str = "porter"):
        with Session(db_engine) as session:
            porter = auth.create_porter(
                session,
                full_name=email.split("@")[0],
                password="testpass",
                email=email,
                role=role,
            )
            token = auth.create_access_token(subject=porter.id, role=(porter.role or "porter"))
            return porter.id, token

    return _create


@pytest.fixture
def admin_token(make_porter):
    pid, token = make_porter("admin-in-tests@example.com", role="admin")
    return token
