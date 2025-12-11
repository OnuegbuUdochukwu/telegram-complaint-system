"""Small script to seed a porter or admin for local testing.

Usage:
    python fastapi-backend/scripts/seed_porter.py --name "Admin" --email admin@example.com --password secret --role admin

This script uses the backend app's SQLModel session to insert a porter with a hashed password.
"""
import argparse
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.append(str(ROOT / "fastapi-backend"))

from app.database import get_session
from app import auth
from app.database import init_db


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--email")
    parser.add_argument("--phone")
    parser.add_argument("--password", required=True)
    parser.add_argument("--role", default="porter")
    args = parser.parse_args()

    # Use a session to create the porter
    # Ensure DB tables exist
    init_db()
    with get_session() as session:
        porter = auth.create_porter(session, full_name=args.name, password=args.password, email=args.email, phone=args.phone, role=args.role)
        print(f"Created porter id={porter.id} email={porter.email} role={porter.role}")


if __name__ == "__main__":
    main()
