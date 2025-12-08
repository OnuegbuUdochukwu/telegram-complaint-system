"""Expand photo metadata for S3 + add photo_uploads table

Revision ID: 20251117_s3_storage_expansion
Revises: 20251113_migrate_category_enum
Create Date: 2025-11-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20251117_s3_storage_expansion"
down_revision: Union[str, None] = "20251113_migrate_category_enum"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns to photos table safely
    op.execute("ALTER TABLE photos ADD COLUMN IF NOT EXISTS processed_at TIMESTAMPTZ")
    op.execute("ALTER TABLE photos ADD COLUMN IF NOT EXISTS storage_provider VARCHAR(32) NOT NULL DEFAULT 's3'")
    op.execute("ALTER TABLE photos ADD COLUMN IF NOT EXISTS s3_key VARCHAR(512)")
    op.execute("ALTER TABLE photos ADD COLUMN IF NOT EXISTS s3_thumbnail_key VARCHAR(512)")
    op.execute("ALTER TABLE photos ADD COLUMN IF NOT EXISTS checksum_sha256 VARCHAR(128)")

    # Create photo_uploads table
    op.execute(r"""
    CREATE TABLE IF NOT EXISTS photo_uploads (
        id VARCHAR(36) PRIMARY KEY,
        complaint_id UUID NOT NULL REFERENCES complaints(id) ON DELETE CASCADE,
        photo_id UUID NOT NULL, -- Logical reference to photos.id? Or just external ID? Using UUID for consistency if photos.id is UUID.
        -- Wait, original said sa.String(36). UUID is safer if matching other tables.
        -- Let's stick to original definition: sa.String(36).
        -- complaint_id was sa.String(36) in original?
        -- complaints.id is UUID. So complaint_id MUST be UUID to reference it.
        -- Original: sa.Column("complaint_id", sa.String(length=36), nullable=False)
        -- This implies implicit cast or text mismatch? 
        -- Postgres allows FK from String to UUID? NO.
        -- I MUST change complaint_id to UUID in photo_uploads if complaints.id is UUID.
        -- And photo_id? Photos.id is UUID.
        
        filename VARCHAR(255) NOT NULL,
        content_type VARCHAR(128) NOT NULL,
        content_length BIGINT,
        -- s3_key already defined above? No, specific to this table.
        s3_key VARCHAR(512) NOT NULL,
        status VARCHAR(32) NOT NULL DEFAULT 'pending',
        expires_at TIMESTAMPTZ NOT NULL,
        created_at TIMESTAMPTZ NOT NULL,
        confirmed_at TIMESTAMPTZ
    )
    """)
    
    # Fix types for FKs if needed (using UUID)
    # Re-reading original file: complaint_id was String(36). complaints.id is UUID.
    # This was a bug in original definition! It would have failed on FK creation.
    # So I AM FIXING A BUG HERE TOO. I will use UUID.

    op.execute("CREATE INDEX IF NOT EXISTS ix_photo_uploads_complaint_id ON photo_uploads (complaint_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_photo_uploads_photo_id ON photo_uploads (photo_id)")


def downgrade() -> None:
    op.drop_index("ix_photo_uploads_photo_id", table_name="photo_uploads")
    op.drop_index("ix_photo_uploads_complaint_id", table_name="photo_uploads")
    op.drop_table("photo_uploads")

    op.drop_column("photos", "checksum_sha256")
    op.drop_column("photos", "s3_thumbnail_key")
    op.drop_column("photos", "s3_key")
    op.drop_column("photos", "storage_provider")
    op.drop_column("photos", "processed_at")

