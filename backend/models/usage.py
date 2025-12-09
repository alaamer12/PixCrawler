"""
Usage and analytics models for PixCrawler.

This module defines SQLAlchemy ORM models for tracking user usage,
metrics, and analytics.
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

# noinspection PyPep8Naming
from sqlalchemy import (
    Date,
    DateTime,
    Integer,
    Numeric,
    UniqueConstraint,
    func,
    UUID as SQLAlchemyUUID,
    CheckConstraint,
    Index,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

__all__ = [
    'UsageMetric',
]


class UsageMetric(Base):
    """
    Usage metric model for tracking daily user activity.

    Stores daily metrics for images processed, storage used,
    API calls, and bandwidth consumption with limits.

    Attributes:
        id: UUID primary key
        user_id: Reference to profiles.id
        metric_date: Date for metrics
        images_processed: Images processed count
        images_limit: Images processing limit
        storage_used_gb: Storage used in GB
        storage_limit_gb: Storage limit in GB
        api_calls: API calls count
        api_calls_limit: API calls limit
        bandwidth_used_gb: Bandwidth used in GB
        bandwidth_limit_gb: Bandwidth limit in GB
        created_at: Creation timestamp
    """

    __tablename__ = "usage_metrics"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )

    # Foreign key
    user_id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Date
    metric_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    # Image metrics
    images_processed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    images_limit: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10000,
        server_default="10000",
    )

    # Storage metrics
    storage_used_gb: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )

    storage_limit_gb: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("100.00"),
        server_default="100.00",
    )

    # API metrics
    api_calls: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    api_calls_limit: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=50000,
        server_default="50000",
    )

    # Bandwidth metrics
    bandwidth_used_gb: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )

    bandwidth_limit_gb: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("500.00"),
        server_default="500.00",
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "metric_date", name="uq_usage_metrics_user_date"),
        CheckConstraint("images_processed >= 0", name="ck_usage_metrics_images_processed_positive"),
        CheckConstraint("images_limit > 0", name="ck_usage_metrics_images_limit_positive"),
        CheckConstraint("storage_used_gb >= 0", name="ck_usage_metrics_storage_used_positive"),
        CheckConstraint("storage_limit_gb > 0", name="ck_usage_metrics_storage_limit_positive"),
        CheckConstraint("api_calls >= 0", name="ck_usage_metrics_api_calls_positive"),
        CheckConstraint("api_calls_limit > 0", name="ck_usage_metrics_api_calls_limit_positive"),
        CheckConstraint("bandwidth_used_gb >= 0", name="ck_usage_metrics_bandwidth_used_positive"),
        CheckConstraint("bandwidth_limit_gb > 0", name="ck_usage_metrics_bandwidth_limit_positive"),
        Index("ix_usage_metrics_user_id", "user_id"),
        Index("ix_usage_metrics_metric_date", "metric_date"),
        Index("ix_usage_metrics_user_date", "user_id", "metric_date"),
    )
