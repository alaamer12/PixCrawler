"""
Core Celery tasks for PixCrawler.

This module provides basic monitoring and maintenance tasks that are
shared across all PixCrawler packages.

Tasks:
    health_check: Basic health check task
    cleanup_expired_results: Clean up expired task results
"""

from typing import Dict, Any
from datetime import datetime, timedelta

from celery_core.base import BaseTask
from celery_core.base import BaseTask as Self
from celery_core.app import get_celery_app
from utility.logging_config import get_logger

logger = get_logger(__name__)

# Get the shared Celery app
app = get_celery_app()


@app.task(bind=True, base=BaseTask, name='celery_core.health_check', rate_limit='12/h')
def health_check(self: Self) -> Dict[str, Any]:
    """
    Basic health check task for monitoring Celery workers.

    Returns:
        Dict containing health check information
    """
    try:
        return {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'worker_id': self.request.hostname,
            'task_id': self.request.id,
            'app_name': app.main,
        }
    except Exception as exc:
        logger.error(f"Health check failed: {exc}")
        raise


@app.task(bind=True, base=BaseTask, name='celery_core.cleanup_expired_results', rate_limit='1/h')
def cleanup_expired_results(self: Self, max_age_hours: int = 24) -> Dict[str, Any]:
    """
    Clean up expired task results from the result backend.

    Args:
        self:
        max_age_hours: Maximum age of results to keep in hours

    Returns:
        Dict containing cleanup information
    """
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

        # This is a placeholder - actual implementation would depend on the backend
        # For Redis, you might use SCAN and DEL commands
        # For database backends, you'd run DELETE queries

        logger.info(f"Cleaning up results older than {cutoff_time}")

        return {
            'status': 'completed',
            'cutoff_time': cutoff_time.isoformat(),
            'max_age_hours': max_age_hours,
            'timestamp': datetime.utcnow().isoformat(),
        }
    except Exception as exc:
        logger.error(f"Cleanup failed: {exc}")
        raise


@app.task(bind=True, base=BaseTask, name='celery_core.get_worker_stats', rate_limit='60/h')
def get_worker_stats(self: Self) -> Dict[str, Any]:
    """
    Get basic worker statistics.

    Returns:
        Dict containing worker statistics
    """
    try:
        # Get basic worker information
        inspect = app.control.inspect()

        stats = {
            'timestamp': datetime.utcnow().isoformat(),
            'worker_id': self.request.hostname,
            'active_tasks': len(inspect.active() or {}),
            'reserved_tasks': len(inspect.reserved() or {}),
            'app_info': {
                'name': app.main,
                'broker': app.conf.broker_url,
                'backend': app.conf.result_backend,
            }
        }

        return stats
    except Exception as exc:
        logger.error(f"Failed to get worker stats: {exc}")
        raise
