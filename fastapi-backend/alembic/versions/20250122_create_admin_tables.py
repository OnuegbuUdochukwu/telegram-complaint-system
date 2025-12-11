"""
Create admin_invitations and otp_tokens tables

Revision ID: 20250122_create_admin_invitation_and_otp_tables
Revises: 20251021_fix_assigned_porter_uuid
Create Date: 2025-01-22 00:00:00.000000
"""

from alembic import op

revision = "20250122_create_admin_tables"
down_revision = "20251117_s3_storage_expansion"
branch_labels = None
depends_on = None


def upgrade():
    # Create admin_invitations table
    # Create admin_invitations table
    op.execute(
        r"""
    CREATE TABLE IF NOT EXISTS admin_invitations (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email VARCHAR(255) NOT NULL UNIQUE,
        invited_by UUID NOT NULL REFERENCES porters(id) ON DELETE CASCADE,
        token VARCHAR(255) NOT NULL UNIQUE,
        expires_at TIMESTAMPTZ NOT NULL,
        used BOOLEAN NOT NULL DEFAULT false,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_admin_invitations_token ON admin_invitations (token)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_admin_invitations_email ON admin_invitations (email)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_admin_invitations_invited_by ON admin_invitations (invited_by)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_admin_invitations_expires_at ON admin_invitations (expires_at)"
    )
    op.execute(
        "COMMENT ON TABLE admin_invitations IS 'Admin invitation records for secure admin onboarding'"
    )

    # Create otp_tokens table
    op.execute(
        r"""
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
    )
    """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_otp_tokens_email ON otp_tokens (email)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_otp_tokens_purpose ON otp_tokens (purpose)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_otp_tokens_expires_at ON otp_tokens (expires_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_otp_tokens_email_purpose ON otp_tokens (email, purpose)"
    )
    op.execute(
        "COMMENT ON TABLE otp_tokens IS 'OTP verification tokens for email verification and password reset'"
    )


def downgrade():
    op.execute(
        r"""
    DROP TABLE IF EXISTS otp_tokens;
    DROP TABLE IF EXISTS admin_invitations;
    """
    )
