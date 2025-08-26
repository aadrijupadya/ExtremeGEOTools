"""
Add is_branded boolean to runs and automated_runs

Revision ID: 0006_add_is_branded
Revises: 0005
Create Date: 2025-08-25 00:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0006_add_is_branded'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add column to runs (nullable with default false for backfill safety)
    op.add_column('runs', sa.Column('is_branded', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    # Drop server_default after population to keep clean model default
    op.alter_column('runs', 'is_branded', server_default=None)

    # Add column to automated_runs
    op.add_column('automated_runs', sa.Column('is_branded', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.alter_column('automated_runs', 'is_branded', server_default=None)


def downgrade() -> None:
    op.drop_column('automated_runs', 'is_branded')
    op.drop_column('runs', 'is_branded')


