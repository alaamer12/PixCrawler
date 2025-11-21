"""
Base task classes and utilities for PixCrawler Celery tasks.

This module provides abstract base classes and utilities for creating
consistent task implementations across all PixCrawler packages.

Classes:
    BaseTask: Abstract base class for all PixCrawler tasks
    TaskResult: Standardized task result format
    TaskContext: Task execution context information

Functions:
    create_task_result: Helper for creating standardized task results
    handle_task_error: Standardized error handling for tasks

Features:
    - Consistent task interface across packages
    - Standardized result formats
    - Built-in error handling and retry logic
    - Task context management
    - Performance monitoring integration
"""

import time
import traceback
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from enum import Enum

from celery import Task
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

from utility.logging_config import get_logger

logger = get_logger(__name__)

__all__ = [
    'TaskStatus',
    'TaskResult',
    'TaskContext',
    'BaseTask',
    'create_task_result',
    'handle_task_error'
]


class TaskStatus(Enum):
    """Enumeration of task statuses."""
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"


class TaskResult(BaseModel):
    """
    Enhanced standardized task result format with Pydantic V2 validation.

    This class provides a consistent structure for task results across
    all PixCrawler packages, making it easier to handle and process
    task outcomes with comprehensive validation.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid',
        use_enum_values=True,
        validate_default=True
    )

    task_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique task identifier",
        examples=["abc123-def456-ghi789", "task_12345"]
    )
    task_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Name of the executed task",
        examples=["process_dataset_task", "validate_images_task"]
    )
    status: TaskStatus = Field(
        ...,
        description="Current task status",
        examples=[TaskStatus.SUCCESS, TaskStatus.FAILURE, TaskStatus.PENDING]
    )
    result: Optional[Any] = Field(
        default=None,
        description="Task execution result data",
        examples=[{"processed": 100}, None, "Task completed successfully"]
    )
    error: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Error message if task failed",
        examples=[None, "Connection timeout", "Invalid input data"]
    )
    traceback: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Error traceback if task failed",
        examples=[None, "Traceback (most recent call last)..."]
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional task metadata",
        examples=[{}, {"worker": "worker1", "queue": "default"}]
    )
    start_time: Optional[float] = Field(
        default=None,
        ge=0,
        description="Task start timestamp",
        examples=[None, 1640995200.0, 1640995260.5]
    )
    end_time: Optional[float] = Field(
        default=None,
        ge=0,
        description="Task end timestamp",
        examples=[None, 1640995300.0, 1640995320.8]
    )
    processing_time: Optional[float] = Field(
        default=None,
        ge=0,
        le=86400,  # 24 hours max
        description="Task processing time in seconds",
        examples=[None, 45.2, 120.7, 0.5]
    )
    retry_count: int = Field(
        default=0,
        ge=0,
        le=20,
        description="Number of retry attempts",
        examples=[0, 1, 3, 5]
    )

    @field_validator('task_id', 'task_name')
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        """Ensure task ID and name are not empty after stripping."""
        if not v.strip():
            raise ValueError("Task ID and name cannot be empty")
        return v.strip()

    @field_validator('error', 'traceback')
    @classmethod
    def validate_error_fields(cls, v: Optional[str]) -> Optional[str]:
        """Clean error and traceback fields."""
        if v is not None:
            v = v.strip()
            return v if v else None
        return v

    @model_validator(mode='after')
    def validate_result_consistency(self) -> 'TaskResult':
        """Validate result consistency and relationships."""
        # Validate time relationships
        if self.start_time is not None and self.end_time is not None:
            if self.end_time < self.start_time:
                raise ValueError("end_time cannot be before start_time")

            # Calculate processing time if not provided
            if self.processing_time is None:
                self.processing_time = self.end_time - self.start_time
            else:
                # Validate provided processing time
                expected_time = self.end_time - self.start_time
                if abs(self.processing_time - expected_time) > 1.0:  # 1 second tolerance
                    raise ValueError("processing_time doesn't match start_time and end_time")

        # Validate status-specific fields
        if self.status == TaskStatus.FAILURE:
            if not self.error:
                raise ValueError("Failed tasks must have an error message")
        elif self.status == TaskStatus.SUCCESS:
            if self.error:
                # Log warning but allow (might be warnings, not errors)
                logger.warning(f"Successful task {self.task_id} has error message: {self.error}")

        # Validate retry count for different statuses
        if self.status == TaskStatus.RETRY and self.retry_count == 0:
            raise ValueError("Retry status requires retry_count > 0")

        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary with enum values."""
        return self.model_dump(mode='json')

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskResult':
        """Create TaskResult from dictionary with validation."""
        # Handle status conversion if it's a string
        if isinstance(data.get('status'), str):
            data['status'] = TaskStatus(data['status'])
        return cls(**data)


