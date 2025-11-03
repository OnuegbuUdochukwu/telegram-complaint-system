BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 1baee5921a2a

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
      ADD CONSTRAINT chk_room_number_format CHECK (room_number ~ '^[A-H][0-9]{3}$');
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_complaints_telegram_user_id ON complaints (telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints (status);
CREATE INDEX IF NOT EXISTS idx_complaints_created_at ON complaints (created_at);

-- Optional: Comments for clarity
COMMENT ON TABLE complaints IS 'Primary table for student maintenance complaints';
COMMENT ON COLUMN complaints.photo_urls IS 'Array of photo URLs (optional)';;

INSERT INTO alembic_version (version_num) VALUES ('1baee5921a2a') RETURNING alembic_version.version_num;

-- Running upgrade 1baee5921a2a -> 34c06045bbb9

-- Migration: Create supporting tables for Phase 2
-- Creates hostels, porters, and users tables used by the complaints system

-- hostels: small lookup table for hostel metadata
CREATE TABLE IF NOT EXISTS hostels (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug TEXT NOT NULL UNIQUE,
  display_name VARCHAR(100) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ
);

-- porters: staff who handle complaints (basic fields for assignment later)
CREATE TABLE IF NOT EXISTS porters (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  full_name VARCHAR(150) NOT NULL,
  phone VARCHAR(32),
  email VARCHAR(255),
  assigned_hostel_id UUID REFERENCES hostels(id) ON DELETE SET NULL,
  active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ
);

-- users: mapping from Telegram user id to internal user record
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  telegram_user_id VARCHAR(32) NOT NULL UNIQUE,
  display_name VARCHAR(150),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ
);

-- Indexes to support common lookups
CREATE INDEX IF NOT EXISTS idx_hostels_slug ON hostels (slug);
CREATE INDEX IF NOT EXISTS idx_porters_assigned_hostel ON porters (assigned_hostel_id);
CREATE INDEX IF NOT EXISTS idx_users_telegram_user_id ON users (telegram_user_id);

-- Comments
COMMENT ON TABLE hostels IS 'Lookup table for hostel canonical names and slugs';
COMMENT ON TABLE porters IS 'Represent porters/maintenance staff for assignment and contact';
COMMENT ON TABLE users IS 'Mapping from Telegram user ID to an internal user record';;

UPDATE alembic_version SET version_num='34c06045bbb9' WHERE alembic_version.version_num = '1baee5921a2a';

-- Running upgrade 34c06045bbb9 -> 4dbeedc537a0

-- Migration: Add password_hash and role to porters table
-- Idempotent: only adds columns if they don't already exist

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='porters' AND column_name='password_hash'
    ) THEN
        ALTER TABLE porters ADD COLUMN password_hash TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='porters' AND column_name='role'
    ) THEN
        ALTER TABLE porters ADD COLUMN role TEXT DEFAULT 'porter' NOT NULL;
    END IF;
END$$;;

UPDATE alembic_version SET version_num='4dbeedc537a0' WHERE alembic_version.version_num = '34c06045bbb9';

-- Running upgrade 4dbeedc537a0 -> 20251021_fix_assigned_porter_uuid

DO $$
    BEGIN
        -- Only alter if column exists and is not already uuid
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='complaints' AND column_name='assigned_porter_id') THEN
            BEGIN
                ALTER TABLE complaints ALTER COLUMN assigned_porter_id TYPE UUID USING assigned_porter_id::uuid;
            EXCEPTION WHEN others THEN
                RAISE NOTICE 'skipping alter complaints.assigned_porter_id: %%', SQLERRM;
            END;
        END IF;

        -- Convert assignment_audits columns to UUID
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='assignment_audits' AND column_name='complaint_id') THEN
            BEGIN
                ALTER TABLE assignment_audits ALTER COLUMN complaint_id TYPE UUID USING complaint_id::uuid;
            EXCEPTION WHEN others THEN
                RAISE NOTICE 'skipping alter assignment_audits.complaint_id: %%', SQLERRM;
            END;
        END IF;

        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='assignment_audits' AND column_name='assigned_by') THEN
            BEGIN
                ALTER TABLE assignment_audits ALTER COLUMN assigned_by TYPE UUID USING assigned_by::uuid;
            EXCEPTION WHEN others THEN
                RAISE NOTICE 'skipping alter assignment_audits.assigned_by: %%', SQLERRM;
            END;
        END IF;

        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='assignment_audits' AND column_name='assigned_to') THEN
            BEGIN
                ALTER TABLE assignment_audits ALTER COLUMN assigned_to TYPE UUID USING assigned_to::uuid;
            EXCEPTION WHEN others THEN
                RAISE NOTICE 'skipping alter assignment_audits.assigned_to: %%', SQLERRM;
            END;
        END IF;
    END$$;;

UPDATE alembic_version SET version_num='20251021_fix_assigned_porter_uuid' WHERE alembic_version.version_num = '4dbeedc537a0';

-- Running upgrade 20251021_fix_assigned_porter_uuid -> 20251021_create_photos_table

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
COMMENT ON TABLE photos IS 'Stores metadata for photos attached to complaints. References S3 or other storage URLs.';;

UPDATE alembic_version SET version_num='20251021_create_photos_table' WHERE alembic_version.version_num = '20251021_fix_assigned_porter_uuid';

-- Running upgrade 20251021_fix_assigned_porter_uuid -> 20250122_create_admin_invitation_and_otp_tables

CREATE TABLE IF NOT EXISTS admin_invitations (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email VARCHAR(255) NOT NULL UNIQUE,
        invited_by UUID NOT NULL REFERENCES porters(id) ON DELETE CASCADE,
        token VARCHAR(255) NOT NULL UNIQUE,
        expires_at TIMESTAMPTZ NOT NULL,
        used BOOLEAN NOT NULL DEFAULT false,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_admin_invitations_token ON admin_invitations (token);
    CREATE INDEX IF NOT EXISTS idx_admin_invitations_email ON admin_invitations (email);
    CREATE INDEX IF NOT EXISTS idx_admin_invitations_invited_by ON admin_invitations (invited_by);
    CREATE INDEX IF NOT EXISTS idx_admin_invitations_expires_at ON admin_invitations (expires_at);

    COMMENT ON TABLE admin_invitations IS 'Admin invitation records for secure admin onboarding';;

CREATE TABLE IF NOT EXISTS otp_tokens (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email VARCHAR(255) NOT NULL,
        code_hash VARCHAR(255) NOT NULL,
        purpose VARCHAR(50) NOT NULL,
        expires_at TIMESTAMPTZ NOT NULL,
        attempts INTEGER NOT NULL DEFAULT 0,
        max_attempts INTEGER NOT NULL DEFAULT 3,
        used BOOLEAN NOT NULL DEFAULT false,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_otp_tokens_email ON otp_tokens (email);
    CREATE INDEX IF NOT EXISTS idx_otp_tokens_purpose ON otp_tokens (purpose);
    CREATE INDEX IF NOT EXISTS idx_otp_tokens_expires_at ON otp_tokens (expires_at);
    CREATE INDEX IF NOT EXISTS idx_otp_tokens_email_purpose ON otp_tokens (email, purpose);

    COMMENT ON TABLE otp_tokens IS 'OTP verification tokens for email verification and password reset';;

INSERT INTO alembic_version (version_num) VALUES ('20250122_create_admin_invitation_and_otp_tables') RETURNING alembic_version.version_num;

COMMIT;

