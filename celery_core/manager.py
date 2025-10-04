"""
Task management and monitoring utilities for PixCrawler Celery.

This module provides high-level task management functionality including
task submission, status tracking, cancellation, and monitoring across
all PixCrawler packages.

Classes:
    TaskManager: High-level task management interface
    TaskMonitor: Task monitoring and health checking utilities

Functions:
    get_task_manager: Get shared task manager instance
    get_task_monitor: Get shared task monitor instance

Features:
    - Unified task management across packages
    - Task status tracking and monitoring
    - Batch task operations
    - Health checking and diagnostics
    - Performance metrics collection
"""

import time
from functools import lru_cache
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field

from celery import group, chord, chain
from celery.result import AsyncResult, GroupResult

from logging_config import get_logger
from celery_core.app import get_celery_app
from celery_core.base import TaskResult, TaskStatus

logger = get_logger(__name__)

__all__ = [
    'TaskInfo',
    'TaskManager',
    'TaskMonitor',
    'get_task_manager',
    'get_task_monitor'
]


@dataclass
class TaskInfo:
    """Information about a submitted task."""
    task_id: str
    task_name: str
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    submitted_at: float = field(default_factory=time.time)
    queue: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'task_id': self.task_id,
            'task_name': self.task_name,
            'args': self.args,
            'kwargs': self.kwargs,
            'submitted_at': self.submitted_at,
            'queue': self.queue,
        }


