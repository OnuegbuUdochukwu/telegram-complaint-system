import sys
import os
from pathlib import Path
from sqlmodel import Session, select

# Setup path to import app modules
backend_path = Path("fastapi-backend").resolve()
sys.path.append(str(backend_path))

# Load env vars BEFORE importing app modules
from dotenv import load_dotenv
env_path = backend_path / ".env"
print(f"Loading .env from {env_path}")
load_dotenv(env_path)

# Verify JWT_SECRET is set
if not os.environ.get("JWT_SECRET"):
    print("WARNING: JWT_SECRET not found in env. Setting default for seeding.")
    os.environ["JWT_SECRET"] = "temp-secret-for-seeding-123"

from app.database import engine, init_db
from app.models import Porter
from app.auth import get_password_hash

def seed_admin():
    print("Initializing database...")
    init_db()
    
    with Session(engine) as session:
        admin_email = "admin@example.com"
        existing = session.exec(select(Porter).where(Porter.email == admin_email)).first()
        
        if existing:
            print(f"Admin user {admin_email} already exists.")
            # Reset password to ensure known state
            existing.password_hash = get_password_hash("admin123")
            session.add(existing)
            session.commit()
            print("Password reset to 'admin123'.")
        else:
            print(f"Creating admin user {admin_email}...")
            admin = Porter(
                full_name="System Admin",
                email=admin_email,
                phone="+1234567890",
                password_hash=get_password_hash("admin123"),
                role="admin",
                is_active=True
            )
            session.add(admin)
            session.commit()
            print("Admin created successfully.")

if __name__ == "__main__":
    seed_admin()
