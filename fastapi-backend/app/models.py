from typing import Optional, List
from datetime import datetime
import uuid
from sqlmodel import SQLModel, Field


class Hostel(SQLModel, table=True):
    __tablename__ = "hostels"
    id: Optional[str] = Field(default=None, primary_key=True)
    slug: str = Field(sa_column_kwargs={"unique": True})
    display_name: str
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class Porter(SQLModel, table=True):
    __tablename__ = "porters"
    id: Optional[str] = Field(default=None, primary_key=True)
    full_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    assigned_hostel_id: Optional[str] = Field(default=None, foreign_key="hostels.id")
    active: bool = Field(default=True)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[str] = Field(default=None, primary_key=True)
    telegram_user_id: str = Field(sa_column_kwargs={"unique": True})
    display_name: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class Complaint(SQLModel, table=True):
    __tablename__ = "complaints"
    # Use a Python-generated UUID string by default to avoid requiring
    # the database-side `gen_random_uuid()` extension during local dev.
    # For production, prefer DB-generated UUIDs and ensure `pgcrypto` is
    # installed or migrate to `uuid-ossp` as appropriate.
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    telegram_user_id: str
    hostel: str
    # Wing is optional for backwards compatibility with bot payloads that
    # don't yet collect this value. Use an empty string as default so DB's
    # NOT NULL constraint (migration) is satisfied when inserting.
    wing: str = Field(default="")
    room_number: str
    category: str
    description: str
    photo_urls: Optional[List[str]] = None
    severity: str
    status: str = Field(default="reported")
    assigned_porter_id: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
