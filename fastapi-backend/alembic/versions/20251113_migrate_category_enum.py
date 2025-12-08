"""
Revision to migrate complaint_category enum values:
- 'structural' -> 'carpentry'
- 'common_area' -> 'metalworks'

This revision attempts to be idempotent and safe for Postgres. It creates a new enum
value type, migrates data via an ALTER TABLE ... USING CASE expression, drops the old
enum type, and renames the new type to the original name.

Downgrade reverses the mapping.
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '20251113_migrate_category_enum'
down_revision = '20251021_create_photos_table'
branch_labels = None
depends_on = None


def upgrade():
    # Perform a safe enum migration for Postgres
    # 1. Create new enum type
    op.execute(r"""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'complaint_category_new') THEN
            CREATE TYPE complaint_category_new AS ENUM ('plumbing','electrical','carpentry','pest','metalworks','other');
        END IF;
    END$$;
    """)

    # 2. Alter column
    op.execute(r"""
    ALTER TABLE complaints ALTER COLUMN category TYPE complaint_category_new USING (
      CASE
        WHEN category::text = 'common_area' THEN 'metalworks'
        WHEN category::text = 'structural' THEN 'carpentry'
        ELSE category::text
      END
    )::complaint_category_new
    """)

    # 3. Drop old enum type
    op.execute(r"""
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'complaint_category') THEN
            DROP TYPE complaint_category;
        END IF;
    END$$;
    """)

    # 4. Rename new type
    op.execute("ALTER TYPE complaint_category_new RENAME TO complaint_category")


def downgrade():
    # Reverse mapping: map carpentry->structural, metalworks->common_area
    op.execute(r"""
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'complaint_category_old') THEN
        CREATE TYPE complaint_category_old AS ENUM ('plumbing','electrical','structural','pest','common_area','other');
    END IF;
END$$;

ALTER TABLE complaints ALTER COLUMN category TYPE complaint_category_old USING (
  CASE
    WHEN category = 'metalworks' THEN 'common_area'
    WHEN category = 'carpentry' THEN 'structural'
    ELSE category
  END
)::complaint_category_old;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'complaint_category') THEN
        DROP TYPE complaint_category;
    END IF;
END$$;

ALTER TYPE complaint_category_old RENAME TO complaint_category;
""")
