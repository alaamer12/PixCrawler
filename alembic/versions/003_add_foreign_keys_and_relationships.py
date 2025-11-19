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
    
    # Add index on Project.user_id if not exists
    op.create_index(
        "ix_projects_user_id",
        "projects",
        ["user_id"],
        if_not_exists=True,
    )
    
    # Add index on Project.status if not exists
    op.create_index(
        "ix_projects_status",
        "projects",
        ["status"],
        if_not_exists=True,
    )
    
    # Add FK constraint on Project.user_id
    op.create_foreign_key(
        "fk_projects_user_id",
        "projects",
        "profiles",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    
    # Add indexes on CrawlJob
    op.create_index(
        "ix_crawl_jobs_project_id",
        "crawl_jobs",
        ["project_id"],
        if_not_exists=True,
    )
    
    op.create_index(
        "ix_crawl_jobs_status",
        "crawl_jobs",
        ["status"],
        if_not_exists=True,
    )
    
    op.create_index(
        "ix_crawl_jobs_project_status",
        "crawl_jobs",
        ["project_id", "status"],
        if_not_exists=True,
    )
    
    op.create_index(
        "ix_crawl_jobs_created_at",
        "crawl_jobs",
        ["created_at"],
        if_not_exists=True,
    )
    
    # Add FK constraint on CrawlJob.project_id
    op.create_foreign_key(
        "fk_crawl_jobs_project_id",
        "crawl_jobs",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    
    # Add indexes on Image
    op.create_index(
        "ix_images_crawl_job_id",
        "images",
        ["crawl_job_id"],
        if_not_exists=True,
    )
    
    op.create_index(
        "ix_images_created_at",
        "images",
        ["created_at"],
        if_not_exists=True,
    )
    
    # Add FK constraint on Image.crawl_job_id
    op.create_foreign_key(
        "fk_images_crawl_job_id",
        "images",
        "crawl_jobs",
        ["crawl_job_id"],
        ["id"],
        ondelete="CASCADE",
    )
    
    # Add indexes on ActivityLog
    op.create_index(
        "ix_activity_logs_user_id",
        "activity_logs",
        ["user_id"],
        if_not_exists=True,
    )
    
    op.create_index(
        "ix_activity_logs_timestamp",
        "activity_logs",
        ["timestamp"],
        if_not_exists=True,
    )
    
    op.create_index(
        "ix_activity_logs_user_timestamp",
        "activity_logs",
        ["user_id", "timestamp"],
        if_not_exists=True,
    )
    
    op.create_index(
        "ix_activity_logs_resource",
        "activity_logs",
        ["resource_type", "resource_id"],
        if_not_exists=True,
    )
    
    # Add FK constraint on ActivityLog.user_id
    op.create_foreign_key(
        "fk_activity_logs_user_id",
        "activity_logs",
        "profiles",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    
    # Add FK constraint on CreditAccount.user_id (already has unique constraint)
    op.create_foreign_key(
        "fk_credit_accounts_user_id",
        "credit_accounts",
        "profiles",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    
    # Add FK constraints on CreditTransaction
    op.create_foreign_key(
        "fk_credit_transactions_account_id",
        "credit_transactions",
        "credit_accounts",
        ["account_id"],
        ["id"],
        ondelete="CASCADE",
    )
    
    op.create_foreign_key(
        "fk_credit_transactions_user_id",
        "credit_transactions",
        "profiles",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    
    # Add FK constraint on APIKey.user_id
    op.create_foreign_key(
        "fk_api_keys_user_id",
        "api_keys",
        "profiles",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    
    # Add FK constraint on Notification.user_id
    op.create_foreign_key(
        "fk_notifications_user_id",
        "notifications",
        "profiles",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    
    # Add FK constraint on NotificationPreference.user_id
    op.create_foreign_key(
        "fk_notification_preferences_user_id",
        "notification_preferences",
        "profiles",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    
    # Add FK constraint on UsageMetric.user_id
    op.create_foreign_key(
        "fk_usage_metrics_user_id",
        "usage_metrics",
        "profiles",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Revert schema changes."""
    
    # Drop foreign keys
    op.drop_constraint("fk_usage_metrics_user_id", "usage_metrics", type_="foreignkey")
    op.drop_constraint("fk_notification_preferences_user_id", "notification_preferences", type_="foreignkey")
    op.drop_constraint("fk_notifications_user_id", "notifications", type_="foreignkey")
    op.drop_constraint("fk_api_keys_user_id", "api_keys", type_="foreignkey")
    op.drop_constraint("fk_credit_transactions_user_id", "credit_transactions", type_="foreignkey")
    op.drop_constraint("fk_credit_transactions_account_id", "credit_transactions", type_="foreignkey")
    op.drop_constraint("fk_credit_accounts_user_id", "credit_accounts", type_="foreignkey")
    op.drop_constraint("fk_activity_logs_user_id", "activity_logs", type_="foreignkey")
    op.drop_constraint("fk_images_crawl_job_id", "images", type_="foreignkey")
    op.drop_constraint("fk_crawl_jobs_project_id", "crawl_jobs", type_="foreignkey")
    op.drop_constraint("fk_projects_user_id", "projects", type_="foreignkey")
    
    # Drop indexes
    op.drop_index("ix_activity_logs_resource", "activity_logs", if_exists=True)
    op.drop_index("ix_activity_logs_user_timestamp", "activity_logs", if_exists=True)
    op.drop_index("ix_activity_logs_timestamp", "activity_logs", if_exists=True)
    op.drop_index("ix_activity_logs_user_id", "activity_logs", if_exists=True)
    op.drop_index("ix_images_created_at", "images", if_exists=True)
    op.drop_index("ix_images_crawl_job_id", "images", if_exists=True)
    op.drop_index("ix_crawl_jobs_created_at", "crawl_jobs", if_exists=True)
    op.drop_index("ix_crawl_jobs_project_status", "crawl_jobs", if_exists=True)
    op.drop_index("ix_crawl_jobs_status", "crawl_jobs", if_exists=True)
    op.drop_index("ix_crawl_jobs_project_id", "crawl_jobs", if_exists=True)
    op.drop_index("ix_projects_status", "projects", if_exists=True)
    op.drop_index("ix_projects_user_id", "projects", if_exists=True)
