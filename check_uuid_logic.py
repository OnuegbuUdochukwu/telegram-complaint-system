
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "")
print(f"DATABASE_URL: {DATABASE_URL}")

_USE_PG_UUID = any(x in DATABASE_URL for x in ("postgres://", "postgresql://", "psycopg2"))
print(f"_USE_PG_UUID: {_USE_PG_UUID}")
