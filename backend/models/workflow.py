"""
Workflow state models for job orchestration.

This module provides models for tracking workflow execution state,
task dependencies, and recovery information.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, Index, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

__all__ = [
    'WorkflowStatus',
    'TaskStatus',
    'WorkflowState',
    'WorkflowTask',
]


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RECOVERING = "recovering"


class TaskStatus(str, Enum):
    """Individual task status within a workflow."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class WorkflowState(Base, TimestampMixin):
    """
    Workflow state model for tracking workflow execution.

    Persists workflow state for recovery and monitoring.

    Attributes:
        id: Serial primary key
        job_id: Reference to crawl_jobs.id (FK)
        status: Workflow status
        current_step: Current step index
        total_steps: Total number of steps
        progress: Progress percentage (0-100)
        workflow_metadata: Workflow-specific metadata (JSONB)
        error_message: Error message if failed
        started_at: Workflow start timestamp
        completed_at: Workflow completion timestamp
        last_checkpoint: Last successful checkpoint
        recovery_attempts: Number of recovery attempts
        max_recovery_attempts: Maximum allowed recovery attempts

    Relationships:
        tasks: Associated workflow tasks (one-to-many)
    """

    __tablename__ = "workflow_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("crawl_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )
    current_step: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_steps: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    workflow_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_checkpoint: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    recovery_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_recovery_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)

    # Relationships
    tasks: Mapped[list["WorkflowTask"]] = relationship(
        "WorkflowTask",
        back_populates="workflow",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Indexes
    __table_args__ = (
        Index("ix_workflow_states_job_id", "job_id"),
        Index("ix_workflow_states_status", "status"),
        Index("ix_workflow_states_job_status", "job_id", "status"),
        Index("ix_workflow_states_created_at", "created_at"),
    )

    @property
    def is_active(self) -> bool:
        """Check if workflow is currently active."""
        return self.status in [WorkflowStatus.RUNNING, WorkflowStatus.RECOVERING]

    @property
    def is_terminal(self) -> bool:
        """Check if workflow is in terminal state."""
        return self.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]

    @property
    def can_recover(self) -> bool:
        """Check if workflow can attempt recovery."""
        return self.recovery_attempts < self.max_recovery_attempts


class WorkflowTask(Base, TimestampMixin):
    """
    Workflow task model for tracking individual tasks within a workflow.

    Attributes:
        id: Serial primary key
        workflow_id: Reference to workflow_states.id (FK)
        task_name: Name of the task
        task_type: Type of task (e.g., 'download', 'validate', 'deduplicate')
        status: Task status
        step_index: Step index in workflow
        celery_task_id: Celery task ID for monitoring
        retry_count: Number of retry attempts
        max_retries: Maximum allowed retries
        dependencies: List of task IDs this task depends on (JSON)
        result: Task result data (JSONB)
        error_message: Error message if failed
        started_at: Task start timestamp
        completed_at: Task completion timestamp
        estimated_duration: Estimated duration in seconds
        actual_duration: Actual duration in seconds

    Relationships:
        workflow: Parent workflow (many-to-one)
    """

    __tablename__ = "workflow_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("workflow_states.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_name: Mapped[str] = mapped_column(String(100), nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    dependencies: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    result: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    estimated_duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    actual_duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    workflow: Mapped["WorkflowState"] = relationship(
        "WorkflowState",
        back_populates="tasks",
        lazy="joined",
    )

    # Indexes
    __table_args__ = (
        Index("ix_workflow_tasks_workflow_id", "workflow_id"),
        Index("ix_workflow_tasks_status", "status"),
        Index("ix_workflow_tasks_celery_task_id", "celery_task_id"),
        Index("ix_workflow_tasks_workflow_status", "workflow_id", "status"),
        Index("ix_workflow_tasks_created_at", "created_at"),
    )

    @property
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.retry_count < self.max_retries

    @property
    def is_complete(self) -> bool:
        """Check if task is complete."""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.SKIPPED]

    @property
    def is_failed(self) -> bool:
        """Check if task has failed."""
        return self.status == TaskStatus.FAILED
