#!/usr/bin/env python3
"""Fix admin account role."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "fastapi-backend"))

async def fix_admin():
    from app.database import engine
    from app.models import Porter
    from sqlmodel import select
    from sqlmodel.ext.asyncio.session import AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        # Find the admin user
        result = await session.exec(select(Porter).where(Porter.email == "admin@test.local"))
        admin = result.first()
        
        if admin:
            admin.role = "admin"
            session.add(admin)
            await session.commit()
            await session.refresh(admin)
            print(f"✅ Fixed admin account!")
            print(f"   Email: {admin.email}")
            print(f"   Role: {admin.role}")
            print(f"   ID: {admin.id}")
        else:
            print("❌ Admin user not found")

if __name__ == "__main__":
    asyncio.run(fix_admin())
