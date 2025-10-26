"""
Add photos table for complaint attachments

Revision ID: 20251021_create_photos_table
Revises: 20251021_fix_assigned_porter_uuid
Create Date: 2025-10-21 12:00:00.000000
"""

from alembic import op

revision = '20251021_create_photos_table'
down_revision = '20251021_fix_assigned_porter_uuid'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(r'''
-- Migration: Create photos table for Phase 3 photo uploads and storage
-- Stores metadata for photos attached to complaints

CREATE TABLE IF NOT EXISTS photos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  complaint_id UUID NOT NULL REFERENCES complaints(id) ON DELETE CASCADE,
  file_url TEXT NOT NULL,
  thumbnail_url TEXT,
  file_name VARCHAR(255) NOT NULL,
  file_size INTEGER,
  mime_type VARCHAR(100),
  width INTEGER,
  height INTEGER,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index to support querying photos by complaint
CREATE INDEX IF NOT EXISTS idx_photos_complaint_id ON photos (complaint_id);

-- Comment
COMMENT ON TABLE photos IS 'Stores metadata for photos attached to complaints. References S3 or other storage URLs.';

''')

def downgrade():
    op.execute('DROP TABLE IF EXISTS photos CASCADE;')

