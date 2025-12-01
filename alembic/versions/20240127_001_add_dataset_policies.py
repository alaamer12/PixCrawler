"""add dataset policies

Revision ID: 20240127_001
Revises: 
Create Date: 2024-01-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20240127_001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create archival_policies table
    op.create_table('archival_policies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('days_until_archive', sa.Integer(), nullable=False, comment='Days since creation or last access before archiving'),
        sa.Column('target_tier', sa.String(length=20), nullable=False, comment='Target storage tier: hot, warm, cold'),
        sa.Column('filter_criteria', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment="Criteria to filter datasets (e.g., {'project_id': 1})"),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when record was created'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when record was last updated'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_archival_policies_is_active', 'archival_policies', ['is_active'], unique=False)

    # Create cleanup_policies table
    op.create_table('cleanup_policies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('days_until_cleanup', sa.Integer(), nullable=False, comment='Days since creation/completion before cleanup'),
        sa.Column('cleanup_target', sa.String(length=50), nullable=False, comment='Target: full_dataset, temp_files, failed_jobs'),
        sa.Column('filter_criteria', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Criteria to filter datasets'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when record was created'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when record was last updated'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_cleanup_policies_is_active', 'cleanup_policies', ['is_active'], unique=False)

    # Create policy_execution_logs table
    op.create_table('policy_execution_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('policy_type', sa.String(length=20), nullable=False, comment='archival or cleanup'),
        sa.Column('policy_id', sa.Integer(), nullable=False),
        sa.Column('dataset_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_policy_logs_executed_at', 'policy_execution_logs', ['executed_at'], unique=False)
    op.create_index('ix_policy_logs_type_status', 'policy_execution_logs', ['policy_type', 'status'], unique=False)
    op.create_index(op.f('ix_policy_execution_logs_dataset_id'), 'policy_execution_logs', ['dataset_id'], unique=False)
    op.create_index(op.f('ix_policy_execution_logs_policy_id'), 'policy_execution_logs', ['policy_id'], unique=False)

    # Add columns to datasets table
    op.add_column('datasets', sa.Column('storage_tier', sa.String(length=20), server_default='hot', nullable=False, comment='Storage tier: hot, warm, cold'))
    op.add_column('datasets', sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp when dataset was archived'))
    op.add_column('datasets', sa.Column('last_accessed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp of last access'))
    op.create_index(op.f('ix_datasets_storage_tier'), 'datasets', ['storage_tier'], unique=False)


def downgrade() -> None:
    # Remove columns from datasets table
    op.drop_index(op.f('ix_datasets_storage_tier'), table_name='datasets')
    op.drop_column('datasets', 'last_accessed_at')
    op.drop_column('datasets', 'archived_at')
    op.drop_column('datasets', 'storage_tier')

    # Drop policy_execution_logs table
    op.drop_index(op.f('ix_policy_execution_logs_policy_id'), table_name='policy_execution_logs')
    op.drop_index(op.f('ix_policy_execution_logs_dataset_id'), table_name='policy_execution_logs')
    op.drop_index('ix_policy_logs_type_status', table_name='policy_execution_logs')
    op.drop_index('ix_policy_logs_executed_at', table_name='policy_execution_logs')
    op.drop_table('policy_execution_logs')

    # Drop cleanup_policies table
    op.drop_index('ix_cleanup_policies_is_active', table_name='cleanup_policies')
    op.drop_table('cleanup_policies')

    # Drop archival_policies table
    op.drop_index('ix_archival_policies_is_active', table_name='archival_policies')
    op.drop_table('archival_policies')
