
from alembic import op

revision = '4dbeedc537a0'
down_revision = '34c06045bbb9'
branch_labels = None
depends_on = None

def upgrade():
    op.execute(r'''
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

''')

def downgrade():
    # Manual downgrade is required for SQL migrations.
    pass
