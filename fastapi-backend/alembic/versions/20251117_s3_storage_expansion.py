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
    op.add_column("photos", sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("photos", sa.Column("storage_provider", sa.String(length=32), nullable=False, server_default="s3"))
    op.add_column("photos", sa.Column("s3_key", sa.String(length=512), nullable=True))
    op.add_column("photos", sa.Column("s3_thumbnail_key", sa.String(length=512), nullable=True))
    op.add_column("photos", sa.Column("checksum_sha256", sa.String(length=128), nullable=True))

    op.create_table(
        "photo_uploads",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("complaint_id", sa.String(length=36), nullable=False),
        sa.Column("photo_id", sa.String(length=36), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("content_length", sa.BigInteger(), nullable=True),
        sa.Column("s3_key", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_photo_uploads_complaint_id", "photo_uploads", ["complaint_id"])
    op.create_index("ix_photo_uploads_photo_id", "photo_uploads", ["photo_id"])


def downgrade() -> None:
    op.drop_index("ix_photo_uploads_photo_id", table_name="photo_uploads")
    op.drop_index("ix_photo_uploads_complaint_id", table_name="photo_uploads")
    op.drop_table("photo_uploads")

    op.drop_column("photos", "checksum_sha256")
    op.drop_column("photos", "s3_thumbnail_key")
    op.drop_column("photos", "s3_key")
    op.drop_column("photos", "storage_provider")
    op.drop_column("photos", "processed_at")

