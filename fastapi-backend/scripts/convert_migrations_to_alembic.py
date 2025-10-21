"""Convert repository SQL migrations (migrations/*.sql) into Alembic revisions.

Each SQL file is copied into an Alembic revision that executes the SQL with
op.execute(). This keeps the SQL content unchanged while tracking it via Alembic.

Usage (from repo root):
  python fastapi-backend/scripts/convert_migrations_to_alembic.py
"""
import hashlib
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
MIG_DIR = ROOT / "migrations"
ALEMBIC_VERSIONS = ROOT / "fastapi-backend" / "alembic" / "versions"
ALEMBIC_VERSIONS.mkdir(parents=True, exist_ok=True)

for sql_file in sorted(MIG_DIR.glob("*.sql")):
    content = sql_file.read_text()
    # Create a deterministic revision id from filename+content
    rev_hash = hashlib.sha1((sql_file.name + content).encode()).hexdigest()[:12]
    rev_filename = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{rev_hash}_{sql_file.stem}.py"
    out = ALEMBIC_VERSIONS / rev_filename
    if out.exists():
        print(f"Skipping existing alembic revision for {sql_file.name}")
        continue
    template = f"""
from alembic import op

revision = '{rev_hash}'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute(r'''
{content}
''')

def downgrade():
    # Manual downgrade is required for SQL migrations.
    pass
"""
    out.write_text(template)
    print(f"Created alembic revision: {out}")

print("Done")
