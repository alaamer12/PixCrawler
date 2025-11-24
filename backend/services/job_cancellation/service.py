"""
Job cancellation service implementation.

This module handles the cancellation of running crawl jobs, including:
- Updating job status
- Revoking Celery tasks
- Cleaning up temporary resources
- Notifying users via activity logs
"""

import os
import shutil
import asyncio
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundError, ValidationError
from backend.models import CrawlJob
from backend.repositories import CrawlJobRepository, ActivityLogRepository
from celery_core.manager import get_task_manager
from utility.logging_config import get_logger

logger = get_logger(__name__)


class JobCancellationService:
    """
    Service for handling job cancellation.
    
    Attributes:
        session: Database session
        crawl_job_repo: Repository for crawl jobs
        activity_log_repo: Repository for activity logs
        task_manager: Celery task manager
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the service.

        Args:
            session: Database session
        """
        self.session = session
        self.crawl_job_repo = CrawlJobRepository(session)
        self.activity_log_repo = ActivityLogRepository(session)
        self.task_manager = get_task_manager()

    async def cancel_job(self, job_id: int, user_id: UUID) -> bool:
        """
        Cancel a running or pending crawl job.

        Args:
            job_id: ID of the job to cancel
            user_id: ID of the user requesting cancellation

        Returns:
            bool: True if cancellation was successful

        Raises:
            NotFoundError: If job not found
            ValidationError: If job cannot be cancelled
        """
        # 1. Get job and validate status
        job = await self.crawl_job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError(f"Crawl job not found: {job_id}")

        if job.status not in ["pending", "running"]:
            raise ValidationError(f"Cannot cancel job with status: {job.status}")

        logger.info(f"Starting cancellation for job {job_id} (User: {user_id})")

        # 2. Update status to cancelling
        job.status = "cancelling"
        await self.session.commit()

        try:
            # 3. Revoke Celery tasks
            revoked_count = await self._revoke_tasks(job)
            logger.info(f"Revoked {revoked_count} tasks for job {job_id}")

            # 4. Clean up resources
            await self._cleanup_resources(job_id)

            # 5. Update final status
            job.status = "cancelled"
            job.completed_at = datetime.utcnow()
            
            # 6. Log activity
            await self.activity_log_repo.create(
                user_id=user_id,
                action="CANCEL_CRAWL_JOB",
                resource_type="crawl_job",
                resource_id=str(job.id),
                metadata={
                    "revoked_tasks": revoked_count,
                    "previous_status": job.status
                }
            )
            
            await self.session.commit()
            logger.info(f"Successfully cancelled job {job_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {e}")
            # Attempt to revert status or mark as failed cancellation?
            # For now, we leave it as 'cancelling' or mark as 'failed' if critical
            # But usually 'cancelled' is safer even if cleanup failed partially.
            job.status = "cancelled" # Force cancelled state even if cleanup fails
            job.error = f"Cancellation warning: {str(e)}"
            await self.session.commit()
            raise

    async def _revoke_tasks(self, job: CrawlJob) -> int:
        """
        Revoke all Celery tasks associated with the job.

        Args:
            job: Crawl job instance

        Returns:
            int: Number of tasks revoked
        """
        revoked_count = 0
        
        # Revoke tasks tracked in task_ids
        if job.task_ids:
            for task_id in job.task_ids:
                if self.task_manager.cancel_task(task_id, terminate=True):
                    revoked_count += 1
        
        # Also try to find tasks by job_id if not explicitly tracked
        # This depends on how tasks are named/tagged. 
        # For now, we rely on task_ids.
        
        return revoked_count

    async def _cleanup_resources(self, job_id: int) -> None:
        """
        Clean up temporary resources (files, directories).

        Args:
            job_id: Job ID
        """
        # Define temp directory path (must match builder config)
        temp_dir = f"/tmp/crawl_{job_id}"
        
        if os.path.exists(temp_dir):
            try:
                # Run in thread pool to avoid blocking event loop
                await asyncio.to_thread(shutil.rmtree, temp_dir, ignore_errors=True)
                logger.info(f"Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp directory {temp_dir}: {e}")
