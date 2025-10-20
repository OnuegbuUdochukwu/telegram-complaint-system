import os
import sys
from typing import Callable, Tuple

import pytest

# Ensure we can import the backend package located under fastapi-backend/
REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
BACKEND_PATH = os.path.join(REPO_ROOT, "fastapi-backend")
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

from sqlmodel import Session

import app.database as database
import app.auth as auth


@pytest.fixture(scope="session")
def db_engine():
    return database.engine


@pytest.fixture
def make_porter(db_engine) -> Callable[[str, str], Tuple[str, str]]:
    """Return a factory that creates a porter directly in the DB and returns (id, token)."""

    def _create(email: str, role: str = "porter"):
        with Session(db_engine) as session:
            # create_porter is idempotent (returns existing if present)
            porter = auth.create_porter(session, full_name=email.split("@")[0], password="testpass", email=email, role=role)
            token = auth.create_access_token(subject=porter.id, role=(porter.role or "porter"))
            return porter.id, token

    return _create


@pytest.fixture
def admin_token(make_porter):
    pid, token = make_porter("admin-in-tests@example.com", role="admin")
    return token
