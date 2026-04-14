#!/usr/bin/env python3
"""Setup an admin account for manual/local testing."""
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "fastapi-backend"))


async def setup_admin():
    from app.database import engine, init_db
    from app.auth import create_porter
    from app.models import Porter
    from sqlmodel import select
    from sqlmodel.ext.asyncio.session import AsyncSession
    from sqlalchemy.orm import sessionmaker

    await init_db()
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.exec(select(Porter).where(Porter.email == "admin@test.local"))
        admin = result.first()

        if not admin:
            admin = await create_porter(
                session,
                full_name="Manual Test Admin",
                email="admin@test.local",
                password="admin123",
                role="admin",
            )
        elif admin.role != "admin":
            admin.role = "admin"
            session.add(admin)
            await session.commit()
            await session.refresh(admin)

        print("Admin ready")
        print(f"email={admin.email}")
        print(f"role={admin.role}")
        print(f"id={admin.id}")


if __name__ == "__main__":
    asyncio.run(setup_admin())
