"""
Crawl job service for managing image crawling tasks.

This module provides services for creating, managing, and executing image crawling
jobs using the PixCrawler builder package. It integrates with the shared Supabase
database and provides real-time status updates.

Classes:
    CrawlJobService: Service for managing crawl jobs
    RateLimiter: Tier-based concurrent job rate limiter

Exceptions:
    RateLimitExceeded: Raised when user exceeds concurrent job limit

Functions:
    execute_crawl_job: Execute a crawl job asynchronously

Features:
    - Integration with PixCrawler builder package
    - Real-time job status updates
    - Progress tracking and error handling
    - Image metadata storage
    - Repository pattern for clean architecture
    - Tier-based concurrent job rate limiting (Free: 1, Pro: 3, Enterprise: 10)
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from celery import current_app as celery_app
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
    'RateLimiter',
    'RateLimitExceeded',
    'execute_crawl_job'
]


# ============================================================================
# RATE LIMITING EXCEPTIONS AND CLASSES
# ============================================================================

class RateLimitExceeded(Exception):
    """
    Exception raised when a user exceeds their concurrent job limit.

    This exception should be caught by the API layer and returned as HTTP 429.

    Attributes:
        tier: User's subscription tier
        active_jobs: Current number of active jobs
        limit: Maximum allowed concurrent jobs for the tier
        message: Detailed error message with advice
    """

    def __init__(self, tier: str, active_jobs: int, limit: int):
        self.tier = tier
        self.active_jobs = active_jobs
        self.limit = limit
        self.message = (
            f"Rate limit exceeded for tier '{tier}'. "
            f"You currently have {active_jobs} active job(s), "
            f"but your tier allows only {limit} concurrent job(s). "
            f"Please wait for existing jobs to complete or upgrade your subscription."
        )
        super().__init__(self.message)


class RateLimiter:
    """
    Tier-based concurrent job rate limiter using Celery Core internals.

    This class enforces concurrent job limits based on user subscription tiers
    by inspecting active and reserved tasks across all 35 worker processes.

    How it works:
    1. Uses Celery's Inspect API to query all workers for active and reserved tasks
    2. Filters tasks by user_id to count user-specific concurrent jobs
    3. Compares count against tier-based limits
    4. Raises RateLimitExceeded if limit is exceeded

    Tier Limits:
        - Free: 1 concurrent job
        - Pro: 3 concurrent jobs
        - Enterprise: 10 concurrent jobs

    Note: This implementation uses Celery's inspect.active() and inspect.reserved()
    which query the worker state directly. With 35 workers, this provides accurate
    real-time concurrency tracking without additional infrastructure.
    """

    # Tier-based concurrent job limits
    TIER_LIMITS = {
        'free': 1,
        'pro': 3,
        'enterprise': 10
    }

    # Task name to monitor (should match your Celery task name)
    CRAWL_TASK_NAME = 'backend.tasks.execute_crawl_job'

    @classmethod
    def check_concurrency(cls, user_id: str, tier: str) -> None:
        """
        Check if user can start a new job based on their tier limit.

        This method queries all Celery workers to count the user's currently
        running jobs (both active and reserved) and compares against their
        tier limit.

        Implementation Details:
        - inspect.active(): Returns tasks currently being executed by workers
        - inspect.reserved(): Returns tasks that are assigned to workers but not yet started
        - Both are checked to ensure accurate concurrency counting
        - Tasks are filtered by user_id stored in task kwargs/args

        Args:
            user_id: User ID to check concurrency for
            tier: User's subscription tier ('free', 'pro', or 'enterprise')

        Raises:
            RateLimitExceeded: If user has reached their concurrent job limit
            ValueError: If tier is invalid

        Example:
            >>> RateLimiter.check_concurrency('user123', 'free')
            # Raises RateLimitExceeded if user already has 1 active job
        """
        # Normalize tier to lowercase
        tier = tier.lower()

        # Validate tier
        if tier not in cls.TIER_LIMITS:
            raise ValueError(
                f"Invalid tier '{tier}'. Must be one of: {list(cls.TIER_LIMITS.keys())}"
            )

        # Get the limit for this tier
        limit = cls.TIER_LIMITS[tier]

        # Get Celery inspector to query worker state
        # This connects to all 35 workers and retrieves their current state
        inspector = celery_app.control.inspect()

        # Count active jobs for this user
        # We check both active (currently running) and reserved (queued on worker)
        active_count = cls._count_user_jobs(inspector, user_id)

        # Check if user has reached their limit
        if active_count >= limit:
            raise RateLimitExceeded(
                tier=tier,
                active_jobs=active_count,
                limit=limit
            )

    @classmethod
    def _count_user_jobs(cls, inspector, user_id: str) -> int:
        """
        Count the number of active and reserved jobs for a specific user.

        This method queries Celery workers using the inspect API to count
        how many crawl jobs are currently running or queued for the user.

        Process:
        1. Query active tasks (currently executing) from all workers
        2. Query reserved tasks (queued on workers) from all workers
        3. Filter tasks by task name (execute_crawl_job)
        4. Extract user_id from task kwargs/args
        5. Count matching tasks

        Args:
            inspector: Celery inspect instance
            user_id: User ID to count jobs for

        Returns:
            Total count of active + reserved jobs for the user

        Note:
            - inspector.active() returns: {worker_name: [task_dict, ...]}
            - inspector.reserved() returns: {worker_name: [task_dict, ...]}
            - Each task_dict contains: {'id', 'name', 'args', 'kwargs', ...}
        """
        count = 0

        # Get active tasks from all workers
        # Returns dict: {worker_name: [task1, task2, ...], ...}
        active_tasks = inspector.active() or {}

        # Get reserved tasks from all workers
        # Reserved tasks are assigned to workers but not yet executing
        reserved_tasks = inspector.reserved() or {}

        # Combine both active and reserved tasks
        # We need to check both because:
        # - Active: tasks currently running
        # - Reserved: tasks queued on worker, about to run
        all_tasks = {}

        # Merge active tasks
        for worker_name, tasks in active_tasks.items():
            if worker_name not in all_tasks:
                all_tasks[worker_name] = []
            all_tasks[worker_name].extend(tasks)

        # Merge reserved tasks
        for worker_name, tasks in reserved_tasks.items():
            if worker_name not in all_tasks:
                all_tasks[worker_name] = []
            all_tasks[worker_name].extend(tasks)

        # Count tasks for this user across all workers
        for worker_name, tasks in all_tasks.items():
            for task in tasks:
                # Only count our crawl job tasks
                if task.get('name') == cls.CRAWL_TASK_NAME:
                    # Extract user_id from task arguments
                    # The task signature is: execute_crawl_job(job_id, user_id=..., tier=...)
                    task_kwargs = task.get('kwargs', {})
                    task_user_id = task_kwargs.get('user_id')

                    # If user_id matches, increment count
                    if task_user_id == user_id:
                        count += 1

        return count


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
        activity_log_repo: ActivityLogRepository,
        session: Optional[AsyncSession] = None
    ) -> None:
        """
        Initialize crawl job service with repositories.

        Args:
            crawl_job_repo: CrawlJob repository
            project_repo: Project repository
            image_repo: Image repository
            activity_log_repo: ActivityLog repository
            session: Optional database session (for backward compatibility)
        """
        super().__init__()
        self.crawl_job_repo = crawl_job_repo
        self.project_repo = project_repo
        self.image_repo = image_repo
        self.activity_log_repo = activity_log_repo
        self._session = session

    async def create_job(
        self,
        project_id: int,
        name: str,
        keywords: List[str],
        max_images: int = 100,
        user_id: Optional[str] = None,
        tier: str = 'free'
    ) -> CrawlJob:
        """
        Create a new crawl job with rate limiting.

        Args:
            project_id: ID of the project this job belongs to
            name: Name of the crawl job
            keywords: List of search keywords
            max_images: Maximum number of images to collect
            user_id: User ID for activity logging and rate limiting
            tier: User's subscription tier ('free', 'pro', or 'enterprise')

        Returns:
            Created crawl job

        Raises:
            NotFoundError: If project is not found
            ValidationError: If job data is invalid
            RateLimitExceeded: If user has reached concurrent job limit
        """
        # RATE LIMITING: Check if user can start a new job
        # This queries all 35 Celery workers to count active jobs for this user
        # and compares against their tier limit (Free: 1, Pro: 3, Enterprise: 10)
        if user_id:
            RateLimiter.check_concurrency(user_id, tier)
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

    async def update_job(
        self,
        job_id: int,
        status: str,
        error: Optional[str] = None,
        **updates: Any
    ) -> Optional[CrawlJob]:
        """
        Update crawl job status and metadata.

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


async def execute_crawl_job(
    job_id: int,
    user_id: Optional[str] = None,
    tier: Optional[str] = None,
    job_service: Optional[CrawlJobService] = None,
    session: Optional[AsyncSession] = None
) -> None:
    """
    Execute a crawl job asynchronously with retry logic.

    This function is called by Celery workers. The user_id and tier parameters
    are used by the RateLimiter to track concurrent jobs per user.

    Args:
        job_id: ID of the crawl job to execute
        user_id: User ID (used for rate limiting tracking)
        tier: User's subscription tier (used for rate limiting tracking)
        job_service: Optional pre-configured CrawlJobService
        session: Optional database session

    Raises:
        NotFoundError: If job not found
        ExternalServiceError: If job execution fails after retries

    Note:
        The user_id and tier are stored in task kwargs so the RateLimiter
        can identify and count this user's active jobs across all workers.
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

            progress = min(int((processed_count / job.max_images)
                           * 100), 100) if job.max_images > 0 else 0

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
            raise ExternalServiceError(
                f"Error during batch processing: {str(e)}") from e

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
