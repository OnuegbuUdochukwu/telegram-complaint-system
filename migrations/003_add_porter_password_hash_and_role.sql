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
END$$;
