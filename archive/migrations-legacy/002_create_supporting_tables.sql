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
COMMENT ON TABLE users IS 'Mapping from Telegram user ID to an internal user record';
