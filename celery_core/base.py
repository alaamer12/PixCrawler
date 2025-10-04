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
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from celery import Task
from celery.exceptions import Retry

from logging_config import get_logger

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


@dataclass
class TaskResult:
    """
    Standardized task result format.
    
    This class provides a consistent structure for task results across
    all PixCrawler packages, making it easier to handle and process
    task outcomes.
    """
    task_id: str
    task_name: str
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    traceback: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    processing_time: Optional[float] = None
    retry_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'task_id': self.task_id,
            'task_name': self.task_name,
            'status': self.status.value,
            'result': self.result,
            'error': self.error,
            'traceback': self.traceback,
            'metadata': self.metadata,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'processing_time': self.processing_time,
            'retry_count': self.retry_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskResult':
        """Create TaskResult from dictionary."""
        data['status'] = TaskStatus(data['status'])
        return cls(**data)


@dataclass
class TaskContext:
    """
    Task execution context information.
    
    This class provides context information for task execution,
    including request details, retry information, and metadata.
    """
    task_id: str
    task_name: str
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    retries: int = 0
    max_retries: int = 3
    eta: Optional[float] = None
    expires: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            'task_id': self.task_id,
            'task_name': self.task_name,
            'args': self.args,
            'kwargs': self.kwargs,
            'retries': self.retries,
            'max_retries': self.max_retries,
            'eta': self.eta,
            'expires': self.expires,
        }


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
    
    def _get_retry_countdown(self, retry_count: int) -> int:
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