class TaskManager:
    """
    High-level task management interface.
    
    This class provides a unified interface for managing tasks across
    all PixCrawler packages, including submission, tracking, and cancellation.
    """
    
    def __init__(self):
        """Initialize the task manager."""
        self.app = get_celery_app()
        self.active_tasks: Dict[str, TaskInfo] = {}
    
    def submit_task(self, task_name: str, *args, **kwargs) -> str:
        """
        Submit a task for execution.
        
        Args:
            task_name: Name of the task to execute
            *args: Task arguments
            **kwargs: Task keyword arguments
            
        Returns:
            str: Task ID
        """
        try:
            # Get the task from the registry
            task = self.app.tasks.get(task_name)
            if not task:
                raise ValueError(f"Task '{task_name}' not found in registry")
            
            # Submit the task
            result = task.delay(*args, **kwargs)
            
            # Track the task
            task_info = TaskInfo(
                task_id=result.id,
                task_name=task_name,
                args=args,
                kwargs=kwargs,
                queue=getattr(task, 'queue', None)
            )
            self.active_tasks[result.id] = task_info
            
            logger.info(f"Submitted task {task_name} with ID {result.id}")
            return result.id
            
        except Exception as e:
            logger.error(f"Failed to submit task {task_name}: {e}")
            raise
    
    def submit_batch_tasks(self, tasks: List[Dict[str, Any]]) -> List[str]:
        """
        Submit multiple tasks as a batch.
        
        Args:
            tasks: List of task dictionaries with 'name', 'args', 'kwargs'
            
        Returns:
            List[str]: List of task IDs
        """
        task_ids = []
        
        for task_spec in tasks:
            task_name = task_spec['name']
            args = task_spec.get('args', ())
            kwargs = task_spec.get('kwargs', {})
            
            task_id = self.submit_task(task_name, *args, **kwargs)
            task_ids.append(task_id)
        
        logger.info(f"Submitted batch of {len(tasks)} tasks")
        return task_ids
    
    def submit_group_tasks(self, task_name: str, task_args_list: List[tuple]) -> str:
        """
        Submit tasks as a Celery group for parallel execution.
        
        Args:
            task_name: Name of the task to execute
            task_args_list: List of argument tuples for each task
            
        Returns:
            str: Group result ID
        """
        try:
            task = self.app.tasks.get(task_name)
            if not task:
                raise ValueError(f"Task '{task_name}' not found in registry")
            
            # Create group of tasks
            job = group(task.s(*args) for args in task_args_list)
            result = job.apply_async()
            
            logger.info(f"Submitted group of {len(task_args_list)} {task_name} tasks")
            return result.id
            
        except Exception as e:
            logger.error(f"Failed to submit group tasks {task_name}: {e}")
            raise
    
    def submit_chain_tasks(self, task_specs: List[Dict[str, Any]]) -> str:
        """
        Submit tasks as a Celery chain for sequential execution.
        
        Args:
            task_specs: List of task specifications
            
        Returns:
            str: Chain result ID
        """
        try:
            signatures = []
            
            for spec in task_specs:
                task_name = spec['name']
                args = spec.get('args', ())
                kwargs = spec.get('kwargs', {})
                
                task = self.app.tasks.get(task_name)
                if not task:
                    raise ValueError(f"Task '{task_name}' not found in registry")
                
                signatures.append(task.s(*args, **kwargs))
            
            # Create chain of tasks
            job = chain(*signatures)
            result = job.apply_async()
            
            logger.info(f"Submitted chain of {len(task_specs)} tasks")
            return result.id
            
        except Exception as e:
            logger.error(f"Failed to submit chain tasks: {e}")
            raise
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of a task.
        
        Args:
            task_id: Task ID
            
        Returns:
            Dict containing task status information
        """
        try:
            result = AsyncResult(task_id, app=self.app)
            
            status_info = {
                'task_id': task_id,
                'status': result.status,
                'result': result.result if result.ready() else None,
                'traceback': result.traceback if result.failed() else None,
                'date_done': result.date_done,
                'successful': result.successful(),
                'failed': result.failed(),
                'ready': result.ready(),
            }
            
            # Add task info if available
            if task_id in self.active_tasks:
                task_info = self.active_tasks[task_id]
                status_info.update({
                    'task_name': task_info.task_name,
                    'submitted_at': task_info.submitted_at,
                    'queue': task_info.queue,
                })
            
            return status_info
            
        except Exception as e:
            logger.error(f"Failed to get status for task {task_id}: {e}")
            return {
                'task_id': task_id,
                'status': 'UNKNOWN',
                'error': str(e)
            }
    
    def cancel_task(self, task_id: str, terminate: bool = False) -> bool:
        """
        Cancel a task.
        
        Args:
            task_id: Task ID to cancel
            terminate: Whether to terminate the task forcefully
            
        Returns:
            bool: True if cancellation was successful
        """
        try:
            self.app.control.revoke(task_id, terminate=terminate)
            
            # Remove from active tasks
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
            logger.info(f"Cancelled task {task_id} (terminate={terminate})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False
    
    def get_active_tasks(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all active tasks.
        
        Returns:
            Dict mapping task IDs to task information
        """
        active_info = {}
        
        for task_id, task_info in self.active_tasks.items():
            status = self.get_task_status(task_id)
            active_info[task_id] = {
                **task_info.to_dict(),
                'current_status': status['status'],
                'ready': status.get('ready', False),
            }
        
        return active_info
    
    def cleanup_completed_tasks(self) -> int:
        """
        Remove completed tasks from active tracking.
        
        Returns:
            int: Number of tasks cleaned up
        """
        completed_tasks = []
        
        for task_id in self.active_tasks:
            status = self.get_task_status(task_id)
            if status.get('ready', False):
                completed_tasks.append(task_id)
        
        for task_id in completed_tasks:
            del self.active_tasks[task_id]
        
        if completed_tasks:
            logger.info(f"Cleaned up {len(completed_tasks)} completed tasks")
        
        return len(completed_tasks)


