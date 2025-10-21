from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field

# SQLAlchemy imports for explicit server-side UUID column
from sqlalchemy import Column, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid
from dotenv import dotenv_values

# Detect whether we're using Postgres so we can use a native UUID column.
_env = dotenv_values("../.env")
_DATABASE_URL = _env.get("DATABASE_URL", "") or ""
_USE_PG_UUID = any(x in _DATABASE_URL for x in ("postgres://", "postgresql://", "psycopg2"))


class Hostel(SQLModel, table=True):
    __tablename__ = "hostels"
    id: Optional[str] = Field(default=None, primary_key=True)
    slug: str = Field(sa_column_kwargs={"unique": True})
    display_name: str
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    # (Hostel has no auth fields)


class Porter(SQLModel, table=True):
    __tablename__ = "porters"
    if _USE_PG_UUID:
        id: Optional[str] = Field(default=None, primary_key=True, sa_column=Column(PG_UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()")))
    else:
        id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    full_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    # Password hash stored for authentication. Use a secure hashing algorithm.
    password_hash: Optional[str] = None
    # Role for RBAC: 'porter' or 'admin'. Default to 'porter'.
    role: Optional[str] = Field(default='porter')
    assigned_hostel_id: Optional[str] = Field(default=None, foreign_key="hostels.id")
    active: bool = Field(default=True)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[str] = Field(default=None, primary_key=True)
    telegram_user_id: str = Field(sa_column_kwargs={"unique": True})
    display_name: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


class Complaint(SQLModel, table=True):
    __tablename__ = "complaints"
    # Use a PostgreSQL UUID column with server_default so the DB assigns
    # the value using gen_random_uuid(). The sa_column explicitly marks
    # the Column as the primary key so SQLAlchemy/SQLModel can map it.
    if _USE_PG_UUID:
        id: Optional[str] = Field(
            default=None,
            primary_key=True,
            sa_column=Column(PG_UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()")),
        )
    else:
        # For SQLite/local tests, use a Python-generated UUID string as the primary key.
        id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
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
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


class AssignmentAudit(SQLModel, table=True):
    __tablename__ = "assignment_audits"
    id: Optional[int] = Field(default=None, primary_key=True)
    complaint_id: str = Field(foreign_key="complaints.id")
    assigned_by: str
    assigned_to: str
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
