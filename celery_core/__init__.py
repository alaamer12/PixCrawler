"""
PixCrawler Celery Core Package.

This package provides shared Celery infrastructure for the PixCrawler project,
including centralized configuration, task base classes, and management utilities.

Main Components:
    - CelerySettings: Pydantic Settings for Celery configuration
    - CeleryApp: Enhanced Celery application with PixCrawler features
    - BaseTask: Abstract base class for all PixCrawler tasks
    - TaskManager: High-level task management interface
    - TaskMonitor: Task monitoring and health checking utilities

Usage:
    from celery_core import get_celery_app, BaseTask, get_task_manager
    
    # Get the shared Celery app
    app = get_celery_app()
    
    # Create a custom task
    class MyTask(BaseTask):
        def run(self, *args, **kwargs):
            return {"result": "success"}
    
    # Use task manager
    manager = get_task_manager()
    task_id = manager.submit_task("my_task", arg1="value")
"""

from celery_core.config import CelerySettings, get_celery_settings
from celery_core.app import CeleryApp, create_celery_app, get_celery_app
from celery_core.base import (
    BaseTask,
    TaskResult,
    TaskContext,
    TaskStatus,
    create_task_result,
    handle_task_error
)
from celery_core.manager import (
    TaskManager,
    TaskMonitor,
    TaskInfo,
    get_task_manager,
    get_task_monitor
)

# Version information
__version__ = "0.1.0"
__author__ = "PixCrawler Team"
__email__ = "team@pixcrawler.com"

# Main exports
__all__ = [
    # Configuration
    'CelerySettings',
    'get_celery_settings',
    
    # Application
    'CeleryApp',
    'create_celery_app',
    'get_celery_app',
    
    # Base classes and utilities
    'BaseTask',
    'TaskResult',
    'TaskContext',
    'TaskStatus',
    'create_task_result',
    'handle_task_error',
    
    # Management
    'TaskManager',
    'TaskMonitor',
    'TaskInfo',
    'get_task_manager',
    'get_task_monitor',
    
    # Version info
    '__version__',
]