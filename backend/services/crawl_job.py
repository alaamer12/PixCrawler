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
    - Repository pattern for clean architecture
    - Repository pattern for clean architecture
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from backend.core.exceptions import NotFoundError, ValidationError
from backend.models import CrawlJob, Image
from backend.repositories import (
    CrawlJobRepository,
    ProjectRepository,
    ImageRepository,
    ActivityLogRepository
)
from backend.core.exceptions import NotFoundError, ValidationError
from backend.models import CrawlJob, Image
from backend.repositories import (
    CrawlJobRepository,
    ProjectRepository,
    ImageRepository,
    ActivityLogRepository
)
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
        crawl_job_repo: CrawlJob repository
        project_repo: Project repository
        image_repo: Image repository
        activity_log_repo: ActivityLog repository
        crawl_job_repo: CrawlJob repository
        project_repo: Project repository
        image_repo: Image repository
        activity_log_repo: ActivityLog repository
    """

    def __init__(
        self,
        crawl_job_repo: CrawlJobRepository,
        project_repo: ProjectRepository,
        image_repo: ImageRepository,
        activity_log_repo: ActivityLogRepository,
        session: Optional[AsyncSession] = None
    ) -> None:
    def __init__(
        self,
        crawl_job_repo: CrawlJobRepository,
        project_repo: ProjectRepository,
        image_repo: ImageRepository,
        activity_log_repo: ActivityLogRepository
    ) -> None:
        """
        Initialize crawl job service with repositories.
        Initialize crawl job service with repositories.

        Args:
            crawl_job_repo: CrawlJob repository
            project_repo: Project repository
            image_repo: Image repository
            activity_log_repo: ActivityLog repository
            session: Optional database session (for backward compatibility)
            crawl_job_repo: CrawlJob repository
            project_repo: Project repository
            image_repo: Image repository
            activity_log_repo: ActivityLog repository
        """
        super().__init__()
        self.crawl_job_repo = crawl_job_repo
        self.project_repo = project_repo
        self.image_repo = image_repo
        self.activity_log_repo = activity_log_repo
        self._session = session
        self.crawl_job_repo = crawl_job_repo
        self.project_repo = project_repo
        self.image_repo = image_repo
        self.activity_log_repo = activity_log_repo

    async def create_job(
        self,
        project_id: int,
        name: str,
        keywords: List[str],
        max_images: int = 100,
        user_id: Optional[str] = None
    ) -> CrawlJob:
        """
        Create a new crawl job.

        Args:
            project_id: ID of the project this job belongs to
            name: Name of the crawl job
            keywords: List of search keywords
            max_images: Maximum number of images to collect
            user_id: User ID for activity logging

        Returns:
            Created crawl job

        Raises:
            NotFoundError: If project is not found
            ValidationError: If job data is invalid
        """
        # Verify project exists using repository
        project = await self.project_repo.get_by_id(project_id)
        # Verify project exists using repository
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise NotFoundError(f"Project not found: {project_id}")

        # Validate keywords
        if not keywords:
            raise ValidationError("Keywords cannot be empty")

        # Create crawl job using repository
        crawl_job = await self.crawl_job_repo.create(
        # Validate keywords
        if not keywords:
            raise ValidationError("Keywords cannot be empty")

        # Create crawl job using repository
        crawl_job = await self.crawl_job_repo.create(
            project_id=project_id,
            name=name,
            keywords={"keywords": keywords},
            keywords={"keywords": keywords},
            max_images=max_images,
            status="pending"
        )

        # Log activity
        if user_id:
            await self.activity_log_repo.create(
                user_id=uuid.UUID(user_id),
            await self.activity_log_repo.create(
                user_id=uuid.UUID(user_id),
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
        return await self.crawl_job_repo.get_by_id(job_id)
        return await self.crawl_job_repo.get_by_id(job_id)

    async def update_job_progress(
    async def update_job_progress(
        self,
        job_id: int,
        progress: int,
        downloaded_images: int,
        valid_images: Optional[int] = None
    ) -> Optional[CrawlJob]:
        progress: int,
        downloaded_images: int,
        valid_images: Optional[int] = None
    ) -> Optional[CrawlJob]:
        """
        Update crawl job progress.
        Update crawl job progress.

        Args:
            job_id: Crawl job ID
            progress: Progress percentage (0-100)
            downloaded_images: Number of images downloaded
            valid_images: Number of valid images

        Returns:
            Updated job or None if not found
        """
        job = await self.crawl_job_repo.get_by_id(job_id)
        if not job:
            return None

        update_data = {
            "progress": progress,
            "downloaded_images": downloaded_images,
            "updated_at": datetime.utcnow()
        }

        if valid_images is not None:
            update_data["valid_images"] = valid_images

        return await self.crawl_job_repo.update(job, **update_data)

    async def get_jobs_by_project(self, project_id: int) -> List[CrawlJob]:
        """
        Get all jobs for a project.

        Args:
            project_id: Project ID

        Returns:
            List of crawl jobs
        """
        return await self.crawl_job_repo.get_by_project(project_id)

    async def get_active_jobs(self) -> List[CrawlJob]:
        """
        Get all active jobs.

        Returns:
            List of active crawl jobs
        """
        return await self.crawl_job_repo.get_active_jobs()

        Returns:
            Updated job or None if not found
        """
        return await self.crawl_job_repo.update_progress(
            job_id=job_id,
            progress=progress,
            downloaded_images=downloaded_images,
            valid_images=valid_images
        )
    
    async def get_jobs_by_project(self, project_id: int) -> List[CrawlJob]:
        """
        Get all jobs for a project.

        Args:
            project_id: Project ID

        Returns:
            List of crawl jobs
        """
        return await self.crawl_job_repo.get_by_project(project_id)
    
    async def get_active_jobs(self) -> List[CrawlJob]:
        """
        Get all active jobs.

        Returns:
            List of active crawl jobs
        """
        return await self.crawl_job_repo.get_active_jobs()

    async def store_image_metadata(
    async def store_image_metadata(
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
        return await self.image_repo.create(
        return await self.image_repo.create(
            crawl_job_id=job_id,
            original_url=image_data["original_url"],
            filename=image_data["filename"],
            storage_url=image_data.get("storage_url"),
            width=image_data.get("width"),
            height=image_data.get("height"),
            file_size=image_data.get("file_size"),
            format=image_data.get("format")
        )

    async def store_bulk_images(
        self,
        job_id: int,
        images_data: List[Dict[str, Any]]
    ) -> List[Image]:
        """
        Store multiple image metadata records in bulk.

        Args:
            job_id: Crawl job ID
            images_data: List of image metadata dictionaries

        Returns:
            List of created image records
        """
        # Add job_id to each image data
        for data in images_data:
            data['crawl_job_id'] = job_id

        return await self.image_repo.bulk_create(images_data)

    async def update_job(
            format=image_data.get("format")
        )
    
    async def store_bulk_images(
        self,
        job_id: int,
        status: str,
        error: Optional[str] = None,
        **updates: Any
    ) -> Optional[CrawlJob]:
        job_id: int,
        images_data: List[Dict[str, Any]]
    ) -> List[Image]:
        """
        Update crawl job status and metadata.
        Store multiple image metadata records in bulk.

        Args:
            job_id: Crawl job ID
            status: New status
            error: Optional error message
            **updates: Additional fields to update

        Returns:
            Updated job or None if not found
        """
        job = await self.crawl_job_repo.get_by_id(job_id)
        if not job:
            return None

        update_data = {"status": status, **updates}

        if error:
            update_data["error"] = error[:500]  # Truncate long error messages

        if status in ["completed", "failed", "cancelled"]:
            update_data["completed_at"] = datetime.utcnow()

        return await self.crawl_job_repo.update(job, **update_data)
            job_id: Crawl job ID
            images_data: List of image metadata dictionaries

        Returns:
            List of created image records
        """
        # Add job_id to each image data
        for data in images_data:
            data['crawl_job_id'] = job_id
        
        return await self.image_repo.bulk_create(images_data)



async def execute_crawl_job(
    job_id: int,
    job_service: Optional[CrawlJobService] = None,
    session: Optional[AsyncSession] = None
) -> None:
    """
    Execute a crawl job asynchronously with retry logic.

    Args:
        job_id: ID of the crawl job to execute
        job_service: Optional pre-configured CrawlJobService
        session: Optional database session
        
    Raises:
        NotFoundError: If job not found
        ExternalServiceError: If job execution fails after retries
    """
    import asyncio
    from datetime import datetime
    from typing import Dict, Any, List
    from backend.core.exceptions import (
        NotFoundError, ExternalServiceError
    )
    from backend.database.connection import AsyncSessionLocal
    from builder import Builder
    from backend.core.async_helpers import run_sync, run_in_threadpool

    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds
    BATCH_SIZE = 50

    # Use provided session or create a new one
    should_close_session = False
    if session is None:
        session = AsyncSessionLocal()
        should_close_session = True

    # Initialize service if not provided
    if job_service is None:
        job_service = CrawlJobService(
            crawl_job_repo=CrawlJobRepository(session),
            project_repo=ProjectRepository(session),
            image_repo=ImageRepository(session),
            activity_log_repo=ActivityLogRepository(session),
            session=session
        )

    try:
        async with session.begin():
            job = await job_service.get_job(job_id, session=session)
            if not job:
                raise NotFoundError(f"Crawl job not found: {job_id}")

            await job_service.update_job(
                job_id,
                status="running",
                started_at=datetime.utcnow(),
                session=session
            )

        # Initialize builder with async support
        builder_config = {
            "keywords": job.keywords.get("keywords", []),
            "max_images": job.max_images,
            "output_dir": f"/tmp/crawl_{job_id}",
            "concurrency": 5,
            "timeout": 30,
            "async_mode": True  # Enable async mode in builder
        }

        # Create builder instance in a thread pool
        builder = await run_sync(Builder, config=builder_config)

        # Process images in batches
        processed_count = 0
        valid_count = 0

        async def process_batch(batch: List[Dict[str, Any]]) -> None:
            nonlocal processed_count, valid_count
            if not batch:
                return

            processed_count += len(batch)
            valid_batch = [img for img in batch if img.get("is_valid", True)]
            valid_count += len(valid_batch)

            progress = min(int((processed_count / job.max_images) * 100), 100) if job.max_images > 0 else 0
            
            await job_service.update_job_progress(
                job_id=job_id,
                progress=progress,
                downloaded_images=processed_count,
                valid_images=valid_count,
                session=session
            )

            if valid_batch:
                await job_service.store_bulk_images(job_id, valid_batch, session=session)

        # Process results as they come using async generator
        try:
            # Get the async generator from builder
            async_gen = await run_in_threadpool(
                builder.generate_async_batches,
                batch_size=BATCH_SIZE
            )
            
            # Process batches as they come
            while True:
                try:
                    batch = await run_in_threadpool(next, async_gen)
                    await process_batch(batch)
                except StopAsyncIteration:
                    break
                    
        except Exception as e:
            raise ExternalServiceError(f"Error during batch processing: {str(e)}") from e
            
        # Ensure resources are cleaned up
        await run_in_threadpool(builder.cleanup)

        # Final update
        async with session.begin():
            await job_service.update_job(
                job_id,
                status="completed",
                progress=100,
                completed_at=datetime.utcnow(),
                downloaded_images=processed_count,
                valid_images=valid_count,
                session=session
            )

    except Exception as e:
        if 'session' in locals() and session.in_transaction():
            await session.rollback()
        
        if 'job_service' in locals() and 'job_id' in locals():
            async with session.begin():
                await job_service.update_job(
                    job_id,
                    status="failed",
                    error=str(e),
                    completed_at=datetime.utcnow(),
                    session=session
                )
        
        raise ExternalServiceError(f"Job execution failed: {str(e)}") from e
    
    finally:
        if should_close_session and 'session' in locals():
            await session.close()
