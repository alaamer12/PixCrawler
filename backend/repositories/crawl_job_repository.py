"""
CrawlJob repository for data access operations.

This module provides the repository pattern implementation for CrawlJob model,
handling all database queries and data access logic.

Classes:
    CrawlJobRepository: Repository for CrawlJob CRUD and queries

Features:
    - CRUD operations via BaseRepository
    - Custom queries for job management
    - Chunk tracking queries
    - Status-based filtering
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import CrawlJob
from .base import BaseRepository

__all__ = ['CrawlJobRepository']


# noinspection PyTypeChecker
class CrawlJobRepository(BaseRepository[CrawlJob]):
    """
    Repository for CrawlJob data access.

    Provides database operations for crawl jobs including CRUD,
    filtering, and chunk tracking queries.

    Attributes:
        session: Database session
        model: CrawlJob model class

    Example:
        >>> repo = CrawlJobRepository(session)
        >>> job = await repo.create(project_id=1, name="Test Job")
        >>> jobs = await repo.get_by_project(project_id=1)
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize CrawlJob repository.

        Args:
            session: Database session
        """
        super().__init__(session, CrawlJob)

    async def get_by_project(self, project_id: int) -> List[CrawlJob]:
        """
        Get all jobs for a specific project.

        Args:
            project_id: Project ID

        Returns:
            List of crawl jobs
        """
        result = await self.session.execute(
            select(CrawlJob)
            .where(CrawlJob.project_id == project_id)
            .order_by(CrawlJob.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_status(self, status: str) -> List[CrawlJob]:
        """
        Get all jobs with specific status.

        Args:
            status: Job status (pending, running, completed, failed)

        Returns:
            List of crawl jobs
        """
        result = await self.session.execute(
            select(CrawlJob).where(CrawlJob.status == status)
        )
        return list(result.scalars().all())

    async def get_active_jobs(self) -> List[CrawlJob]:
        """
        Get all currently running jobs.

        Returns:
            List of active crawl jobs
        """
        return await self.get_by_status("running")

    async def get_pending_jobs(self) -> List[CrawlJob]:
        """
        Get all pending jobs.

        Returns:
            List of pending crawl jobs
        """
        return await self.get_by_status("pending")

    async def count_active_chunks(self) -> int:
        """
        Count total active chunks across all jobs.

        Returns:
            Total number of active chunks
        """
        result = await self.session.execute(
            select(func.sum(CrawlJob.active_chunks))
        )
        return result.scalar() or 0

    async def get_total_active_chunks(self) -> int:
        """
        Get total active chunks across all jobs.

        Alias for count_active_chunks for consistency.

        Returns:
            Total number of active chunks
        """
        return await self.count_active_chunks()

    async def update_progress(
        self,
        job_id: int,
        progress: int,
        downloaded_images: int,
        valid_images: Optional[int] = None
    ) -> Optional[CrawlJob]:
        """
        Update job progress metrics.

        This method only persists the provided values without any calculations
        or business logic. The service layer is responsible for calculating
        the correct values before calling this method.

        Args:
            job_id: Job ID
            progress: Progress percentage (0-100) - calculated by service
            downloaded_images: Number of downloaded images
            valid_images: Number of valid images (optional)

        Returns:
            Updated job or None if not found
        """
        job = await self.get_by_id(job_id)
        if not job:
            return None

        # Simple data persistence - no business logic
        update_data = {
            'progress': progress,
            'downloaded_images': downloaded_images
        }
        if valid_images is not None:
            update_data['valid_images'] = valid_images

        return await self.update(job, **update_data)

    async def update_chunk_counts(
        self,
        job_id: int,
        active_chunks: int,
        completed_chunks: int,
        failed_chunks: int
    ) -> Optional[CrawlJob]:
        """
        Update chunk tracking counters with absolute values.

        This method only persists the provided absolute values without any
        calculations. The service layer is responsible for calculating the
        correct chunk counts before calling this method.

        Args:
            job_id: Job ID
            active_chunks: Absolute count of active chunks
            completed_chunks: Absolute count of completed chunks
            failed_chunks: Absolute count of failed chunks

        Returns:
            Updated job or None if not found
        """
        job = await self.get_by_id(job_id)
        if not job:
            return None

        # Simple data persistence - no calculations or business logic
        return await self.update(
            job,
            active_chunks=active_chunks,
            completed_chunks=completed_chunks,
            failed_chunks=failed_chunks
        )

    async def update_status(
        self,
        job_id: int,
        status: str,
        completed_at: Optional[datetime] = None,
        progress: Optional[int] = None
    ) -> Optional[CrawlJob]:
        """
        Update job status and related fields.

        This method only persists the provided values. The service layer
        is responsible for determining the correct status, timestamp, and
        progress values based on business rules.

        Args:
            job_id: Job ID
            status: Job status (pending, running, completed, failed, etc.)
            completed_at: Completion timestamp (optional)
            progress: Progress percentage (optional)

        Returns:
            Updated job or None if not found
        """
        job = await self.get_by_id(job_id)
        if not job:
            return None

        # Simple data persistence - no business logic
        update_data = {'status': status}
        if completed_at is not None:
            update_data['completed_at'] = completed_at
        if progress is not None:
            update_data['progress'] = progress

        return await self.update(job, **update_data)

    async def add_task_id(self, job_id: int, task_id: str) -> Optional[CrawlJob]:
        """
        Add a Celery task ID to the job's task_ids array.

        This method appends a task ID to the JSONB task_ids array field.
        The service layer is responsible for ensuring task IDs are valid
        and properly tracked.

        Args:
            job_id: Job ID
            task_id: Celery task ID to add

        Returns:
            Updated job or None if not found
        """
        job = await self.get_by_id(job_id)
        if not job:
            return None

        # Get current task_ids or initialize empty list
        task_ids = job.task_ids if job.task_ids else []

        # Append new task_id if not already present
        if task_id not in task_ids:
            task_ids.append(task_id)

        return await self.update(job, task_ids=task_ids)

    async def mark_completed(self, job_id: int) -> Optional[CrawlJob]:
        """
        Mark a job as completed.

        Convenience method that sets status to 'completed', progress to 100,
        and sets the completed_at timestamp.

        Args:
            job_id: Job ID

        Returns:
            Updated job or None if not found
        """
        return await self.update_status(
            job_id=job_id,
            status='completed',
            completed_at=datetime.utcnow(),
            progress=100
        )

    async def mark_failed(self, job_id: int, error: str) -> Optional[CrawlJob]:
        """
        Mark a job as failed with error message.

        Convenience method that sets status to 'failed' and sets the
        completed_at timestamp. The error message is logged but not stored
        in the database as there is no error field in the schema.

        Note: Error details are maintained in Celery task results and logs.
        The service layer should log the error message before calling this method.

        Args:
            job_id: Job ID
            error: Error message describing the failure (for logging only)

        Returns:
            Updated job or None if not found
        """
        job = await self.get_by_id(job_id)
        if not job:
            return None

        # Note: error parameter is kept for API compatibility but not stored
        # The service layer should log errors before calling this method
        return await self.update(
            job,
            status='failed',
            completed_at=datetime.utcnow()
        )

    async def get_active_tasks(self, job_id: int) -> List[str]:
        """
        Get list of active Celery task IDs for a job.

        Retrieves the task_ids array from the job record. The service layer
        is responsible for determining which tasks are actually still active
        in Celery.

        Args:
            job_id: Job ID

        Returns:
            List of Celery task IDs (empty list if job not found or no tasks)
        """
        job = await self.get_by_id(job_id)
        if not job or not job.task_ids:
            return []

        return job.task_ids if isinstance(job.task_ids, list) else []

    async def get_image_stats(
        self,
        user_id: Optional[str] = None,
        dataset_ids: Optional[List[int]] = None
    ) -> dict:
        """
        Get aggregated image statistics from crawl jobs.

        Args:
            user_id: Optional user ID filter (not directly used as CrawlJob doesn't have user_id)
            dataset_ids: Optional list of dataset IDs to filter by

        Returns:
            Dictionary with image statistics:
                - total_images: Sum of downloaded_images across matching jobs
        """
        query = select(func.sum(CrawlJob.downloaded_images))
        
        # If dataset_ids provided, filter by them (assuming 1:1 mapping between dataset and job)
        # Note: This is a simplification. Ideally we'd join with Dataset table, but 
        # repositories should be independent. The service layer passes dataset_ids.
        if dataset_ids:
            query = query.where(CrawlJob.id.in_(dataset_ids))
            
        result = await self.session.execute(query)
        total_images = result.scalar() or 0
        
        return {
            "total_images": total_images
        }
