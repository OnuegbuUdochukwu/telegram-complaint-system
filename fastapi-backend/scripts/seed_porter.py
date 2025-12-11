"""Small script to seed a porter or admin for local testing (Async version).

Usage:
    python fastapi-backend/scripts/seed_porter.py --name "Admin" --email admin@example.com --password secret --role admin
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Ensure project root is on sys.path if running locally
# In Docker, we set PYTHONPATH=. so this might not be needed, but harmless
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "fastapi-backend"))

from app.database import get_session, init_db
from app import auth


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--email")
    parser.add_argument("--phone")
    parser.add_argument("--password", required=True)
    parser.add_argument("--role", default="porter")
    args = parser.parse_args()

    # Ensure DB tables exist
    print("Initializing DB...")
    await init_db()

    print(f"Creating user {args.email} / {args.phone}...")
    async for session in get_session():
        porter = await auth.create_porter(
            session,
            full_name=args.name,
            password=args.password,
            email=args.email,
            phone=args.phone,
            role=args.role,
        )
        print(
            f"Created/Updated porter id={porter.id} email={porter.email} role={porter.role}"
        )
        break  # Use one session then exit


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
