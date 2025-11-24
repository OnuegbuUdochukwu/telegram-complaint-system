import sys
import os
from pathlib import Path

# Mimic conftest.py setup
backend_path = Path("fastapi-backend").resolve()
sys.path.append(str(backend_path))

os.environ["JWT_SECRET"] = "test-secret-key-for-pytest-only-12345"
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["STORAGE_PROVIDER"] = "local"

print("Attempting to import app.main...")
try:
    from app.main import app
    print("Successfully imported app.main")
except Exception as e:
    print(f"Failed to import app.main: {e}")
    import traceback
    traceback.print_exc()

print("\nAttempting to import test_presign_flow...")
try:
    # We need to add the test dir to path or import by file path logic, 
    # but for now let's just see if app.main works, which is the likely culprit.
    pass
except Exception as e:
    print(f"Failed: {e}")
