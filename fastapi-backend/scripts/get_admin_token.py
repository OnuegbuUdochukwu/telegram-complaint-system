"""Create an admin porter and print a JWT token for tests.

Usage:
    python fastapi-backend/scripts/get_admin_token.py --email admin@example.com --password secret

This script will:
- create an admin porter via the app DB
- call the /auth/login endpoint to receive a JWT and print it
"""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "fastapi-backend"))

import requests
from app.database import engine
from sqlmodel import Session
from app import auth
from app.database import init_db


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    # Ensure DB tables exist
    init_db()

    with Session(engine) as session:
        # Create admin porter directly in DB
        porter = auth.create_porter(
            session,
            full_name="Admin User",
            password=args.password,
            email=args.email,
            role="admin",
        )
        print(f"Created admin porter id={porter.id} email={porter.email}")

    # Use login endpoint to get token
    resp = requests.post(
        "http://127.0.0.1:8001/auth/login",
        data={"username": args.email, "password": args.password},
    )
    resp.raise_for_status()
    token = resp.json().get("access_token")
    print(token)


if __name__ == "__main__":
    main()
