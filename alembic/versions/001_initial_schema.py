"""Initial schema with foreign keys, relationships, and indexes.

Revision ID: 001
Revises: 
Create Date: 2024-11-14 16:30:00.000000

This migration creates the initial database schema with all tables,
foreign key constraints, and performance indexes.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial schema."""
    # Create profiles table
    op.create_table(
        'profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(100), nullable=True),
        sa.Column('avatar_url', sa.Text(), nullable=True),
        sa.Column('role', sa.String(20), nullable=False, server_default='user'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_profiles_email', 'profiles', ['email'])

    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_project_user_id', 'projects', ['user_id'])

    # Create crawl_jobs table
    op.create_table(
        'crawl_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('keywords', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('max_images', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_images', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('downloaded_images', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('valid_images', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_chunks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('active_chunks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completed_chunks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_chunks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('task_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_crawl_job_status', 'crawl_jobs', ['status'])
    op.create_index('ix_crawl_job_project_status', 'crawl_jobs', ['project_id', 'status'])
    op.create_index('ix_crawl_jobs_project_id', 'crawl_jobs', ['project_id'])

    # Create images table
    op.create_table(
        'images',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('crawl_job_id', sa.Integer(), nullable=False),
        sa.Column('original_url', sa.Text(), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('storage_url', sa.Text(), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('format', sa.String(10), nullable=True),
        sa.ForeignKeyConstraint(['crawl_job_id'], ['crawl_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_image_crawl_job_id', 'images', ['crawl_job_id'])

    # Create activity_logs table
    op.create_table(
        'activity_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.Text(), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', sa.String(50), nullable=True),
        sa.Column('metadata_', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['profiles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_activity_log_user_id', 'activity_logs', ['user_id'])
    op.create_index('ix_activity_log_timestamp', 'activity_logs', ['timestamp'])

    # Create validation_jobs table
    op.create_table(
        'validation_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('crawl_job_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_images', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('validated_images', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('invalid_images', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('validation_rules', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['crawl_job_id'], ['crawl_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_validation_job_status', 'validation_jobs', ['status'])
    op.create_index('ix_validation_job_crawl_job_id', 'validation_jobs', ['crawl_job_id'])

    # Create export_jobs table
    op.create_table(
        'export_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('crawl_job_id', sa.Integer(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('format', sa.String(20), nullable=False, server_default='zip'),
        sa.Column('total_images', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('exported_images', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('download_url', sa.Text(), nullable=True),
        sa.Column('export_options', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['crawl_job_id'], ['crawl_jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_export_job_status', 'export_jobs', ['status'])
    op.create_index('ix_export_job_user_id', 'export_jobs', ['user_id'])
    op.create_index('ix_export_job_crawl_job_id', 'export_jobs', ['crawl_job_id'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('export_jobs')
    op.drop_table('validation_jobs')
    op.drop_table('activity_logs')
    op.drop_table('images')
    op.drop_table('crawl_jobs')
    op.drop_table('projects')
    op.drop_table('profiles')
