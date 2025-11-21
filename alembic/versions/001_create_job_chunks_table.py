"""Create job_chunks table

Revision ID: 001
Revises: None
Create Date: 2025-01-16 12:00:00.000000

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
    # Create job_chunks table
    op.create_table(
        "job_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("image_range", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("task_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["job_id"], ["crawl_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("ix_job_chunks_job_id", "job_chunks", ["job_id"])
    op.create_index("ix_job_chunks_status", "job_chunks", ["status"])
    op.create_index("ix_job_chunks_job_status", "job_chunks", ["job_id", "status"])
    op.create_index("ix_job_chunks_priority_created", "job_chunks", ["priority", "created_at"])
    op.create_index("ix_job_chunks_task_id", "job_chunks", ["task_id"])

    # Create check constraints
    op.create_check_constraint(
        "ck_job_chunks_status_valid",
        "job_chunks",
        "status IN ('pending', 'processing', 'completed', 'failed')",
    )
    op.create_check_constraint(
        "ck_job_chunks_priority_range",
        "job_chunks",
        "priority >= 0 AND priority <= 10",
    )
    op.create_check_constraint(
        "ck_job_chunks_retry_count_positive",
        "job_chunks",
        "retry_count >= 0",
    )


def downgrade() -> None:
    # Drop check constraints
    op.drop_constraint("ck_job_chunks_retry_count_positive", "job_chunks", type_="check")
    op.drop_constraint("ck_job_chunks_priority_range", "job_chunks", type_="check")
    op.drop_constraint("ck_job_chunks_status_valid", "job_chunks", type_="check")

    # Drop indexes
    op.drop_index("ix_job_chunks_task_id", table_name="job_chunks")
    op.drop_index("ix_job_chunks_priority_created", table_name="job_chunks")
    op.drop_index("ix_job_chunks_job_status", table_name="job_chunks")
    op.drop_index("ix_job_chunks_status", table_name="job_chunks")
    op.drop_index("ix_job_chunks_job_id", table_name="job_chunks")

    # Drop table
    op.drop_table("job_chunks")
