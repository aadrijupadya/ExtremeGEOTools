"""
add soft-delete column on runs

Revision ID: 0002_add_deleted
Revises: 0001_initial
Create Date: 2025-08-18 00:00:01
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_add_deleted'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add the deleted column if it doesn't exist yet
    op.execute("ALTER TABLE runs ADD COLUMN IF NOT EXISTS deleted boolean NOT NULL DEFAULT false;")


def downgrade() -> None:
    op.execute("ALTER TABLE runs DROP COLUMN IF EXISTS deleted;")


