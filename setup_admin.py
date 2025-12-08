#!/usr/bin/env python3
"""Setup admin account for manual testing."""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "fastapi-backend"))

async def setup_admin():
    from app.database import engine, init_db
    from app.auth import create_porter
    from app.models import Porter
    from sqlmodel import select
    from sqlmodel.ext.asyncio.session import AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    print("🔄 Initializing database...")
    await init_db()
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        # Check if admin exists
        result = await session.exec(select(Porter).where(Porter.email == "admin@test.local"))
        admin = result.first()
        
        if not admin:
            print("👤 Creating new admin account...")
            admin = await create_porter(
                session,
                full_name="Manual Test Admin",
                email="admin@test.local",
                password="admin123",
                role="admin"
            )
        else:
            print("👤 Admin account exists. Verifying role...")
            if admin.role != "admin":
                print(f"⚠️  Fixing role from {admin.role} to admin...")
                admin.role = "admin"
                session.add(admin)
                await session.commit()
                await session.refresh(admin)
        
        print(f"✅ Admin Ready!")
        print(f"   Email: {admin.email}")
        print(f"   Role: {admin.role}")
        print(f"   ID: {admin.id}")

if __name__ == "__main__":
    asyncio.run(setup_admin())
