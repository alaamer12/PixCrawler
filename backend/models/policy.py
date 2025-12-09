"""
Policy models for dataset lifecycle management.

This module provides SQLAlchemy models for defining and tracking
archival and cleanup policies for datasets.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
if TYPE_CHECKING:
    from . import Dataset

__all__ = [
    'ArchivalPolicy',
    'CleanupPolicy',
    'PolicyExecutionLog',
]


class ArchivalPolicy(Base, TimestampMixin):
    """
    Archival policy model.

    Defines rules for moving datasets to different storage tiers
    based on age or inactivity.

    Attributes:
        id: Serial primary key
        name: Policy name
        description: Optional policy description
        is_active: Whether policy is active
        days_until_archive: Number of days before archiving
        target_tier: Target storage tier (e.g., 'warm', 'cold')
        filter_criteria: JSON criteria for applying policy (e.g., specific tags)
    """

    __tablename__ = "archival_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true"
    )

    days_until_archive: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Days since creation or last access before archiving"
    )

    target_tier: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="cold",
        comment="Target storage tier: hot, warm, cold"
    )

    filter_criteria: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Criteria to filter datasets (e.g., {'project_id': 1})"
    )

    # Indexes
    __table_args__ = (
        Index("ix_archival_policies_is_active", "is_active"),
    )


class CleanupPolicy(Base, TimestampMixin):
    """
    Cleanup policy model.

    Defines rules for deleting datasets or artifacts based on
    age, status, or other criteria.

    Attributes:
        id: Serial primary key
        name: Policy name
        description: Optional policy description
        is_active: Whether policy is active
        days_until_cleanup: Number of days before cleanup
        cleanup_target: What to cleanup (e.g., 'full_dataset', 'temp_files', 'failed_jobs')
        filter_criteria: JSON criteria for applying policy
    """

    __tablename__ = "cleanup_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true"
    )

    days_until_cleanup: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Days since creation/completion before cleanup"
    )

    cleanup_target: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="temp_files",
        comment="Target: full_dataset, temp_files, failed_jobs"
    )

    filter_criteria: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Criteria to filter datasets"
    )

    # Indexes
    __table_args__ = (
        Index("ix_cleanup_policies_is_active", "is_active"),
    )


class PolicyExecutionLog(Base):
    """
    Log of policy executions.

    Tracks when policies were applied and their outcome.

    Attributes:
        id: Serial primary key
        policy_type: Type of policy (archival, cleanup)
        policy_id: ID of the policy executed
        dataset_id: ID of the dataset affected
        status: Execution status (success, failed, skipped)
        details: JSON details about execution (e.g., bytes moved, files deleted)
        executed_at: Timestamp of execution
    """

    __tablename__ = "policy_execution_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    policy_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="archival or cleanup"
    )

    policy_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    dataset_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("datasets.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="success"
    )

    details: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True
    )

    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()"
    )

    # Relationships
    dataset: Mapped[Optional["Dataset"]] = relationship(
        "Dataset",
        lazy="joined"
    )

    # Indexes
    __table_args__ = (
        Index("ix_policy_logs_executed_at", "executed_at"),
        Index("ix_policy_logs_type_status", "policy_type", "status"),
    )
