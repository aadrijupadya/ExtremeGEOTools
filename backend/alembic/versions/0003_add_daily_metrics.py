"""
add daily_metrics table for aggregated metrics

Revision ID: 0003_add_daily_metrics
Revises: 0002_add_deleted_column
Create Date: 2025-01-27 00:00:00

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0003_add_daily_metrics'
down_revision = '0002_add_deleted'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create daily_metrics table
    op.create_table(
        'daily_metrics',
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('engine', sa.String(), nullable=False),
        sa.Column('brand_context', sa.String(), nullable=False),
        sa.Column('total_runs', sa.Integer(), nullable=False, default=0),
        sa.Column('total_cost_usd', sa.Numeric(18, 6), nullable=False, default=0),
        sa.Column('total_citations', sa.Integer(), nullable=False, default=0),
        sa.Column('unique_domains', sa.Integer(), nullable=False, default=0),
        sa.Column('top_domains', postgresql.JSONB(), nullable=False, default=list),
        sa.Column('brand_mentions', sa.Integer(), nullable=False, default=0),
        sa.Column('competitor_mentions', sa.Integer(), nullable=False, default=0),
        sa.Column('share_of_voice_pct', sa.Numeric(5, 2), nullable=False, default=0),
        sa.Column('avg_visibility_score', sa.Numeric(5, 2), nullable=False, default=0),
        sa.Column('high_quality_citations', sa.Integer(), nullable=False, default=0),
        sa.Column('last_updated', sa.String(), nullable=False),
        sa.Column('data_version', sa.String(), nullable=False, default='1.0'),
        sa.PrimaryKeyConstraint('date', 'engine', 'brand_context')
    )
    
    # Add indexes for performance
    op.create_index('ix_daily_metrics_date', 'daily_metrics', ['date'])
    op.create_index('ix_daily_metrics_engine', 'daily_metrics', ['engine'])
    op.create_index('ix_daily_metrics_brand_context', 'daily_metrics', ['brand_context'])
    op.create_index('ix_daily_metrics_date_engine', 'daily_metrics', ['date', 'engine'])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('ix_daily_metrics_date_engine')
    op.drop_index('ix_daily_metrics_brand_context')
    op.drop_index('ix_daily_metrics_engine')
    op.drop_index('ix_daily_metrics_date')
    
    # Drop table
    op.drop_table('daily_metrics')
