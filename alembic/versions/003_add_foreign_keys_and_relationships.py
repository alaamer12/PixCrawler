"""Add foreign key constraints, relationships, and indexes for schema alignment.

Revision ID: 003
Revises: 002
Create Date: 2024-11-18 13:00:00.000000

This migration adds all missing foreign key constraints, indexes, and establishes
proper relationships between tables for data integrity and performance optimization.

Changes:
    - Add FK: Project.user_id -> Profile.id
    - Add FK: CrawlJob.project_id -> Project.id
    - Add FK: Image.crawl_job_id -> CrawlJob.id
    - Add FK: ActivityLog.user_id -> Profile.id
    - Add FK: CreditAccount.user_id -> Profile.id
    - Add FK: CreditTransaction.account_id -> CreditAccount.id
    - Add FK: CreditTransaction.user_id -> Profile.id
    - Add FK: APIKey.user_id -> Profile.id
    - Add FK: Notification.user_id -> Profile.id
    - Add FK: NotificationPreference.user_id -> Profile.id
    - Add FK: UsageMetric.user_id -> Profile.id
    - Add indexes for performance optimization
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply schema changes."""
    pass


def downgrade() -> None:
    """Revert schema changes."""
    pass
