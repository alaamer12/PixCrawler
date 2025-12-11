"""
Workflow schemas for job orchestration.

This module defines Pydantic schemas for workflow management,
including state tracking, task management, and progress updates.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional, List, Dict

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    'WorkflowStatus',
    'TaskStatus',
    'WorkflowTaskCreate',
    'WorkflowTaskResponse',
    'WorkflowStateCreate',
    'WorkflowStateUpdate',
    'WorkflowStateResponse',
    'WorkflowProgressUpdate',
    'WorkflowRecoveryRequest',
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


class WorkflowTaskCreate(BaseModel):
    """Schema for creating a workflow task."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid',
    )

    task_name: str = Field(
        min_length=1,
        max_length=100,
        description="Task name",
        examples=["download_images", "validate_images", "deduplicate"],
    )

    task_type: str = Field(
        min_length=1,
        max_length=50,
        description="Task type",
        examples=["download", "validate", "deduplicate", "label"],
    )

    step_index: int = Field(
        ge=0,
        description="Step index in workflow",
        examples=[0, 1, 2],
    )

    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts",
    )

    dependencies: List[int] = Field(
        default_factory=list,
        description="Task IDs this task depends on",
    )

    estimated_duration: Optional[int] = Field(
        default=None,
        ge=0,
        description="Estimated duration in seconds",
    )


class WorkflowTaskResponse(BaseModel):
    """Schema for workflow task response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    workflow_id: int
    task_name: str
    task_type: str
    status: TaskStatus
    step_index: int
    celery_task_id: Optional[str] = None
    retry_count: int
    max_retries: int
    dependencies: List[int]
    result: Dict[str, Any]
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_duration: Optional[int] = None
    actual_duration: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class WorkflowStateCreate(BaseModel):
    """Schema for creating a workflow state."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid',
    )

    job_id: int = Field(
        gt=0,
        description="Job ID",
    )

    total_steps: int = Field(
        gt=0,
        le=100,
        description="Total number of workflow steps",
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Workflow metadata",
    )

    max_recovery_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum recovery attempts",
    )


class WorkflowStateUpdate(BaseModel):
    """Schema for updating workflow state."""

    model_config = ConfigDict(
        validate_assignment=True,
        extra='forbid',
    )

    status: Optional[WorkflowStatus] = None
    current_step: Optional[int] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class WorkflowProgressUpdate(BaseModel):
    """Schema for workflow progress updates."""

    model_config = ConfigDict(
        validate_assignment=True,
        extra='forbid',
    )

    current_step: int = Field(
        ge=0,
        description="Current step index",
    )

    progress: int = Field(
        ge=0,
        le=100,
        description="Progress percentage",
    )

    metadata: Optional[Dict[str, Any]] = None


class WorkflowStateResponse(BaseModel):
    """Schema for workflow state response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    status: WorkflowStatus
    current_step: int
    total_steps: int
    progress: int
    metadata: Dict[str, Any]
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_checkpoint: Optional[datetime] = None
    recovery_attempts: int
    max_recovery_attempts: int
    tasks: List[WorkflowTaskResponse] = []
    created_at: datetime
    updated_at: datetime


class WorkflowRecoveryRequest(BaseModel):
    """Schema for workflow recovery request."""

    model_config = ConfigDict(
        validate_assignment=True,
        extra='forbid',
    )

    from_step: int = Field(
        ge=0,
        description="Step index to recover from",
    )

    reason: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Recovery reason",
    )
