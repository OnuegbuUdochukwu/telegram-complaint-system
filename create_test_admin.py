#!/usr/bin/env python3
"""Create admin account for manual testing."""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "fastapi-backend"))

async def create_admin():
    from app.database import engine, init_db
    from app.auth import create_porter
    from sqlmodel import SQLModel
    from sqlmodel.ext.asyncio.session import AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    # Initialize database
    await init_db()
    
    # Create admin user
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        admin = await create_porter(
            session,
            full_name="Manual Test Admin",
            email="admin@test.local",
            password="admin123",
            role="admin"
        )
        print(f"✅ Admin account created!")
        print(f"   Email: admin@test.local")
        print(f"   Password: admin123")
        print(f"   ID: {admin.id}")
        return admin

if __name__ == "__main__":
    asyncio.run(create_admin())
