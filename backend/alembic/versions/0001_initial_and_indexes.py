"""
initial tables (runs) and indexes + enrichment columns

Revision ID: 0001_initial
Revises: 
Create Date: 2025-08-18 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This migration assumes the 'runs' table already exists (created by app startup in early versions).
    # We add missing enrichment columns and performance indexes. All statements are IF NOT EXISTS to be idempotent.

    # Add enrichment and soft-delete columns
    op.execute("ALTER TABLE runs ADD COLUMN IF NOT EXISTS citations_enriched jsonb NOT NULL DEFAULT '[]'::jsonb;")
    op.execute("ALTER TABLE runs ADD COLUMN IF NOT EXISTS entities_normalized jsonb NOT NULL DEFAULT '[]'::jsonb;")
    op.execute("ALTER TABLE runs ADD COLUMN IF NOT EXISTS deleted boolean NOT NULL DEFAULT false;")

    # Indexes
    op.execute("CREATE INDEX IF NOT EXISTS ix_runs_ts ON runs (ts);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_runs_engine ON runs (engine);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_runs_model ON runs (model);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_runs_query_lower ON runs (lower(query));")


def downgrade() -> None:
    # Best-effort drops; safe in dev. In prod, prefer forward-only migrations.
    op.execute("DROP INDEX IF EXISTS ix_runs_query_lower;")
    op.execute("DROP INDEX IF EXISTS ix_runs_model;")
    op.execute("DROP INDEX IF EXISTS ix_runs_engine;")
    op.execute("DROP INDEX IF EXISTS ix_runs_ts;")
    op.execute("ALTER TABLE runs DROP COLUMN IF EXISTS entities_normalized;")
    op.execute("ALTER TABLE runs DROP COLUMN IF EXISTS citations_enriched;")
    op.execute("ALTER TABLE runs DROP COLUMN IF EXISTS deleted;")


