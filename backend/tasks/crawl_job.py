"""
Celery tasks for the backend package.

This module defines the Celery tasks that orchestrate backend services,
specifically the crawl job execution.
"""

from typing import Optional

from celery_core.app import celery_app
from celery_core.base import BaseTask
from utility.logging_config import get_logger
from backend.services.crawl_job import execute_crawl_job as execute_crawl_job_service

logger = get_logger(__name__)

@celery_app.task(
    bind=True,
    base=BaseTask,
    name='backend.tasks.execute_crawl_job',
    queue='crawl',
    acks_late=True,
    track_started=True
)
def execute_crawl_job(
    self,
    job_id: int,
    user_id: Optional[str] = None,
    tier: Optional[str] = None
) -> None:
    """
    Execute a crawl job asynchronously.

    This task wraps the execute_crawl_job service function.

    Args:
        self: Celery task instance
        job_id: ID of the crawl job to execute
        user_id: User ID (used for rate limiting tracking)
        tier: User's subscription tier (used for rate limiting tracking)
    """
    import asyncio
    logger.info(f"Starting crawl job task for job {job_id}")
    try:
        # Run async service in a new event loop
        asyncio.run(execute_crawl_job_service(job_id=job_id, user_id=user_id, tier=tier))
        logger.info(f"Crawl job task for job {job_id} completed successfully")
    except Exception as e:
        logger.error(f"Crawl job task for job {job_id} failed: {str(e)}")
        raise
