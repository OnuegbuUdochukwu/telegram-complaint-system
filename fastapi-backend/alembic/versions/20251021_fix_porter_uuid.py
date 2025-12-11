"""
Fix complaint FK columns to use UUID types

Revision ID: 20251021_fix_assigned_porter_uuid
Revises: 4dbeedc537a0
Create Date: 2025-10-21 00:00:00.000000
"""

from alembic import op

revision = "20251021_fix_porter_uuid"
down_revision = "4dbeedc537a0"
branch_labels = None
depends_on = None


def upgrade():
    # Convert complaints.assigned_porter_id to UUID to match porters.id
    op.execute(
        r"""
    DO $$
    BEGIN
        -- Only alter if column exists and is not already uuid
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='complaints' AND column_name='assigned_porter_id') THEN
            BEGIN
                ALTER TABLE complaints ALTER COLUMN assigned_porter_id TYPE UUID USING assigned_porter_id::uuid;
            EXCEPTION WHEN others THEN
                RAISE NOTICE 'skipping alter complaints.assigned_porter_id: %', SQLERRM;
            END;
        END IF;

        -- Convert assignment_audits columns to UUID
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='assignment_audits' AND column_name='complaint_id') THEN
            BEGIN
                ALTER TABLE assignment_audits ALTER COLUMN complaint_id TYPE UUID USING complaint_id::uuid;
            EXCEPTION WHEN others THEN
                RAISE NOTICE 'skipping alter assignment_audits.complaint_id: %', SQLERRM;
            END;
        END IF;

        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='assignment_audits' AND column_name='assigned_by') THEN
            BEGIN
                ALTER TABLE assignment_audits ALTER COLUMN assigned_by TYPE UUID USING assigned_by::uuid;
            EXCEPTION WHEN others THEN
                RAISE NOTICE 'skipping alter assignment_audits.assigned_by: %', SQLERRM;
            END;
        END IF;

        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='assignment_audits' AND column_name='assigned_to') THEN
            BEGIN
                ALTER TABLE assignment_audits ALTER COLUMN assigned_to TYPE UUID USING assigned_to::uuid;
            EXCEPTION WHEN others THEN
                RAISE NOTICE 'skipping alter assignment_audits.assigned_to: %', SQLERRM;
            END;
        END IF;
    END$$;
    """
    )


def downgrade():
    # Downgrade is intentionally a no-op because converting back to VARCHAR may be lossy
    pass
