#!/usr/bin/env python3
"""
Create an admin porter in the configured DATABASE_URL and print credentials + JWT.

Optional environment variables:
- ADMIN_FULL_NAME
- ADMIN_EMAIL
- ADMIN_PASSWORD

This script uses the same app code (importing app.auth) so passwords and tokens are created
consistently with the running backend.
"""
import os
import secrets
import sys
from sqlmodel import Session

try:
    from app.database import engine
    from app.auth import create_porter, create_access_token
except Exception as e:
    print("Failed to import application modules:", e, file=sys.stderr)
    sys.exit(2)


def main():
    full_name = os.environ.get("ADMIN_FULL_NAME", "Auto Admin")
    email = os.environ.get("ADMIN_EMAIL", f"admin-{secrets.token_hex(4)}@example.test")
    password = os.environ.get("ADMIN_PASSWORD") or secrets.token_urlsafe(12)

    with Session(engine) as session:
        porter = create_porter(
            session, full_name=full_name, password=password, email=email, role="admin"
        )
        token = create_access_token(subject=porter.id, role="admin")

        print("ADMIN_CREATED")
        print(f"id: {porter.id}")
        print(f"full_name: {porter.full_name}")
        print(f"email: {porter.email}")
        print(f"password: {password}")
        print(f"access_token: {token}")


if __name__ == "__main__":
    main()
