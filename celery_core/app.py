"""
Celery application for PixCrawler.

This module provides the main Celery application instance with production-ready
configuration including task routing, priority queues, and rate limiting.

Functions:
    get_celery_app: Get the shared Celery application instance
    setup_task_queues: Configure task queues and routing
    revoke_task: Revoke a running task

Features:
    - Priority-based task queues (crawl, validation, maintenance)
    - Task routing by package and priority
    - Rate limiting for API-bound tasks
    - Scheduled tasks via Celery Beat
    - Task revocation support
"""

from functools import lru_cache

from celery import Celery
from celery.schedules import crontab
from celery.signals import setup_logging
from kombu import Exchange, Queue

from utility.logging_config import get_logger
from celery_core.config import get_celery_settings

logger = get_logger(__name__)

__all__ = [
    'app',
    'celery_app',
    'get_celery_app',
    'revoke_task'
]


@setup_logging.connect
def config_loggers(*args, **kwargs) -> None:
    """Configure Loguru logging for Celery workers."""
    # Celery will use the centralized Loguru configuration
    pass


@lru_cache()
def get_celery_app() -> Celery:
    """
    Get the shared Celery application instance.

    Returns:
        Configured Celery application
    """
    settings = get_celery_settings()

    # Create standard Celery app
    app = Celery('pixcrawler')

    # Configure from settings
    app.config_from_object(settings.get_celery_config())

    # Setup priority queues
    setup_task_queues(app)

    # Setup Celery Beat schedule
    setup_beat_schedule(app)

    logger.info(f"Initialized Celery app with broker: {settings.broker_url}")
    return app


def setup_task_queues(app: Celery) -> None:
    """
    Configure task queues with priorities and routing.

    Queues:
        - crawl: High priority, for image crawling tasks
        - validation: Medium priority, for image validation
        - maintenance: Low priority, for cleanup and background tasks
        - default: Standard priority, for general tasks

    Args:
        app: Celery application instance
    """
    default_exchange = Exchange('tasks', type='direct', durable=True)

    app.conf.task_queues = (
        Queue('crawl', exchange=default_exchange, routing_key='crawl', priority=9),
        Queue('validation', exchange=default_exchange, routing_key='validation', priority=5),
        Queue('maintenance', exchange=default_exchange, routing_key='maintenance', priority=1),
        Queue('default', exchange=default_exchange, routing_key='default', priority=5),
    )

    # Task routing by pattern
    app.conf.task_routes = {
        'builder.tasks.*': {'queue': 'crawl', 'priority': 9},
        'validator.tasks.*': {'queue': 'validation', 'priority': 5},
        'celery_core.cleanup_*': {'queue': 'maintenance', 'priority': 1},
        'celery_core.health_check': {'queue': 'maintenance', 'priority': 3},
        'temp_storage.*': {'queue': 'maintenance', 'priority': 2},
        'backend.tasks.temp_storage_cleanup.*': {'queue': 'maintenance', 'priority': 2},
    }

    logger.info("Configured task queues: crawl, validation, maintenance, default")


def setup_beat_schedule(app: Celery) -> None:
    """
    Configure Celery Beat periodic tasks.

    Scheduled tasks:
        - cleanup_expired_results: Daily at 2 AM
        - health_check: Every 5 minutes
        - temp_storage_scheduled_cleanup: Every hour
        - temp_storage_emergency_check: Every 5 minutes
        - temp_storage_orphaned_cleanup: Every 6 hours

    Args:
        app: Celery application instance
    """
    settings = get_celery_settings()

    if settings.beat_schedule_enabled:
        app.conf.beat_schedule = {
            'cleanup-expired-results': {
                'task': 'celery_core.cleanup_expired_results',
                'schedule': crontab(hour=2, minute=0),  # 2 AM daily
                'kwargs': {'max_age_hours': 24},
            },
            'health-check': {
                'task': 'celery_core.health_check',
                'schedule': 300.0,  # Every 5 minutes
            },
            # Temp Storage Cleanup Tasks
            'temp-storage-scheduled-cleanup': {
                'task': 'backend.tasks.temp_storage_cleanup.task_scheduled_cleanup',
                'schedule': crontab(minute=0),  # Every hour at minute 0
            },
            'temp-storage-emergency-check': {
                'task': 'backend.tasks.temp_storage_cleanup.task_get_storage_stats',
                'schedule': 300.0,  # Every 5 minutes - check if emergency cleanup needed
                'options': {
                    'expires': 240,  # Expire after 4 minutes to avoid overlap
                }
            },
            'temp-storage-orphaned-cleanup': {
                'task': 'backend.tasks.temp_storage_cleanup.task_cleanup_orphaned_files',
                'schedule': crontab(hour='*/6', minute=30),  # Every 6 hours at minute 30
                'kwargs': {'max_age_hours': 24},
            },
        }
        logger.info("Configured Celery Beat schedule with temp storage cleanup tasks")


def revoke_task(task_id: str, terminate: bool = True, signal: str = 'SIGTERM') -> None:
    """
    Revoke a running task.

    Args:
        task_id: Task ID to revoke
        terminate: Whether to terminate the task immediately
        signal: Signal to send to the worker (SIGTERM or SIGKILL)

    Example:
        >>> revoke_task('abc-123-def-456', terminate=True)
    """
    app = get_celery_app()
    app.control.revoke(task_id, terminate=terminate, signal=signal)
    logger.info(f"Revoked task {task_id} (terminate={terminate})")


# Create the main Celery app instance
app = get_celery_app()

# Export for use by other packages
celery_app = app
