from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field

# SQLAlchemy imports for explicit server-side UUID column
from sqlalchemy import Column, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


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
    # password_hash stores the bcrypt-hashed password for porter/admin login
    password_hash: Optional[str] = None
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
    # Use a PostgreSQL UUID column with server_default so the DB assigns
    # the value using gen_random_uuid(). The sa_column explicitly marks
    # the Column as the primary key so SQLAlchemy/SQLModel can map it.
    id: Optional[str] = Field(
        default=None,
        primary_key=True,
        sa_column=Column(PG_UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()")),
    )
    telegram_user_id: str
    hostel: str
    # Wing is optional for backwards compatibility with older bot payloads.
    # Make it nullable so clients that don't include it can still create
    # complaints without providing an empty-string placeholder.
    wing: Optional[str] = None
    room_number: str
    category: str
    description: str
    photo_urls: Optional[List[str]] = None
    severity: str
    status: str = Field(default="reported")
    assigned_porter_id: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
