"""Add source column to runs table

Revision ID: 0004
Revises: 0003_add_daily_metrics
Create Date: 2025-08-20 14:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0004'
down_revision = '0003_add_daily_metrics'
branch_labels = None
depends_on = None


def upgrade():
    # Add source column with default value 'manual'
    op.add_column('runs', sa.Column('source', sa.String(), nullable=False, server_default='manual'))


def downgrade():
    # Remove source column
    op.drop_column('runs', 'source')