class TaskMonitor:
    """
    Task monitoring and health checking utilities.
    
    This class provides monitoring functionality for Celery tasks and workers,
    including health checks, performance metrics, and system diagnostics.
    """
    
    def __init__(self):
        """Initialize the task monitor."""
        self.app = get_celery_app()
    
    def get_worker_stats(self) -> Dict[str, Any]:
        """
        Get statistics about active workers.
        
        Returns:
            Dict containing worker statistics
        """
        try:
            inspect = self.app.control.inspect()
            
            # Get worker information
            stats = inspect.stats()
            active = inspect.active()
            reserved = inspect.reserved()
            
            worker_info = {}
            
            if stats:
                for worker_name, worker_stats in stats.items():
                    worker_info[worker_name] = {
                        'stats': worker_stats,
                        'active_tasks': len(active.get(worker_name, [])) if active else 0,
                        'reserved_tasks': len(reserved.get(worker_name, [])) if reserved else 0,
                    }
            
            return {
                'workers': worker_info,
                'total_workers': len(worker_info),
                'total_active_tasks': sum(w['active_tasks'] for w in worker_info.values()),
                'total_reserved_tasks': sum(w['reserved_tasks'] for w in worker_info.values()),
            }
            
        except Exception as e:
            logger.error(f"Failed to get worker stats: {e}")
            return {'error': str(e)}
    
    def get_queue_info(self) -> Dict[str, Any]:
        """
        Get information about task queues.
        
        Returns:
            Dict containing queue information
        """
        return self.app.get_queue_info()
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a comprehensive health check.
        
        Returns:
            Dict containing health check results
        """
        start_time = time.time()
        
        health_info = {
            'timestamp': start_time,
            'status': 'healthy',
            'checks': {},
            'response_time': 0,
        }
        
        try:
            # Check broker connectivity
            inspect = self.app.control.inspect()
            ping_result = inspect.ping()
            
            health_info['checks']['broker_connectivity'] = {
                'status': 'ok' if ping_result else 'failed',
                'workers_responding': len(ping_result) if ping_result else 0,
            }
            
            # Check worker availability
            worker_stats = self.get_worker_stats()
            health_info['checks']['workers'] = {
                'status': 'ok' if worker_stats.get('total_workers', 0) > 0 else 'warning',
                'total_workers': worker_stats.get('total_workers', 0),
                'active_tasks': worker_stats.get('total_active_tasks', 0),
            }
            
            # Check queue configuration
            queue_info = self.get_queue_info()
            health_info['checks']['queues'] = {
                'status': 'ok',
                'configured_queues': len(queue_info.get('queues', [])),
            }
            
            # Overall status
            failed_checks = [
                check for check in health_info['checks'].values()
                if check['status'] == 'failed'
            ]
            
            if failed_checks:
                health_info['status'] = 'unhealthy'
            elif any(check['status'] == 'warning' for check in health_info['checks'].values()):
                health_info['status'] = 'degraded'
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_info['status'] = 'unhealthy'
            health_info['error'] = str(e)
        
        finally:
            health_info['response_time'] = time.time() - start_time
        
        return health_info
    
    def get_task_metrics(self) -> Dict[str, Any]:
        """
        Get task execution metrics.
        
        Returns:
            Dict containing task metrics
        """
        try:
            inspect = self.app.control.inspect()
            
            # Get registered tasks
            registered = inspect.registered()
            
            # Get active tasks
            active = inspect.active()
            
            # Get reserved tasks
            reserved = inspect.reserved()
            
            metrics = {
                'registered_tasks': {},
                'active_tasks': 0,
                'reserved_tasks': 0,
                'workers': 0,
            }
            
            if registered:
                # Count registered tasks per worker
                all_tasks = set()
                for worker_tasks in registered.values():
                    all_tasks.update(worker_tasks)
                
                metrics['registered_tasks'] = {
                    'total_unique_tasks': len(all_tasks),
                    'tasks': sorted(list(all_tasks)),
                }
                metrics['workers'] = len(registered)
            
            if active:
                metrics['active_tasks'] = sum(len(tasks) for tasks in active.values())
            
            if reserved:
                metrics['reserved_tasks'] = sum(len(tasks) for tasks in reserved.values())
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get task metrics: {e}")
            return {'error': str(e)}


@lru_cache()
def get_task_manager() -> TaskManager:
    """
    Get shared task manager instance.
    
    Returns:
        TaskManager: Shared task manager
    """
    return TaskManager()


@lru_cache()
def get_task_monitor() -> TaskMonitor:
    """
    Get shared task monitor instance.
    
    Returns:
        TaskMonitor: Shared task monitor
    """
    return TaskMonitor()