class TaskContext(BaseModel):
    """
    Enhanced task execution context with Pydantic V2 validation.

    This class provides context information for task execution,
    including request details, retry information, and metadata.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid',
        validate_default=True
    )

    task_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique task identifier",
        examples=["abc123-def456-ghi789", "task_12345"]
    )
    task_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Name of the task",
        examples=["process_dataset_task", "validate_images_task"]
    )
    args: tuple = Field(
        default_factory=tuple,
        description="Task positional arguments",
        examples=[(), ("arg1", "arg2"), (123, "test")]
    )
    kwargs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Task keyword arguments",
        examples=[{}, {"param1": "value1"}, {"max_images": 100, "format": "jpg"}]
    )
    retries: int = Field(
        default=0,
        ge=0,
        le=20,
        description="Current retry count",
        examples=[0, 1, 3, 5]
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=20,
        description="Maximum allowed retries",
        examples=[0, 3, 5, 10]
    )
    eta: Optional[float] = Field(
        default=None,
        ge=0,
        description="Estimated time of arrival (timestamp)",
        examples=[None, 1640995200.0, 1640995260.5]
    )
    expires: Optional[float] = Field(
        default=None,
        ge=0,
        description="Task expiration timestamp",
        examples=[None, 1640995200.0, 1640995260.5]
    )

    @field_validator('task_id', 'task_name')
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        """Ensure task ID and name are not empty after stripping."""
        if not v.strip():
            raise ValueError("Task ID and name cannot be empty")
        return v.strip()

    @model_validator(mode='after')
    def validate_context_consistency(self) -> 'TaskContext':
        """Validate context consistency and relationships."""
        # Validate retry settings
        if self.retries > self.max_retries:
            raise ValueError("retries cannot exceed max_retries")

        # Validate time relationships
        if self.eta is not None and self.expires is not None:
            if self.expires < self.eta:
                raise ValueError("expires cannot be before eta")

        # Validate current time relationships
        current_time = time.time()
        if self.eta is not None and self.eta < current_time - 86400:  # 24 hours ago
            raise ValueError("eta cannot be more than 24 hours in the past")

        if self.expires is not None and self.expires < current_time:
            raise ValueError("expires cannot be in the past")

        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return self.model_dump(mode='json')


class BaseTask(Task, ABC):
    """
    Abstract base class for all PixCrawler tasks.

    This class provides a consistent interface and common functionality
    for all tasks across PixCrawler packages, including error handling,
    retry logic, and result formatting.
    """

    # Task configuration
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 60}
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes
    retry_jitter = True

    def __call__(self, *args, **kwargs):
        """
        Enhanced task execution with context management and error handling.
        """
        context = TaskContext(
            task_id=self.request.id,
            task_name=self.name,
            args=args,
            kwargs=kwargs,
            retries=self.request.retries,
            max_retries=self.max_retries,
        )

        start_time = time.time()

        try:
            logger.info(f"Starting task {self.name} (ID: {self.request.id})")

            # Call the actual task implementation
            result = self.run_with_context(context, *args, **kwargs)

            end_time = time.time()
            processing_time = end_time - start_time

            task_result = create_task_result(
                task_id=context.task_id,
                task_name=context.task_name,
                status=TaskStatus.SUCCESS,
                result=result,
                start_time=start_time,
                end_time=end_time,
                processing_time=processing_time,
                retry_count=context.retries
            )

            logger.info(f"Task {self.name} completed successfully in {processing_time:.2f}s")
            return task_result.to_dict()

        except Exception as exc:
            end_time = time.time()
            processing_time = end_time - start_time

            error_result = handle_task_error(
                context=context,
                error=exc,
                start_time=start_time,
                end_time=end_time,
                processing_time=processing_time
            )

            # Check if we should retry
            if context.retries < context.max_retries:
                logger.warning(f"Task {self.name} failed, retrying ({context.retries + 1}/{context.max_retries})")
                raise self.retry(exc=exc, countdown=self._get_retry_countdown(context.retries))
            else:
                logger.error(f"Task {self.name} failed after {context.retries} retries")
                return error_result.to_dict()

    def run_with_context(self, context: TaskContext, *args, **kwargs) -> Any:
        """
        Run the task with context information.

        This method should be implemented by subclasses instead of the
        standard run() method to get access to task context.

        Args:
            context: Task execution context
            *args: Task arguments
            **kwargs: Task keyword arguments

        Returns:
            Task result
        """
        return self.run(*args, **kwargs)

    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """
        Abstract method for task implementation.

        This method must be implemented by subclasses to define
        the actual task logic.

        Args:
            *args: Task arguments
            **kwargs: Task keyword arguments

        Returns:
            Task result
        """
        pass

    @staticmethod
    def _get_retry_countdown(retry_count: int) -> int:
        """
        Calculate retry countdown with exponential backoff.

        Args:
            retry_count: Current retry count

        Returns:
            Countdown in seconds
        """
        base_countdown = 60  # 1 minute base
        max_countdown = 600  # 10 minutes max

        countdown = min(base_countdown * (2 ** retry_count), max_countdown)
        return countdown

    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds."""
        logger.debug(f"Task {self.name} (ID: {task_id}) succeeded")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails."""
        logger.error(f"Task {self.name} (ID: {task_id}) failed: {exc}")

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried."""
        logger.warning(f"Task {self.name} (ID: {task_id}) retrying: {exc}")


