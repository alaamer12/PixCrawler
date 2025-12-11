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
    - Server-Sent Events (SSE) for real-time progress updates
"""
import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, AsyncGenerator, Union
from uuid import UUID

from celery_core.app import celery_app

# Optional SSE support
try:
    from sse_starlette.sse import EventSourceResponse
    SSE_AVAILABLE = True
except ImportError:
    SSE_AVAILABLE = False
    EventSourceResponse = None  # type: ignore

from backend.core.exceptions import NotFoundError, ValidationError
from backend.models import CrawlJob, Image
from backend.repositories import (
    CrawlJobRepository,
    ProjectRepository,
    ImageRepository,
    ActivityLogRepository,
    DatasetRepository,
)
from .base import BaseService
from backend.core.supabase import get_supabase_client
from utility.logging_config import get_logger

logger = get_logger(__name__)

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
        'hobby': 3,
        'pro': 10
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
        dataset_repo: DatasetRepository
    ) -> None:
        """
        Initialize crawl job service with repositories.

        Args:
            crawl_job_repo: CrawlJob repository
            project_repo: Project repository
            image_repo: Image repository
            activity_log_repo: ActivityLog repository
            dataset_repo: Dataset repository
        """
        super().__init__()
        self.crawl_job_repo = crawl_job_repo
        self.project_repo = project_repo
        self.image_repo = image_repo
        self.activity_log_repo = activity_log_repo
        self.dataset_repo = dataset_repo

    async def create_job(
        self,
        dataset_id: int,
        name: str,
        keywords: List[str],
        max_images: int = 100,
        user_id: Optional[str] = None,
        tier: str = 'free'
    ) -> CrawlJob:
        """
        Create a new crawl job with rate limiting.

        Args:
            dataset_id: ID of the dataset this job belongs to
            name: Name of the crawl job
            keywords: List of search keywords
            max_images: Maximum number of images to collect
            user_id: User ID for activity logging and rate limiting
            tier: User's subscription tier ('free', 'pro', or 'enterprise')

        Returns:
            Created crawl job

        Raises:
            NotFoundError: If dataset is not found
            ValidationError: If job data is invalid
            RateLimitExceeded: If user has reached concurrent job limit
        """
        # RATE LIMITING: Check if user can start a new job
        # This queries all 35 Celery workers to count active jobs for this user
        # and compares against their tier limit (Free: 1, Hobby: 3, Pro: 10)
        if user_id:
            # Determine actual user tier from credit account
            real_tier = await self._get_user_tier(user_id)
            RateLimiter.check_concurrency(user_id, real_tier)
        
        # Verify dataset exists using repository
        dataset = await self.dataset_repo.get_by_id(dataset_id)
        if not dataset:
            raise NotFoundError(f"Dataset not found: {dataset_id}")

        # Validate keywords
        if not keywords:
            raise ValidationError("Keywords cannot be empty")

        # Create crawl job using repository
        crawl_job = await self.crawl_job_repo.create(
            dataset_id=dataset_id,
            name=name,
            keywords={"keywords": keywords},
            max_images=max_images,
            status="pending"
        )

        # Log activity
        if user_id:
            await self.activity_log_repo.create(
                user_id=user_id,
                action="START_CRAWL_JOB",
                resource_type="crawl_job",
                resource_id=str(crawl_job.id),
                metadata={"name": name, "keywords": keywords}
            )

        self.log_operation("create_crawl_job", job_id=crawl_job.id,
                           dataset_id=dataset_id)
        return crawl_job

    async def start_job(
        self,
        job_id: int,
        user_id: str,
        engines: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Start a crawl job by dispatching Celery tasks.

        This method implements the complete job start workflow with idempotency:
        1. Retrieve and validate job exists
        2. Check job status for idempotency (return existing task_ids if already running)
        3. Validate job ownership
        4. Calculate total chunks (keywords × engines)
        5. Dispatch download tasks for each keyword-engine combination
        6. Store task IDs in database
        7. Update job status to 'running' with total_chunks
        8. Create notification

        Idempotency:
        - If job is already running, returns existing task_ids without dispatching new tasks
        - If job is not in pending status (and not running), returns 400 error

        Args:
            job_id: ID of the job to start
            user_id: ID of the user starting the job
            engines: List of search engines to use (default: ['google', 'bing', 'duckduckgo'])

        Returns:
            Dict with task_ids, status, total_chunks, and message

        Raises:
            NotFoundError: If job not found
            ValidationError: If job status doesn't allow starting or user doesn't own job
        """
        from builder.tasks import (
            task_download_google,
            task_download_bing,
            task_download_baidu,
            task_download_duckduckgo
        )

        # Step 1: Retrieve job
        job = await self.get_job(job_id)
        if not job:
            raise NotFoundError(f"Crawl job not found: {job_id}")

        # Step 2: Check job status for idempotency
        # If job is already running, return existing task_ids (idempotent behavior)
        if job.status == 'running':
            existing_task_ids = await self.crawl_job_repo.get_active_tasks(job_id)
            logger.info(
                f"Job {job_id} is already running. Returning existing task_ids (idempotent).",
                job_id=job_id,
                task_count=len(existing_task_ids)
            )
            return {
                "job_id": job_id,
                "status": "running",
                "task_ids": existing_task_ids,
                "total_chunks": job.total_chunks or 0,
                "message": f"Job is already running with {len(existing_task_ids)} tasks (idempotent response)"
            }

        # If job is not pending (and not running), it cannot be started
        if job.status != 'pending':
            raise ValidationError(
                f"Cannot start job with status '{job.status}'. "
                f"Only pending jobs can be started."
            )

        # Step 3: Validate ownership (get project through dataset)
        dataset = await self.dataset_repo.get_by_id(job.dataset_id)
        if not dataset:
            raise ValidationError("Dataset not found")
        
        project = await self.project_repo.get_by_id(dataset.project_id)
        if not project or str(project.user_id) != str(user_id):
            raise ValidationError("You do not have permission to start this job")

        # Step 4: Calculate total chunks
        keywords = job.keywords.get("keywords", [])
        if not keywords:
            raise ValidationError("Job has no keywords")

        # Default engines if not specified
        if not engines:
            engines = ['google', 'bing', 'duckduckgo']

        # Map engine names to task functions
        engine_tasks = {
            'google': task_download_google,
            'bing': task_download_bing,
            'baidu': task_download_baidu,
            'duckduckgo': task_download_duckduckgo
        }

        # Calculate total chunks (one chunk per keyword-engine combination)
        total_chunks = len(keywords) * len(engines)

        # Step 5: Dispatch tasks
        task_ids = []
        output_dir = f"/tmp/crawl_{job_id}"

        logger.info(
            f"Starting job {job_id}: {len(keywords)} keywords × {len(engines)} engines = {total_chunks} chunks",
            job_id=job_id,
            keywords=keywords,
            engines=engines,
            total_chunks=total_chunks
        )

        for keyword in keywords:
            for engine in engines:
                task_func = engine_tasks.get(engine.lower())
                if not task_func:
                    logger.warning(f"Unknown engine '{engine}', skipping")
                    continue

                # Dispatch task with serializable arguments only
                task = task_func.delay(
                    keyword=keyword,
                    output_dir=output_dir,
                    max_images=job.max_images // len(keywords),  # Distribute images across keywords
                    job_id=str(job_id),
                    user_id=user_id
                )

                task_ids.append(task.id)

                logger.debug(
                    f"Dispatched {engine} task for keyword '{keyword}': {task.id}",
                    job_id=job_id,
                    keyword=keyword,
                    engine=engine,
                    task_id=task.id
                )

        # Step 6: Update job status to 'running' with total_chunks and task_ids
        # Refetch job to avoid session issues
        fresh_job = await self.crawl_job_repo.get_by_id(job_id)
        if fresh_job:
            await self.crawl_job_repo.update(
                fresh_job,
                status='running',
                total_chunks=total_chunks,
                active_chunks=total_chunks,
                completed_chunks=0,
                failed_chunks=0,
                task_ids=task_ids,
                started_at=datetime.utcnow()
            )

        # Step 7: Log activity
        await self.activity_log_repo.create(
            user_id=uuid.UUID(user_id),
            action="START_CRAWL_JOB",
            resource_type="crawl_job",
            resource_id=str(job_id),
            metadata={
                "total_chunks": total_chunks,
                "task_count": len(task_ids),
                "engines": engines
            }
        )

        logger.info(
            f"Job {job_id} started successfully with {len(task_ids)} tasks",
            job_id=job_id,
            task_count=len(task_ids),
            total_chunks=total_chunks
        )

        return {
            "job_id": job_id,
            "status": "running",
            "task_ids": task_ids,
            "total_chunks": total_chunks,
            "message": f"Job started with {len(task_ids)} tasks"
        }

    async def get_job(self, job_id: int) -> Optional[CrawlJob]:
        """
        Get crawl job by ID.

        Args:
            job_id: Crawl job ID

        Returns:
            Crawl job or None if not found
        """
        return await self.crawl_job_repo.get_by_id(job_id)

    async def handle_task_completion(
        self,
        job_id: int,
        task_id: str,
        result: Dict[str, Any]
    ) -> None:
        """
        Handle Celery task completion callback with result deduplication.

        This method processes task completion results and updates the job state:
        1. Retrieve job from repository within a transaction
        2. Check if task has already been processed (deduplication)
        3. Update chunk counters (completed_chunks++, active_chunks--)
        4. Calculate progress percentage
        5. If successful, create image records using bulk_create()
        6. If failed, increment failed_chunks
        7. Mark task as processed to prevent duplicate processing
        8. If all chunks complete, mark job as completed
        9. Create notification if job completed

        Deduplication:
        - Uses database transaction to ensure atomic updates
        - Checks current chunk counts before updating to detect duplicates
        - Prevents race conditions through transaction isolation

        Args:
            job_id: ID of the job
            task_id: ID of the completed task
            result: Task result dictionary containing:
                - success: Boolean indicating task success
                - downloaded: Number of images downloaded
                - images: List of image metadata dicts (if successful)
                - error: Error message (if failed)

        Raises:
            NotFoundError: If job not found
        """
        # Use a database transaction to ensure atomic updates
        # This prevents race conditions and duplicate processing
        async with self.crawl_job_repo.session.begin_nested():
            # Step 1: Retrieve job with row-level lock (SELECT FOR UPDATE)
            # This ensures no other transaction can modify the job until we're done
            from sqlalchemy import select
            from backend.models import CrawlJob

            stmt = select(CrawlJob).where(CrawlJob.id == job_id).with_for_update()
            result_obj = await self.crawl_job_repo.session.execute(stmt)
            job = result_obj.scalar_one_or_none()

            if not job:
                raise NotFoundError(f"Crawl job not found: {job_id}")

            # Step 2: Check for duplicate task result (deduplication)
            # If the sum of completed + failed chunks would exceed total_chunks,
            # this is likely a duplicate result
            current_processed = (job.completed_chunks or 0) + (job.failed_chunks or 0)
            total_chunks = job.total_chunks or 0

            if current_processed >= total_chunks and total_chunks > 0:
                logger.warning(
                    f"Task {task_id} for job {job_id} appears to be a duplicate. "
                    f"All chunks already processed ({current_processed}/{total_chunks}). "
                    f"Ignoring duplicate result (deduplication).",
                    job_id=job_id,
                    task_id=task_id,
                    current_processed=current_processed,
                    total_chunks=total_chunks
                )
                return  # Idempotent - ignore duplicate

            logger.info(
                f"Processing task completion for job {job_id}, task {task_id}",
                job_id=job_id,
                task_id=task_id,
                success=result.get('success', False)
            )

        # Step 2: Update chunk counters
        success = result.get('success', False)

        if success:
            # Increment completed_chunks, decrement active_chunks
            new_completed = (job.completed_chunks or 0) + 1
            new_active = max((job.active_chunks or 0) - 1, 0)
            new_failed = job.failed_chunks or 0
        else:
            # Increment failed_chunks, decrement active_chunks
            new_completed = job.completed_chunks or 0
            new_active = max((job.active_chunks or 0) - 1, 0)
            new_failed = (job.failed_chunks or 0) + 1

            # Log error
            error_msg = result.get('error', 'Unknown error')
            logger.error(
                f"Task {task_id} failed for job {job_id}: {error_msg}",
                job_id=job_id,
                task_id=task_id,
                error=error_msg
            )

        # Update chunk counts
        await self.crawl_job_repo.update_chunk_counts(
            job_id=job_id,
            active_chunks=new_active,
            completed_chunks=new_completed,
            failed_chunks=new_failed
        )

        # Step 3: Calculate progress percentage
        total_chunks = job.total_chunks or 1
        progress = int(((new_completed + new_failed) / total_chunks) * 100)
        progress = min(progress, 100)

        # Step 4: Create image records if successful
        if success and 'images' in result:
            images_data = result['images']
            if images_data:
                try:
                    # Add job_id to each image
                    for img_data in images_data:
                        img_data['crawl_job_id'] = job_id

                    await self.image_repo.bulk_create(images_data)

                    # Update downloaded_images count
                    downloaded_count = result.get('downloaded', len(images_data))
                    new_downloaded = (job.downloaded_images or 0) + downloaded_count

                    await self.crawl_job_repo.update_progress(
                        job_id=job_id,
                        progress=progress,
                        downloaded_images=new_downloaded
                    )

                    logger.info(
                        f"Created {len(images_data)} image records for job {job_id}",
                        job_id=job_id,
                        image_count=len(images_data)
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to create image records for job {job_id}: {str(e)}",
                        job_id=job_id,
                        error=str(e)
                    )
        else:
            # Just update progress
            await self.crawl_job_repo.update_progress(
                job_id=job_id,
                progress=progress,
                downloaded_images=job.downloaded_images or 0
            )

        # Step 6: Check if all chunks are complete
        all_chunks_done = (new_completed + new_failed) >= total_chunks

        if all_chunks_done:
            # Mark job as completed
            await self.crawl_job_repo.mark_completed(job_id)

            logger.info(
                f"Job {job_id} completed: {new_completed} successful, {new_failed} failed",
                job_id=job_id,
                completed_chunks=new_completed,
                failed_chunks=new_failed
            )

            # Step 7: Create completion notification
            try:
                from backend.repositories import NotificationRepository
                from backend.models import Notification

                # Get project to find user_id (through dataset)
                dataset = await self.dataset_repo.get_by_id(job.dataset_id)
                if dataset:
                    project = await self.project_repo.get_by_id(dataset.project_id)
                if dataset and project:
                    notification_repo = NotificationRepository(self.crawl_job_repo.session)
                    await notification_repo.create(
                        user_id=project.user_id,
                        type='job_completed',
                        category='crawl_jobs',
                        title='Crawl Job Completed',
                        message=f'Job "{job.name}" has completed with {new_completed} successful chunks and {new_failed} failed chunks.',
                        metadata_={
                            'job_id': job_id,
                            'completed_chunks': new_completed,
                            'failed_chunks': new_failed,
                            'total_chunks': total_chunks
                        }
                    )

                    logger.info(
                        f"Created completion notification for job {job_id}",
                        job_id=job_id
                    )
            except Exception as e:
                # Log but don't fail if notification creation fails
                logger.error(
                    f"Failed to create completion notification for job {job_id}: {str(e)}",
                    job_id=job_id,
                    error=str(e)
                )

    async def update_job_progress(
        self,
        job_id: int,
        progress: int,
        downloaded_images: int,
        valid_images: Optional[int] = None
    ) -> Optional[CrawlJob]:
        """
        Update crawl job progress and broadcast via SSE.

        Args:
            job_id: Crawl job ID
            progress: Progress percentage (0-100)
            downloaded_images: Number of images downloaded
            valid_images: Number of valid images

        Returns:
            Updated job or None if not found
        """
        # Ensure progress is within bounds
        progress = max(0, min(100, progress))

        updates = {
            'progress': progress,
            'downloaded_images': downloaded_images,
            'last_activity': datetime.utcnow(),
            'status': 'in_progress' if progress < 100 else 'completed'
        }

        if valid_images is not None:
            updates['valid_images'] = valid_images

        job = await self.crawl_job_repo.get_by_id(job_id)
        if job:
            job = await self.crawl_job_repo.update(job, **updates)

        if job:
            # Broadcast progress update via Supabase
            supabase = get_supabase_client()
            if supabase:
                channel = supabase.channel(f'crawl_job_{job_id}')
                update_data = {
                    'job_id': job_id,
                    'progress': progress,
                    'downloaded_images': downloaded_images,
                    'valid_images': valid_images or 0,
                    'total_images': job.max_images,
                    'status': job.status,
                    'timestamp': datetime.utcnow().isoformat()
                }

                await channel.send({
                    'type': 'broadcast',
                    'event': 'progress',
                    'payload': update_data
                })

                # Also update the job status in the database for real-time subscriptions
                if progress >= 100:
                    await self.update_job_status(
                        job_id=job_id,
                        status='completed'
                    )

        return job

    async def get_jobs_by_dataset(self, dataset_id: int) -> List[CrawlJob]:
        """
        Get all jobs for a dataset.

        Args:
            dataset_id: Dataset ID

        Returns:
            List of crawl jobs
        """
        return await self.crawl_job_repo.get_by_dataset(dataset_id)

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
            format_=image_data.get("format_")
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

    async def update_job_status(
        self,
        job_id: int,
        status: str,
        error: Optional[str] = None,
        **updates: Any
    ) -> Optional[CrawlJob]:
        """
        Update crawl job status and metadata with real-time updates.

        Args:
            job_id: Crawl job ID
            status: New status
            error: Optional error message
            **updates: Additional fields to update

        Returns:
            Updated job or None if not found
        """
        updates['status'] = status
        if error:
            updates['error'] = error
            updates['completed_at'] = datetime.utcnow()
        elif status == 'completed':
            updates['completed_at'] = datetime.utcnow()
            updates['progress'] = 100

        job = await self.crawl_job_repo.get_by_id(job_id)
        if not job:
            return None

        # Store values before updating (to avoid lazy loading issues)
        dataset_id = job.dataset_id
        original_progress = job.progress or 0
        original_downloaded = job.downloaded_images or 0
        original_valid = job.valid_images or 0
        max_images = job.max_images
        
        # Update the job
        job = await self.crawl_job_repo.update(job, **updates)

        # Log activity using the stored dataset_id
        if dataset_id:
            dataset = await self.dataset_repo.get_by_id(dataset_id)
            if dataset:
                await self._log_activity(
                    dataset.project_id,
                    f"Job {job_id} status updated to: {status}",
                    job_id=job_id,
                    status=status,
                    **{k: v for k, v in updates.items() if k != 'status'}
                )

        # Broadcast status change via Supabase
        supabase = get_supabase_client()
        if supabase:
            channel = supabase.channel(f'crawl_job_{job_id}')
            update_data = {
                'job_id': job_id,
                'status': status,
                'progress': updates.get('progress', original_progress),
                'downloaded_images': updates.get('downloaded_images', original_downloaded),
                'valid_images': updates.get('valid_images', original_valid),
                'total_images': max_images,
                'timestamp': datetime.utcnow().isoformat()
            }

            if error:
                update_data['error'] = error

            await channel.send({
                'type': 'broadcast',
                'event': 'status_update',
                'payload': update_data
            })

        return job

    # Alias for backward compatibility
    update_job = update_job_status

    async def get_job_progress_stream(self, job_id: int) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Get a stream of job progress updates.

        Args:
            job_id: Crawl job ID

        Yields:
            Job progress updates as a dictionary with the following keys:
            - job_id: ID of the crawl job
            - progress: Current progress percentage (0-100)
            - downloaded_images: Number of images downloaded so far
            - valid_images: Number of valid images
            - total_images: Total number of images to download
            - status: Current job status
            - timestamp: ISO timestamp of the update
        """
        # Get current job state first
        job = await self.get_job(job_id)
        if not job:
            raise NotFoundError(f"Crawl job not found: {job_id}")

        # Yield initial state
        initial_state = {
            'job_id': job_id,
            'progress': job.progress or 0,
            'downloaded_images': job.downloaded_images or 0,
            'valid_images': job.valid_images or 0,
            'total_images': job.max_images,
            'status': job.status,
            'timestamp': datetime.utcnow().isoformat()
        }
        yield initial_state

        # If job is already completed, no need to subscribe to updates
        if job.status in ['completed', 'failed', 'cancelled']:
            return

        # Subscribe to real-time updates
        supabase = get_supabase_client()
        if not supabase:
            return

        channel = supabase.channel(f'crawl_job_{job_id}')

        try:
            # Subscribe to the channel
            subscription = await channel.subscribe()

            # Track last update time to detect stale connections
            last_update = time.time()

            # Listen for messages
            while True:
                try:
                    message = await asyncio.wait_for(subscription.receive(), timeout=30.0)
                    last_update = time.time()

                    if message and message.get('type') == 'broadcast':
                        event = message.get('event')
                        if event in ['progress', 'status_update']:
                            if isinstance(message.get('payload'), dict):
                                yield message['payload']
                            else:
                                # Handle string payload for backward compatibility
                                try:
                                    payload = json.loads(message['payload'])
                                    yield payload
                                except (json.JSONDecodeError, TypeError):
                                    yield {'error': 'Invalid message format_'}

                    # If job is completed, stop the stream
                    if message and message.get('payload', {}).get('status') in ['completed', 'failed', 'cancelled']:
                        break

                except asyncio.TimeoutError:
                    # Send a heartbeat to keep the connection alive
                    if time.time() - last_update > 30:
                        yield {
                            'job_id': job_id,
                            'event': 'heartbeat',
                            'timestamp': datetime.utcnow().isoformat()
                        }

                # Small sleep to prevent busy waiting
                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            # Clean up on cancellation
            await channel.unsubscribe()
            raise
        except Exception as e:
            logger.error(f"Error in job progress stream: {str(e)}")
            yield {
                'job_id': job_id,
                'error': str(e),
                'status': 'error',
                'timestamp': datetime.utcnow().isoformat()
            }
        finally:
            # Ensure we always clean up
            if 'channel' in locals():
                await channel.unsubscribe()

    async def get_job_progress_sse(self, job_id: int) -> EventSourceResponse:
        """
        Get a Server-Sent Events (SSE) stream of job progress updates.

        Args:
            job_id: Crawl job ID

        Returns:
            An EventSourceResponse object
        """
        async def event_generator():
            try:
                # Keep the connection alive with a heartbeat
                last_activity = time.time()

                async for update in self.get_job_progress_stream(job_id):
                    # Send a heartbeat every 30 seconds if no updates
                    if time.time() - last_activity > 30:
                        yield {
                            'event': 'heartbeat',
                            'data': json.dumps({'timestamp': datetime.utcnow().isoformat()})
                        }

                    # Send the actual progress update
                    yield {
                        'event': 'crawl_progress',
                        'data': json.dumps(update),
                        'retry': 3000  # 3 second retry delay for reconnections
                    }
                    last_activity = time.time()

            except asyncio.CancelledError:
                # Handle client disconnection
                pass
            except Exception as e:
                # Log any errors that occur during streaming
                logger.error(f"Error in SSE stream for job {job_id}: {str(e)}")
                yield {
                    'event': 'error',
                    'data': json.dumps({
                        'error': 'An error occurred while streaming progress',
                        'timestamp': datetime.utcnow().isoformat()
                    })
                }

        # Create the SSE response with appropriate headers
        return EventSourceResponse(
            event_generator(),
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'  # Disable buffering for Nginx
            }
        )

    async def cancel_job(
        self,
        job_id: int,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cancel a running or pending crawl job with idempotency.

        This method performs a complete cancellation workflow:
        1. Validates job exists and can be cancelled
        2. Revokes all associated Celery tasks
        3. Cleans up temporary storage
        4. Updates job status to 'cancelled'
        5. Logs cancellation activity
        6. Broadcasts cancellation via real-time updates

        Idempotency:
        - If job is already cancelled/completed/failed, returns success without side effects
        - Only pending or running jobs trigger actual cancellation workflow

        Args:
            job_id: Crawl job ID to cancel
            user_id: Optional user ID for activity logging

        Returns:
            Dictionary containing:
                - job_id: Job ID
                - status: Job status (should be 'cancelled')
                - revoked_tasks: Number of tasks revoked
                - message: Success message

        Raises:
            NotFoundError: If job doesn't exist
            ValidationError: If job status doesn't allow cancellation
        """
        from backend.core.exceptions import ValidationError

        # Get the job
        job = await self.get_job(job_id)
        if not job:
            raise NotFoundError(f"Crawl job not found: {job_id}")

        # Idempotency: If job is already in a terminal state, return success without side effects
        if job.status in ['cancelled', 'completed', 'failed']:
            logger.info(
                f"Job {job_id} is already in terminal state '{job.status}'. "
                f"Returning success (idempotent).",
                job_id=job_id,
                status=job.status
            )
            return {
                "job_id": job_id,
                "status": job.status,
                "revoked_tasks": 0,
                "message": f"Job is already {job.status} (idempotent response)"
            }

        # Validate job status - only pending or running jobs can be cancelled
        if job.status not in ['pending', 'running', 'in_progress']:
            raise ValidationError(
                f"Cannot cancel job with status '{job.status}'. "
                f"Only pending or running jobs can be cancelled."
            )

        logger.info(f"Cancelling job {job_id} with status '{job.status}'")

        # Step 1: Revoke Celery tasks and count them
        revoked_count = 0
        if job.task_ids and isinstance(job.task_ids, list) and len(job.task_ids) > 0:
            await self._revoke_celery_tasks(job.task_ids, terminate=True)
            revoked_count = len(job.task_ids)
            logger.info(f"Revoked {revoked_count} Celery tasks for job {job_id}")
        else:
            logger.info(f"No Celery tasks to revoke for job {job_id}")

        # Step 2: Clean up temporary storage
        try:
            await self._cleanup_job_storage(job_id)
            logger.info(f"Cleaned up storage for job {job_id}")
        except Exception as e:
            # Log but don't fail cancellation if storage cleanup fails
            logger.error(f"Failed to cleanup storage for job {job_id}: {str(e)}")

        # Step 3: Update job status to cancelled
        updated_job = await self.update_job_status(
            job_id=job_id,
            status='cancelled',
            completed_at=datetime.utcnow()
        )

        # Step 4: Log cancellation activity
        if user_id:
            await self.activity_log_repo.create(
                user_id=uuid.UUID(user_id),
                action="CANCEL_CRAWL_JOB",
                resource_type="crawl_job",
                resource_id=str(job_id),
                metadata={
                    "reason": "User requested cancellation",
                    "revoked_tasks": revoked_count
                }
            )

        return {
            "job_id": job_id,
            "status": updated_job.status,
            "revoked_tasks": revoked_count,
            "message": f"Job cancelled successfully. {revoked_count} task(s) revoked."
        }

    async def apply_retention_policy(self) -> Dict[str, int]:
        """
        Apply data retention policies based on user tiers.

        Policies:
        - Free: Archive after 7 days
        - Hobby: Move to cold storage after 30 days
        - Pro: Keep hot indefinitely
        """
        from datetime import timedelta

        results = {
            'archived': 0,
            'cold_storage': 0,
            'errors': 0
        }

        try:
            # Get all completed jobs
            completed_jobs = await self.crawl_job_repo.get_by_status('completed')

            now = datetime.utcnow()

            for job in completed_jobs:
                if not job.completed_at:
                    continue

                # Calculate age
                age = now - job.completed_at

                # Get user tier
                # Note: We assume job.project.user is available via lazy='joined'
                user_id = job.project.user_id if job.project else None
                if not user_id:
                    continue

                tier = await self._get_user_tier(user_id)

                if tier == 'free':
                    if age > timedelta(days=7):
                        await self.update_job_status(job.id, 'archived')
                        results['archived'] += 1
                elif tier == 'hobby':
                    if age > timedelta(days=30):
                        await self.update_job_status(job.id, 'cold_storage')
                        results['cold_storage'] += 1
                # Pro: do nothing

        except Exception as e:
            logger.error(f"Error applying retention policy: {str(e)}")
            results['errors'] += 1

        return results

    async def _get_user_tier(self, user_id: Union[uuid.UUID, str]) -> str:
        """
        Determine user's subscription tier based on credit account limits.

        Uses CreditAccount.monthly_limit to infer tier:
        - < 2000: Free
        - 2000 - 500,000: Hobby
        - > 500,000: Pro

        Args:
            user_id: User UUID

        Returns:
            Tier name ('free', 'hobby', 'pro')
        """
        from sqlalchemy import select
        from backend.models import CreditAccount

        try:
            # Query credit account for user
            query = select(CreditAccount).where(CreditAccount.user_id == user_id)
            result = await self.crawl_job_repo.session.execute(query)
            account = result.scalar_one_or_none()

            if not account:
                return 'free'

            limit = account.monthly_limit

            if limit > 500000:
                return 'pro'
            elif limit > 2000:
                return 'hobby'
            else:
                return 'free'

        except Exception as e:
            logger.error(f"Error determining user tier for {user_id}: {str(e)}")
            return 'free'


        # Step 5: Broadcast cancellation via Supabase real-time
        supabase = get_supabase_client()
        if supabase:
            channel = supabase.channel(f'crawl_job_{job_id}')
            await channel.send({
                'type': 'broadcast',
                'event': 'job_cancelled',
                'payload': {
                    'job_id': job_id,
                    'status': 'cancelled',
                    'timestamp': datetime.utcnow().isoformat(),
                    'message': 'Job has been cancelled by user'
                }
            })

        self.log_operation("cancel_crawl_job", job_id=job_id, status='cancelled')
        logger.info(f"Successfully cancelled job {job_id}")

        return updated_job

    async def _log_activity(
        self,
        project_id: int,
        action: str,
        user_id: Optional[str] = None,
        **metadata: Any
    ) -> None:
        """
        Log activity for crawl job operations.

        Args:
            project_id: Project ID
            action: Action description
            user_id: Optional user ID
            **metadata: Additional metadata
        """
        try:
            # If user_id is not provided, try to get owner from project
            if not user_id:
                project = await self.project_repo.get_by_id(project_id)
                if project:
                    user_id = str(project.user_id)

            if user_id:
                await self.activity_log_repo.create(
                    user_id=uuid.UUID(user_id),
                    action=action,
                    resource_type="crawl_job",
                    metadata=metadata
                )
        except Exception as e:
            logger.error(f"Failed to log activity: {str(e)}")

    async def list_jobs(self, user_id: str, dataset_id: int) -> Any:
        """
        List all crawl jobs for a specific dataset.

        Args:
            user_id: User ID for ownership verification
            dataset_id: Dataset ID to retrieve jobs for

        Returns:
            Paginated list of crawl jobs
        """
        from fastapi_pagination.ext.sqlalchemy import paginate
        from sqlalchemy import select
        from backend.models import Project, Dataset

        # Build query for dataset's crawl jobs with ownership verification
        # Jobs belong to datasets, datasets belong to projects, projects belong to users
        query = (
            select(CrawlJob)
            .join(Dataset, Dataset.id == CrawlJob.dataset_id)
            .join(Project, Project.id == Dataset.project_id)
            .where(CrawlJob.dataset_id == dataset_id)
            .where(Project.user_id == user_id)
            .order_by(CrawlJob.created_at.desc())
        )

        # Use fastapi-pagination's paginate function
        return await paginate(self.crawl_job_repo.session, query)

    def to_response(self, job: CrawlJob):
        """
        Convert CrawlJob model to CrawlJobResponse schema.

        Args:
            job: CrawlJob model instance

        Returns:
            CrawlJobResponse schema
        """
        from backend.schemas.crawl_jobs import CrawlJobResponse

        return CrawlJobResponse(
            id=job.id,
            dataset_id=job.dataset_id,
            name=job.name,
            keywords=job.keywords,
            max_images=job.max_images,
            search_engine="duckduckgo",  # Default, not stored in DB
            status=job.status,
            progress=job.progress,
            total_images=job.total_images,
            downloaded_images=job.downloaded_images,
            valid_images=job.valid_images,
            config={},  # Default empty config
            created_at=job.created_at.isoformat(),
            updated_at=job.updated_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
        )

    async def get_job_with_ownership_check(
        self,
        job_id: int,
        user_id: str
    ) -> Optional[CrawlJob]:
        """
        Get crawl job by ID with ownership verification.

        Args:
            job_id: Crawl job ID
            user_id: User ID to verify ownership

        Returns:
            CrawlJob if found and owned by user, None otherwise

        Raises:
            NotFoundError: If job not found or access denied
        """
        from sqlalchemy import select
        from backend.models import Project

        job = await self.get_job(job_id)
        if not job:
            return None

        # Verify ownership via project (through dataset)
        from backend.models.dataset import Dataset
        owner_query = (
            select(Project.user_id)
            .join(Dataset, Dataset.project_id == Project.id)
            .where(Dataset.id == job.dataset_id)
        )
        owner_result = await self.crawl_job_repo.session.execute(owner_query)
        owner_id = owner_result.scalar_one_or_none()

        if str(owner_id) != str(user_id):
            return None

        return job

    async def retry_job(self, job_id: int, user_id: str) -> CrawlJob:
        """
        Retry a failed or cancelled crawl job with counter reset.

        This method resets all job counters and state to allow a fresh retry:
        - Resets status to 'pending'
        - Resets progress and image counters
        - Resets chunk counters (total, active, completed, failed)
        - Clears task IDs
        - Clears timestamps

        Args:
            job_id: Crawl job ID
            user_id: User ID for ownership verification

        Returns:
            Updated crawl job with reset progress and counters

        Raises:
            NotFoundError: If job not found or access denied
            ValidationError: If job status doesn't allow retry
        """
        # Verify ownership
        job = await self.get_job_with_ownership_check(job_id, user_id)
        if not job:
            raise NotFoundError(f"Crawl job {job_id} not found")

        # Validate status
        if job.status not in ["failed", "cancelled"]:
            raise ValidationError(
                f"Only failed or cancelled jobs can be retried (current: {job.status})"
            )

        # Reset job state including chunk counters (Requirement 11.4)
        job.status = "pending"
        job.progress = 0
        job.total_images = 0
        job.downloaded_images = 0
        job.valid_images = 0

        # Reset chunk counters to 0 before dispatching new tasks
        job.total_chunks = 0
        job.active_chunks = 0
        job.completed_chunks = 0
        job.failed_chunks = 0

        # Clear task IDs from previous attempt
        job.task_ids = []

        # Clear timestamps
        job.started_at = None
        job.completed_at = None

        await self.crawl_job_repo.session.commit()
        await self.crawl_job_repo.session.refresh(job)

        logger.info(
            f"Job {job_id} reset for retry by user {user_id}. "
            f"All counters and task IDs cleared.",
            job_id=job_id,
            user_id=user_id
        )

        return job

    async def get_job_logs(
        self,
        job_id: int,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get activity logs for a crawl job.

        Args:
            job_id: Crawl job ID
            user_id: User ID for ownership verification

        Returns:
            List of job log entries

        Raises:
            NotFoundError: If job not found or access denied
        """
        from sqlalchemy import select
        from backend.models import ActivityLog
        from backend.schemas.crawl_jobs import JobLogEntry

        # Verify ownership
        job = await self.get_job_with_ownership_check(job_id, user_id)
        if not job:
            raise NotFoundError(f"Crawl job {job_id} not found")

        # Query activity logs for this job
        logs_query = (
            select(ActivityLog)
            .where(
                ActivityLog.resource_type == "crawl_job",
                ActivityLog.resource_id == str(job_id),
            )
            .order_by(ActivityLog.timestamp.desc())
        )
        logs_result = await self.crawl_job_repo.session.execute(logs_query)
        logs = list(logs_result.scalars().all())

        return [
            JobLogEntry(
                action=log.action,
                timestamp=log.timestamp.isoformat(),
                metadata=log.metadata_,
            )
            for log in logs
        ]

    async def _get_user_tier(self, user_id: UUID) -> str:
        """
        Get user's subscription tier from credit account.

        Determines the user's tier based on their credit account balance.
        Used for rate limiting concurrent jobs.

        Args:
            user_id: User UUID

        Returns:
            Tier string: 'free', 'hobby', or 'pro'
        """
        from sqlalchemy import select
        from backend.models import CreditAccount

        try:
            # Query credit account
            query = select(CreditAccount).where(CreditAccount.user_id == user_id)
            result = await self.crawl_job_repo.session.execute(query)
            credit_account = result.scalar_one_or_none()

            if not credit_account:
                return 'free'  # Default to free tier if no account

            # Determine tier based on credit balance
            balance = credit_account.current_balance

            if balance >= 10000:
                return 'pro'
            elif balance >= 1000:
                return 'hobby'
            else:
                return 'free'

        except Exception as e:
            logger.warning(f"Failed to determine user tier for {user_id}: {str(e)}")
            return 'free'  # Default to free on error


    async def _revoke_celery_tasks(
        self,
        task_ids: List[str],
        terminate: bool = True
    ) -> None:
        """
        Revoke Celery tasks gracefully or forcefully.

        This method revokes all tasks in the provided list. With terminate=True,
        tasks are forcefully terminated. With terminate=False, tasks are allowed
        to finish their current work before stopping.

        Args:
            task_ids: List of Celery task IDs to revoke
            terminate: If True, forcefully terminate tasks. If False, allow
                      graceful shutdown (tasks finish current work)

        Note:
            - terminate=True: Sends SIGTERM to worker process (forceful)
            - terminate=False: Task won't accept new work but finishes current work
        """
        if not task_ids:
            return

        for task_id in task_ids:
            try:
                # Revoke the task
                # terminate=True: Forcefully kill the task (SIGTERM)
                # terminate=False: Graceful - task won't start if not started,
                #                  or will finish current work if already running
                celery_app.control.revoke(
                    task_id,
                    terminate=terminate,
                    signal='SIGTERM' if terminate else None
                )
                logger.debug(
                    f"Revoked Celery task {task_id} "
                    f"({'forceful' if terminate else 'graceful'})"
                )
            except Exception as e:
                # Log error but continue revoking other tasks
                logger.error(f"Failed to revoke Celery task {task_id}: {str(e)}")


    async def _cleanup_job_storage(self, job_id: int) -> None:
        """
        Clean up temporary storage files for a cancelled job.

        This method removes all files associated with the job from temporary
        storage. Files are identified by the path prefix pattern: job_{job_id}/

        Args:
            job_id: Job ID whose storage should be cleaned up

        Note:
            This method uses LocalStorageProvider to list and delete files.
            If storage cleanup fails, the error is logged but not raised to
            avoid blocking the cancellation process.
        """
        try:
            from backend.storage.factory import get_storage_provider

            # Get storage provider (defaults to local storage)
            storage = get_storage_provider()

            # List all files for this job using the prefix pattern
            prefix = f"job_{job_id}/"
            files = storage.list_files(prefix=prefix)

            if not files:
                logger.info(f"No storage files found for job {job_id}")
                return

            # Delete each file
            deleted_count = 0
            failed_count = 0

            for file_path in files:
                try:
                    storage.delete(file_path)
                    deleted_count += 1
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Failed to delete file {file_path}: {str(e)}")

            logger.info(
                f"Storage cleanup for job {job_id}: "
                f"{deleted_count} files deleted, {failed_count} failed"
            )

        except Exception as e:
            # Log error but don't raise - storage cleanup is best-effort
            logger.error(f"Error during storage cleanup for job {job_id}: {str(e)}")




async def execute_crawl_job(
    job_id: int,
    user_id: Optional[str] = None,
    tier: Optional[str] = None,
    job_service: Optional[CrawlJobService] = None
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

    Raises:
        NotFoundError: If job not found
        ExternalServiceError: If job execution fails after retries

    Note:
        The user_id and tier are stored in task kwargs so the RateLimiter
        can identify and count this user's active jobs across all workers.
    """
    import uuid
    from datetime import datetime
    from typing import Dict, Any, List
    from backend.core.exceptions import (
        NotFoundError, ExternalServiceError
    )
    from backend.database.connection import get_session_maker
    from builder import Builder
    from backend.core.async_helpers import run_sync, run_in_threadpool
    from backend.services.metrics import MetricsService
    from backend.repositories import (
        ProcessingMetricRepository,
        ResourceMetricRepository,
        QueueMetricRepository
    )

    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds
    BATCH_SIZE = 50

    # Create session maker for this background task
    session_maker = get_session_maker()

    def create_services_with_session(session):
        """Create fresh services with provided session."""
        from backend.repositories.dataset_repository import DatasetRepository
        
        job_service = CrawlJobService(
            crawl_job_repo=CrawlJobRepository(session),
            project_repo=ProjectRepository(session),
            image_repo=ImageRepository(session),
            activity_log_repo=ActivityLogRepository(session),
            dataset_repo=DatasetRepository(session)
        )
        
        metrics_service = MetricsService(
            processing_repo=ProcessingMetricRepository(session),
            resource_repo=ResourceMetricRepository(session),
            queue_repo=QueueMetricRepository(session)
        )
        
        return job_service, metrics_service

    try:
        # Initialize job and start processing
        async with session_maker() as session:
            async with session.begin():
                job_service, metrics_service = create_services_with_session(session)
                
                job = await job_service.get_job(job_id)
                if not job:
                    raise NotFoundError(f"Crawl job not found: {job_id}")

                # Simple update without accessing relationships
                job = await job_service.crawl_job_repo.get_by_id(job_id)
                if job:
                    await job_service.crawl_job_repo.update(job, 
                        status="running",
                        started_at=datetime.utcnow()
                    )

        # Start job metric with fresh session
        async with session_maker() as session:
            async with session.begin():
                _, metrics_service = create_services_with_session(session)
                job_metric = await metrics_service.start_processing_metric(
                    operation_type="full_job",
                    job_id=job_id,
                    user_id=uuid.UUID(user_id) if user_id else None
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
        total_chunks = max(1, job.max_images // 50)  # 50 images per chunk
        current_chunk = 0

        async def process_batch(batch: List[Dict[str, Any]]) -> None:
            nonlocal processed_count, valid_count, current_chunk
            if not batch:
                return

            # Use fresh session for batch processing
            async with session_maker() as batch_session:
                async with batch_session.begin():
                    batch_job_service, batch_metrics_service = create_services_with_session(batch_session)
                    
                    # Track batch metric
                    batch_metric = await batch_metrics_service.start_processing_metric(
                        operation_type="batch_processing",
                        job_id=job_id,
                        user_id=uuid.UUID(user_id) if user_id else None
                    )

                    try:
                        processed_count += len(batch)
                        valid_batch = [img for img in batch if img.get("is_valid", True)]
                        valid_count += len(valid_batch)
                        current_chunk = min(current_chunk + 1, total_chunks)

                        # Calculate overall progress (0-100)
                        if job.max_images > 0:
                            progress = min(
                                int((processed_count / job.max_images) * 100), 100)
                        else:
                            progress = 0

                        # Direct repository update to avoid session issues
                        job_to_update = await batch_job_service.crawl_job_repo.get_by_id(job_id)
                        if job_to_update:
                            await batch_job_service.crawl_job_repo.update(job_to_update,
                                progress=progress,
                                downloaded_images=processed_count,
                                valid_images=valid_count,
                                last_activity=datetime.utcnow()
                            )

                        if valid_batch:
                            await batch_job_service.store_bulk_images(job_id, valid_batch)

                        # Complete batch metric
                        await batch_metrics_service.complete_processing_metric(
                            metric_id=batch_metric.id,
                            status="completed",
                            images_processed=len(batch),
                            images_succeeded=len(valid_batch),
                            images_failed=len(batch) - len(valid_batch)
                        )

                        # Collect resource metrics periodically (every 5 chunks)
                        if current_chunk % 5 == 0:
                            await batch_metrics_service.collect_resource_metrics(job_id=job_id)

                    except Exception as e:
                        # Fail batch metric
                        await batch_metrics_service.complete_processing_metric(
                            metric_id=batch_metric.id,
                            status="failed",
                            error_message=str(e)
                        )
                        raise

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

                    # Send progress update after each batch with fresh session
                    progress = min(
                        int((processed_count / job.max_images) * 100), 100) if job.max_images > 0 else 0

                    async with session_maker() as progress_session:
                        async with progress_session.begin():
                            progress_job_service, _ = create_services_with_session(progress_session)
                            # Direct repository update to avoid session issues
                            job_to_update = await progress_job_service.crawl_job_repo.get_by_id(job_id)
                            if job_to_update:
                                await progress_job_service.crawl_job_repo.update(job_to_update,
                                    progress=progress,
                                    downloaded_images=processed_count,
                                    valid_images=valid_count,
                                    last_activity=datetime.utcnow()
                                )

                except StopAsyncIteration:
                    break

            # Final progress update with fresh session
            progress = 100 if processed_count >= job.max_images else min(
                int((processed_count / job.max_images) * 100), 99)
            
            async with session_maker() as final_session:
                async with final_session.begin():
                    final_job_service, _ = create_services_with_session(final_session)
                    # Direct repository update to avoid session issues
                    job_to_update = await final_job_service.crawl_job_repo.get_by_id(job_id)
                    if job_to_update:
                        await final_job_service.crawl_job_repo.update(job_to_update,
                            progress=progress,
                            downloaded_images=processed_count,
                            valid_images=valid_count,
                            last_activity=datetime.utcnow()
                        )

        except Exception as e:
            # Update job status to failed in case of errors with fresh session
            async with session_maker() as error_session:
                async with error_session.begin():
                    error_job_service, _ = create_services_with_session(error_session)
                    # Direct repository update to avoid session issues
                    job = await error_job_service.crawl_job_repo.get_by_id(job_id)
                    if job:
                        await error_job_service.crawl_job_repo.update(job,
                            status="failed",
                            error=str(e)
                        )
            raise ExternalServiceError(
                f"Error during batch processing: {str(e)}") from e
        finally:
            # Ensure resources are cleaned up
            try:
                await run_in_threadpool(builder.cleanup)
            except Exception as cleanup_error:
                logger.error(f"Error during cleanup: {str(cleanup_error)}")

        # Final update with completion status using fresh session
        async with session_maker() as completion_session:
            async with completion_session.begin():
                completion_job_service, completion_metrics_service = create_services_with_session(completion_session)
                
                # Direct repository update to avoid session issues
                job = await completion_job_service.crawl_job_repo.get_by_id(job_id)
                if job:
                    await completion_job_service.crawl_job_repo.update(job,
                        status="completed",
                        progress=100,
                        completed_at=datetime.utcnow(),
                        downloaded_images=processed_count,
                        valid_images=valid_count
                    )

                # Complete job metric
                await completion_metrics_service.complete_processing_metric(
                    metric_id=job_metric.id,
                    status="completed",
                    images_processed=processed_count,
                    images_succeeded=valid_count,
                    images_failed=processed_count - valid_count
                )

    except Exception as e:
        # Handle failure with fresh session
        try:
            async with session_maker() as failure_session:
                async with failure_session.begin():
                    failure_job_service, failure_metrics_service = create_services_with_session(failure_session)
                    
                    # Direct repository update to avoid session issues
                    job = await failure_job_service.crawl_job_repo.get_by_id(job_id)
                    if job:
                        await failure_job_service.crawl_job_repo.update(job,
                            status="failed",
                            error=str(e),
                            completed_at=datetime.utcnow(),
                            downloaded_images=processed_count if 'processed_count' in locals() else 0,
                            valid_images=valid_count if 'valid_count' in locals() else 0
                        )

                    # Complete job metric if it exists
                    if 'job_metric' in locals():
                        await failure_metrics_service.complete_processing_metric(
                            metric_id=job_metric.id,
                            status="failed",
                            error_message=str(e)
                        )
        except Exception as cleanup_error:
            logger.error(f"Error during failure cleanup: {cleanup_error}")

        raise ExternalServiceError(f"Job execution failed: {str(e)}") from e
