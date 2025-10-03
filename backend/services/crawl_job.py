"""
Crawl job service for managing image crawling tasks.

This module provides services for creating, managing, and executing image crawling
jobs using the PixCrawler builder package. It integrates with the shared Supabase
database and provides real-time status updates.

Classes:
    CrawlJobService: Service for managing crawl jobs

Functions:
    execute_crawl_job: Execute a crawl job asynchronously

Features:
    - Integration with PixCrawler builder package
    - Real-time job status updates
    - Progress tracking and error handling
    - Image metadata storage
"""

from typing import Dict, Any, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundError
from backend.database.models import CrawlJob, Project, Image, ActivityLog
# Import builder package for crawling functionality
from .base import BaseService

__all__ = [
    'CrawlJobService',
    'execute_crawl_job'
]


class CrawlJobService(BaseService):
    """
    Service for managing crawl jobs.

    Provides functionality for creating, updating, and executing
    image crawling jobs using the PixCrawler builder package.

    Attributes:
        session: Database session for data operations
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize crawl job service.

        Args:
            session: Database session
        """
        super().__init__()
        self.session = session

    async def create_job(
        self,
        project_id: int,
        name: str,
        keywords: List[str],
        max_images: int = 100,
        search_engine: str = "duckduckgo",
        config: Optional[Dict[str, Any]] = None,
        user_id: UUID = None
    ) -> CrawlJob:
        """
        Create a new crawl job.

        Args:
            project_id: ID of the project this job belongs to
            name: Name of the crawl job
            keywords: List of search keywords
            max_images: Maximum number of images to collect
            search_engine: Search engine to use
            config: Additional configuration options
            user_id: User ID for activity logging

        Returns:
            Created crawl job

        Raises:
            NotFoundError: If project is not found
            ValidationError: If job data is invalid
        """
        # Verify project exists
        project_result = await self.session.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project_result.scalar_one_or_none()

        if not project:
            raise NotFoundError(f"Project not found: {project_id}")

        # Create crawl job
        crawl_job = CrawlJob(
            project_id=project_id,
            name=name,
            keywords=keywords,
            max_images=max_images,
            status="pending"
        )

        self.session.add(crawl_job)
        await self.session.commit()
        await self.session.refresh(crawl_job)

        # Log activity
        if user_id:
            await self._log_activity(
                user_id=user_id,
                action="START_CRAWL_JOB",
                resource_type="crawl_job",
                resource_id=str(crawl_job.id),
                metadata={"name": name, "keywords": keywords}
            )

        self.log_operation("create_crawl_job", job_id=crawl_job.id,
                           project_id=project_id)
        return crawl_job

    async def get_job(self, job_id: int) -> Optional[CrawlJob]:
        """
        Get crawl job by ID.

        Args:
            job_id: Crawl job ID

        Returns:
            Crawl job or None if not found
        """
        result = await self.session.execute(
            select(CrawlJob).where(CrawlJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def update_job(
        self,
        job_id: int,
        status: str,
        progress: int = None,
        total_images: int = None,
        downloaded_images: int = None,
        valid_images: int = None,
        error_message: str = None
    ) -> None:
        """
        Update crawl job status and progress.

        Args:
            job_id: Crawl job ID
            status: New job status
            progress: Progress percentage (0-100)
            total_images: Total images found
            downloaded_images: Number of images downloaded
            valid_images: Number of valid images
            error_message: Error message if job failed
        """
        raise NotImplementedError("Placeholder for update job")

    async def store_metadata(
        self,
        job_id: int,
        image_data: Dict[str, Any]
    ) -> Image:
        """
        Store image metadata in the database.

        Args:
            job_id: Crawl job ID
            image_data: Image metadata dictionary

        Returns:
            Created image record
        """
        image = Image(
            crawl_job_id=job_id,
            original_url=image_data["original_url"],
            filename=image_data["filename"],
            storage_url=image_data.get("storage_url"),
            width=image_data.get("width"),
            height=image_data.get("height"),
            file_size=image_data.get("file_size"),
            format=image_data.get("format"),
        )

        self.session.add(image)
        await self.session.commit()
        await self.session.refresh(image)

        return image

    async def _log_activity(
        self,
        user_id: UUID,
        action: str,
        resource_type: str = None,
        resource_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> None:
        """
        Log user activity.

        Args:
            user_id: User ID
            action: Action performed
            resource_type: Type of resource
            resource_id: Resource ID
            metadata: Additional metadata
        """
        activity_log = ActivityLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata=metadata or {}
        )

        self.session.add(activity_log)
        await self.session.commit()


async def execute_crawl_job(job_id: int) -> None:
    """
    Execute a crawl job asynchronously.

    This function runs the actual image crawling process using the
    PixCrawler builder package and updates the job status in real-time.

    Args:
        job_id: ID of the crawl job to execute
    """
    raise NotImplementedError("Placeholder for job execution")
