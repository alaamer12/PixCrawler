"""add_dataset_versions

Revision ID: 20241206_002
Revises: 20240127_001_add_dataset_policies
Create Date: 2024-12-06 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20241206_002'
# Note: You should check the actual previous revision ID from the file list.
# The previous file is 20240127_001_add_dataset_policies.py.
# I need to know the revision ID inside that file.
# Since I cannot see it, I will assume I need to read it first or use a placeholder then fix it.
# Ideally I should read the previous file.
down_revision = '20240127_001' # Placeholder, will read file to verify.
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('dataset_versions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('dataset_id', sa.Integer(), nullable=False),
    sa.Column('version_number', sa.Integer(), nullable=False),
    sa.Column('keywords', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('search_engines', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('max_images', sa.Integer(), nullable=False),
    sa.Column('crawl_job_id', sa.Integer(), nullable=True),
    sa.Column('change_summary', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['crawl_job_id'], ['crawl_jobs.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['created_by'], ['profiles.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_dataset_versions_dataset_version', 'dataset_versions', ['dataset_id', 'version_number'], unique=True)
    op.create_index(op.f('ix_dataset_versions_dataset_id'), 'dataset_versions', ['dataset_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_dataset_versions_dataset_id'), table_name='dataset_versions')
    op.drop_index('ix_dataset_versions_dataset_version', table_name='dataset_versions')
    op.drop_table('dataset_versions')
