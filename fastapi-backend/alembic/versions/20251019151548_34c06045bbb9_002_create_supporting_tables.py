from alembic import op

revision = "34c06045bbb9"
down_revision = "1baee5921a2a"
branch_labels = None
depends_on = None


def upgrade():
    # hostels
    op.execute(
        r"""
    CREATE TABLE IF NOT EXISTS hostels (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      slug TEXT NOT NULL UNIQUE,
      display_name VARCHAR(100) NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at TIMESTAMPTZ
    )
    """
    )

    # porters
    op.execute(
        r"""
    CREATE TABLE IF NOT EXISTS porters (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      full_name VARCHAR(150) NOT NULL,
      phone VARCHAR(32),
      email VARCHAR(255),
      assigned_hostel_id UUID REFERENCES hostels(id) ON DELETE SET NULL,
      active BOOLEAN NOT NULL DEFAULT true,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at TIMESTAMPTZ
    )
    """
    )

    # users
    op.execute(
        r"""
    CREATE TABLE IF NOT EXISTS users (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      telegram_user_id VARCHAR(32) NOT NULL UNIQUE,
      display_name VARCHAR(150),
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at TIMESTAMPTZ
    )
    """
    )

    # Indexes
    op.execute("CREATE INDEX IF NOT EXISTS idx_hostels_slug ON hostels (slug)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_porters_assigned_hostel ON porters (assigned_hostel_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_users_telegram_user_id ON users (telegram_user_id)"
    )

    # Comments
    op.execute(
        "COMMENT ON TABLE hostels IS 'Lookup table for hostel canonical names and slugs'"
    )
    op.execute(
        "COMMENT ON TABLE porters IS 'Represent porters/maintenance staff for assignment and contact'"
    )
    op.execute(
        "COMMENT ON TABLE users IS 'Mapping from Telegram user ID to an internal user record'"
    )


def downgrade():
    # Manual downgrade is required for SQL migrations.
    pass
