
from alembic import op

revision = '1baee5921a2a'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute(r'''
-- Migration: Create complaints table (UUID primary key variant)
-- Adds ENUM types for category, severity, and status and the complaints table

-- Note: the `pgcrypto` extension provides gen_random_uuid().
-- Creating extensions requires database-level CREATE privileges (superuser).
-- If pgcrypto is not installed in your Postgres cluster, ask the DB admin to run:
--   CREATE EXTENSION IF NOT EXISTS pgcrypto;
-- The migration will continue without attempting to create the extension here to avoid permission errors.

-- Attempt to create pgcrypto if the current role has the required privileges.
-- This will succeed silently for superusers and will do nothing for users
-- without permissions (safe to run in mixed environments).
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pgcrypto') THEN
    BEGIN
      PERFORM pg_catalog.set_config('search_path', '', false);
      EXECUTE 'CREATE EXTENSION IF NOT EXISTS pgcrypto';
    EXCEPTION WHEN insufficient_privilege THEN
      -- no-op: extension creation skipped due to lack of privileges
      RAISE NOTICE 'pgcrypto not created: insufficient privileges';
    END;
  END IF;
END$$;

-- ENUM types (compact storage keys)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'complaint_category') THEN
        CREATE TYPE complaint_category AS ENUM ('plumbing','electrical','structural','pest','common_area','other');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'complaint_severity') THEN
        CREATE TYPE complaint_severity AS ENUM ('low','medium','high');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'complaint_status') THEN
        CREATE TYPE complaint_status AS ENUM ('reported','in_progress','on_hold','resolved','rejected');
    END IF;
END$$;

-- Create table
CREATE TABLE IF NOT EXISTS complaints (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  telegram_user_id VARCHAR(32) NOT NULL,
  hostel VARCHAR(50) NOT NULL,
  wing VARCHAR(20), -- nullable to support older clients that don't provide wing
  room_number VARCHAR(10) NOT NULL,
  category complaint_category NOT NULL,
  description TEXT NOT NULL,
  photo_urls TEXT[],
  severity complaint_severity NOT NULL,
  status complaint_status NOT NULL DEFAULT 'reported',
  assigned_porter_id VARCHAR(32),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ
);

-- Constraints / Indexes
-- Add a room number format check constraint if it does not already exist
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'chk_room_number_format'
  ) THEN
    ALTER TABLE complaints
      ADD CONSTRAINT chk_room_number_format CHECK (room_number ~ '^[A-Za-z0-9\\-\\s]{1,10}$');
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_complaints_telegram_user_id ON complaints (telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints (status);
CREATE INDEX IF NOT EXISTS idx_complaints_created_at ON complaints (created_at);

-- Optional: Comments for clarity
COMMENT ON TABLE complaints IS 'Primary table for student maintenance complaints';
COMMENT ON COLUMN complaints.photo_urls IS 'Array of photo URLs (optional)';

''')

def downgrade():
    # Manual downgrade is required for SQL migrations.
    pass
