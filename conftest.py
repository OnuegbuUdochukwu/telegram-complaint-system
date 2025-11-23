import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
BACKEND_PATH = REPO_ROOT / "fastapi-backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
db_url = os.environ["DATABASE_URL"]
if db_url.startswith("sqlite:///"):
    raw_path = db_url.split("sqlite:///", 1)[1]
    abs_path = (REPO_ROOT / raw_path).resolve()
    os.environ["DATABASE_URL"] = f"sqlite:///{abs_path}"

os.environ.setdefault("ALLOW_DEV_REGISTER", "1")
os.environ.setdefault("TEST_ADMIN_EMAIL", "admin@test.local")
os.environ.setdefault("TEST_ADMIN_PASSWORD", "testpass123")
os.environ.setdefault("TEST_ADMIN_ALT_PASSWORD", "adminpassword")
os.environ.setdefault("AUTO_ADMIN_EMAILS", "admin@test.local,admin-purge@test.com")

