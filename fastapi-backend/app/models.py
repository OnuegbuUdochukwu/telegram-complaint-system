from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field

# SQLAlchemy imports for explicit server-side UUID column
from sqlalchemy import Column, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid
from dotenv import dotenv_values
from pathlib import Path
import os

# Detect whether we're using Postgres so we can use a native UUID column.
# Prefer environment variable override (useful for tests/CI), fall back to .env file.
_env_path = Path(__file__).resolve().parents[2] / ".env"
_env = dotenv_values(str(_env_path))
_DATABASE_URL = os.environ.get("DATABASE_URL", "") or _env.get("DATABASE_URL", "") or ""
_USE_PG_UUID = any(x in _DATABASE_URL for x in ("postgres://", "postgresql://", "psycopg2"))


class Hostel(SQLModel, table=True):
    __tablename__ = "hostels"
    if _USE_PG_UUID:
        id: Optional[str] = Field(default=None, primary_key=True, sa_column=Column(PG_UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()")))
    else:
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
    # assigned_hostel_id references hostels.id; ensure column type matches hostels.id
    if _USE_PG_UUID:
        assigned_hostel_id: Optional[str] = Field(default=None, foreign_key="hostels.id", sa_column=Column(PG_UUID(as_uuid=False)))
    else:
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
    # Ensure assigned_porter_id column type matches porters.id when using Postgres UUIDs
    if _USE_PG_UUID:
        assigned_porter_id: Optional[str] = Field(default=None, foreign_key="porters.id", sa_column=Column(PG_UUID(as_uuid=False)))
    else:
        assigned_porter_id: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


class AssignmentAudit(SQLModel, table=True):
    __tablename__ = "assignment_audits"
    id: Optional[int] = Field(default=None, primary_key=True)
    # Use matching column types for FK references. When Postgres with UUIDs is used
    # ensure complaint_id / assigned_by / assigned_to use the native UUID column type
    if _USE_PG_UUID:
        complaint_id: str = Field(foreign_key="complaints.id", sa_column=Column(PG_UUID(as_uuid=False)))
        assigned_by: str = Field(sa_column=Column(PG_UUID(as_uuid=False)))
        assigned_to: str = Field(sa_column=Column(PG_UUID(as_uuid=False)))
    else:
        complaint_id: str = Field(foreign_key="complaints.id")
        assigned_by: str
        assigned_to: str
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))


class Photo(SQLModel, table=True):
    __tablename__ = "photos"
    if _USE_PG_UUID:
        id: Optional[str] = Field(default=None, primary_key=True, sa_column=Column(PG_UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()")))
    else:
        id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    
    if _USE_PG_UUID:
        complaint_id: str = Field(foreign_key="complaints.id", sa_column=Column(PG_UUID(as_uuid=False)))
    else:
        complaint_id: str = Field(foreign_key="complaints.id")
    
    # S3/Storage URL for the original photo
    file_url: str
    
    # S3/Storage URL for the thumbnail (optional)
    thumbnail_url: Optional[str] = None
    
    # File metadata
    file_name: str
    file_size: Optional[int] = None  # Size in bytes
    mime_type: Optional[str] = None  # e.g., "image/jpeg"
    
    # Dimensions (optional, useful for display)
    width: Optional[int] = None
    height: Optional[int] = None
    
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))


class AdminInvitation(SQLModel, table=True):
    """Admin invitation model for secure admin onboarding."""
    __tablename__ = "admin_invitations"
    if _USE_PG_UUID:
        id: Optional[str] = Field(default=None, primary_key=True, sa_column=Column(PG_UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()")))
    else:
        id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    
    email: str = Field(sa_column_kwargs={"unique": True})
    
    # Foreign key to Porter who sent the invitation
    if _USE_PG_UUID:
        invited_by: str = Field(foreign_key="porters.id", sa_column=Column(PG_UUID(as_uuid=False)))
    else:
        invited_by: str = Field(foreign_key="porters.id")
    
    # Secure random token for invitation link
    token: str = Field(sa_column_kwargs={"unique": True})
    
    # Expiration time (default 48 hours)
    expires_at: datetime
    
    used: bool = Field(default=False)
    
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))


class OTPToken(SQLModel, table=True):
    """OTP token model for email verification and password reset."""
    __tablename__ = "otp_tokens"
    if _USE_PG_UUID:
        id: Optional[str] = Field(default=None, primary_key=True, sa_column=Column(PG_UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()")))
    else:
        id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    
    email: str
    
    # Hashed OTP code (like password hashes)
    code_hash: str
    
    # Purpose: 'signup', 'password_reset'
    purpose: str
    
    # Expiration time (default 10 minutes)
    expires_at: datetime
    
    # Rate limiting: track verification attempts
    attempts: int = Field(default=0)
    max_attempts: int = Field(default=3)
    
    used: bool = Field(default=False)
    
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