def create_task_result(
    task_id: str,
    task_name: str,
    status: TaskStatus,
    result: Optional[Any] = None,
    error: Optional[str] = None,
    traceback: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
    processing_time: Optional[float] = None,
    retry_count: int = 0
) -> TaskResult:
    """
    Helper function for creating standardized task results.

    Args:
        task_id: Task ID
        task_name: Task name
        status: Task status
        result: Task result data
        error: Error message if failed
        traceback: Error traceback if failed
        metadata: Additional metadata
        start_time: Task start time
        end_time: Task end time
        processing_time: Task processing time
        retry_count: Number of retries

    Returns:
        TaskResult: Standardized task result
    """
    return TaskResult(
        task_id=task_id,
        task_name=task_name,
        status=status,
        result=result,
        error=error,
        traceback=traceback,
        metadata=metadata or {},
        start_time=start_time,
        end_time=end_time,
        processing_time=processing_time,
        retry_count=retry_count
    )


def handle_task_error(
    context: TaskContext,
    error: Exception,
    start_time: float,
    end_time: float,
    processing_time: float
) -> TaskResult:
    """
    Standardized error handling for tasks.

    Args:
        context: Task context
        error: Exception that occurred
        start_time: Task start time
        end_time: Task end time
        processing_time: Task processing time

    Returns:
        TaskResult: Error result
    """
    error_message = str(error)
    error_traceback = traceback.format_exc()

    logger.error(f"Task {context.task_name} failed: {error_message}")
    logger.debug(f"Task {context.task_name} traceback: {error_traceback}")

    return create_task_result(
        task_id=context.task_id,
        task_name=context.task_name,
        status=TaskStatus.FAILURE,
        error=error_message,
        traceback=error_traceback,
        start_time=start_time,
        end_time=end_time,
        processing_time=processing_time,
        retry_count=context.retries
    )
