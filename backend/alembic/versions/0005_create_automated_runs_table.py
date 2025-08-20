"""Create automated_runs table

Revision ID: 0005
Revises: 0004
Create Date: 2025-08-20 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade():
    # Create automated_runs table
    op.create_table('automated_runs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('ts', sa.DateTime(), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('engine', sa.String(), nullable=False),
        sa.Column('model', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('answer_text', sa.Text(), nullable=True),
        sa.Column('entities_normalized', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('links', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('domains', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('extreme_mentioned', sa.Boolean(), nullable=True),
        sa.Column('competitor_mentions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('citation_count', sa.Integer(), nullable=True),
        sa.Column('domain_count', sa.Integer(), nullable=True),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('cost_usd', sa.Float(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('intent_category', sa.String(), nullable=True),
        sa.Column('competitor_set', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('metrics_computed', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better performance
    op.create_index(op.f('ix_automated_runs_ts'), 'automated_runs', ['ts'], unique=False)
    op.create_index(op.f('ix_automated_runs_engine'), 'automated_runs', ['engine'], unique=False)
    op.create_index(op.f('ix_automated_runs_intent_category'), 'automated_runs', ['intent_category'], unique=False)
    op.create_index(op.f('ix_automated_runs_status'), 'automated_runs', ['status'], unique=False)


def downgrade():
    # Drop indexes first
    op.drop_index(op.f('ix_automated_runs_status'), table_name='automated_runs')
    op.drop_index(op.f('ix_automated_runs_intent_category'), table_name='automated_runs')
    op.drop_index(op.f('ix_automated_runs_engine'), table_name='automated_runs')
    op.drop_index(op.f('ix_automated_runs_ts'), table_name='automated_runs')
    
    # Drop table
    op.drop_table('automated_runs')
