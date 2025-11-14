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
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from backend.core.exceptions import NotFoundError, ValidationError
from backend.database.connection import AsyncSessionLocal
from backend.models import CrawlJob, Image
from backend.repositories import (
    CrawlJobRepository,
    ProjectRepository,
    ImageRepository,
    ActivityLogRepository
)
from backend.utils.metrics_collector import MetricsCollector
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
    """

    def __init__(
        self,
        crawl_job_repo: CrawlJobRepository,
        project_repo: ProjectRepository,
        image_repo: ImageRepository,
        activity_log_repo: ActivityLogRepository
    ) -> None:
        """
        Initialize crawl job service with repositories.

        Args:
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
        if not project:
            raise NotFoundError(f"Project not found: {project_id}")

        # Validate keywords
        if not keywords:
            raise ValidationError("Keywords cannot be empty")

        # Create crawl job using repository
        crawl_job = await self.crawl_job_repo.create(
            project_id=project_id,
            name=name,
            keywords={"keywords": keywords},
            max_images=max_images,
            status="pending"
        )

        # Log activity
        if user_id:
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

    async def update_job_progress(
        self,
        job_id: int,
        progress: int,
        downloaded_images: int,
        valid_images: Optional[int] = None
    ) -> Optional[CrawlJob]:
        """
        Update crawl job progress.

        Args:
            job_id: Crawl job ID
            progress: Progress percentage (0-100)
            downloaded_images: Number of images downloaded
            valid_images: Number of valid images

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



async def execute_crawl_job(job_id: int) -> None:
    """
    Execute a crawl job asynchronously.

    This function runs the actual image crawling process using the
    PixCrawler builder package and updates the job status in real-time.
    Also collects metrics for download, validation, and upload operations.

    Args:
        job_id: ID of the crawl job to execute
    """
    async with AsyncSessionLocal() as session:
        try:
            # Initialize repositories and services
            crawl_job_repo = CrawlJobRepository(session)
            image_repo = ImageRepository(session)
            metrics_collector = MetricsCollector(session, service_name="crawl-job")
            
            # Get job
            job = await crawl_job_repo.get_by_id(job_id)
            if not job:
                raise NotFoundError(f"Crawl job not found: {job_id}")
            
            # Update job status
            job.status = "processing"
            job.started_at = datetime.utcnow()
            await session.commit()
            
            # Track total processing time
            async with metrics_collector.track_operation(
                "total_processing",
                metadata={"job_id": job_id, "max_images": job.max_images}
            ):
                # Phase 1: Download images
                downloaded_count = 0
                async with metrics_collector.track_operation(
                    "download",
                    metadata={"job_id": job_id}
                ):
                    # TODO: Implement actual download using builder package
                    # For now, this is a placeholder
                    # downloaded_count = await download_images(job.keywords, job.max_images)
                    pass
                
                # Track download success rate
                total_attempted = job.max_images
                await metrics_collector.record_success_rate(
                    "download",
                    downloaded_count,
                    total_attempted,
                    metadata={"job_id": job_id}
                )
                
                # Update job progress
                job.downloaded_images = downloaded_count
                job.total_images = downloaded_count
                await session.commit()
                
                # Phase 2: Validate images
                valid_count = 0
                if downloaded_count > 0:
                    async with metrics_collector.track_operation(
                        "validate",
                        metadata={"job_id": job_id, "image_count": downloaded_count}
                    ):
                        # TODO: Implement actual validation
                        # valid_count = await validate_images(job_id, downloaded_count)
                        valid_count = downloaded_count  # Placeholder
                    
                    # Track validation success rate
                    await metrics_collector.record_success_rate(
                        "validate",
                        valid_count,
                        downloaded_count,
                        metadata={"job_id": job_id}
                    )
                    
                    # Update job progress
                    job.valid_images = valid_count
                    await session.commit()
                
                # Phase 3: Upload to storage
                uploaded_count = 0
                if valid_count > 0:
                    async with metrics_collector.track_operation(
                        "upload",
                        metadata={"job_id": job_id, "image_count": valid_count}
                    ):
                        # TODO: Implement actual upload
                        # uploaded_count = await upload_images(job_id, valid_count)
                        uploaded_count = valid_count  # Placeholder
                    
                    # Track upload success rate
                    await metrics_collector.record_success_rate(
                        "upload",
                        uploaded_count,
                        valid_count,
                        metadata={"job_id": job_id}
                    )
            
            # Flush all metrics
            await metrics_collector.flush()
            
            # Update job status
            job.status = "completed"
            job.progress = 100
            job.completed_at = datetime.utcnow()
            await session.commit()
            
        except Exception as e:
            # Update job status to failed
            async with AsyncSessionLocal() as error_session:
                error_repo = CrawlJobRepository(error_session)
                error_job = await error_repo.get_by_id(job_id)
                if error_job:
                    error_job.status = "failed"
                    error_job.completed_at = datetime.utcnow()
                    await error_session.commit()
            
            # Record failure metric
            async with AsyncSessionLocal() as metrics_session:
                metrics_collector = MetricsCollector(metrics_session, service_name="crawl-job")
                await metrics_collector.record_success_rate(
                    "total_processing",
                    0,
                    1,
                    metadata={"job_id": job_id, "error": str(e)}
                )
                await metrics_collector.flush()
            
            raise
