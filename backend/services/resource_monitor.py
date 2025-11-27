"""
Resource monitoring service for PixCrawler.

This module provides resource monitoring and capacity checking for
chunk orchestration without relying on psutil or runtime metrics.

Classes:
    ResourceMonitor: Monitor resources and check capacity

Features:
    - Database-based active chunk tracking
    - Configuration-based capacity limits
    - Environment-aware resource management
    - No psutil dependency (works on all platforms)
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple

from celery import Celery
from celery.schedules import crontab
from celery.signals import task_success, task_failure, task_revoked, worker_ready, beat_init
from sqlalchemy import select, func, desc, and_, or_, case, update
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import contextmanager
import asyncio
from datetime import datetime, timedelta

from backend.core.settings.resources import get_resource_settings, ResourceSettings
from backend.models import CrawlJob, User, UserTier
from utility.logging_config import get_logger

logger = get_logger(__name__)

__all__ = [
    'ResourceMonitor',
]


class PriorityScheduler:
    """
    Priority-based scheduler for crawl job chunks with Celery task execution.

    Manages a pool of 35 concurrent chunks with priority-based scheduling:
    - New users (first 24h): Priority 100
    - Enterprise: Priority 80
    - Pro: Priority 50
    - Free: Priority 30

    Features:
    - Strict 35-slot limit enforcement
    - Automatic recovery from failures
    - Comprehensive logging and monitoring
    - Periodic health checks
    - Task retry with exponential backoff
    """

    # Priority tiers with weights (higher = more important)
    PRIORITY_TIERS = {
        'new_user': 100,    # Highest priority for new users
        'enterprise': 80,   # Enterprise tier
        'pro': 50,          # Pro tier
        'free': 30          # Free tier (lowest priority)
    }

    # System constants
    MAX_CONCURRENT_CHUNKS = 35  # Strict limit on concurrent chunks
    MAX_RETRIES = 3             # Maximum number of retry attempts
    RETRY_DELAY = 60            # Initial retry delay in seconds
    LOCK_TIMEOUT = 300          # Lock timeout in seconds
    HEALTH_CHECK_INTERVAL = 30  # Health check interval in seconds

    def __init__(self, session: AsyncSession, celery_app: Optional[Celery] = None):
        """
        Initialize the priority scheduler.

        Args:
            session: Database session for job queries
            celery_app: Celery application instance (optional)
        """
        self.session = session
        self.celery = celery_app
        self.active_chunks: Dict[str, dict] = {}
        self._lock = asyncio.Lock()
        self._last_health_check = datetime.utcnow()
        self._setup_celery_signals()
        self._setup_periodic_tasks()

        logger.info(
            "PriorityScheduler initialized",
            max_concurrent_chunks=self.MAX_CONCURRENT_CHUNKS,
            priority_tiers=self.PRIORITY_TIERS
        )

    def _setup_celery_signals(self):
        """Setup Celery signal handlers for task lifecycle events."""
        task_success.connect(self._on_task_success, weak=False)
        task_failure.connect(self._on_task_failure, weak=False)
        task_revoked.connect(self._on_task_revoked, weak=False)
        worker_ready.connect(self._on_worker_ready, weak=False)

        # Add beat_init signal if Celery Beat is available
        if hasattr(worker_ready, 'connect'):
            beat_init.connect(self._on_beat_init, weak=False)

        logger.debug("Celery signal handlers registered")

    async def _get_user_priority(self, user_id: str) -> Tuple[int, str]:
        """Get priority score and tier name for a user.

        Args:
            user_id: User ID to get priority for

        Returns:
            Tuple of (priority_score, tier_name)
        """
        try:
            # Get user and their tier
            user = await self.session.get(User, user_id)
            if not user:
                return self.PRIORITY_TIERS['free'], 'free'

            # Check if user is new (first 24 hours)
            if datetime.utcnow() - user.created_at < timedelta(hours=24):
                return self.PRIORITY_TIERS['new_user'], 'new_user'

            # Return priority based on tier
            if user.tier == UserTier.ENTERPRISE:
                return self.PRIORITY_TIERS['enterprise'], 'enterprise'
            elif user.tier == UserTier.PRO:
                return self.PRIORITY_TIERS['pro'], 'pro'

            return self.PRIORITY_TIERS['free'], 'free'

        except Exception as e:
            logger.error(f"Error getting user priority: {e}", exc_info=True)
            return self.PRIORITY_TIERS['free'], 'error'

    def get_available_slots(self) -> int:
        """Get number of available slots in the pool.

        Returns:
            Number of available slots (0 to MAX_CONCURRENT_CHUNKS)
        """
        return max(0, self.MAX_CONCURRENT_CHUNKS - len(self.active_chunks))

    async def _execute_chunk_task(self, chunk_id: str) -> bool:
        """Execute a chunk processing task.

        Args:
            chunk_id: ID of the chunk to process

        Returns:
            bool: True if task was successfully started, False otherwise
        """
        try:
            if not self.celery:
                logger.error("Celery app not initialized")
                return False

            # Import task here to avoid circular imports
            from backend.tasks.process_chunk import process_chunk_task

            # Start the Celery task
            task = process_chunk_task.delay(chunk_id)

            logger.info(
                "Started processing chunk",
                chunk_id=chunk_id,
                task_id=task.id
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to start chunk processing task",
                chunk_id=chunk_id,
                error=str(e),
                exc_info=True
            )
            return False

    async def get_next_chunk(self) -> Optional[dict]:
        """Get and start processing the next chunk based on priority.

        Returns:
            Dictionary with chunk info if started, None if no chunks available
        """
        async with self._lock:
            try:
                # Check if we have available slots
                if len(self.active_chunks) >= self.MAX_CONCURRENT_CHUNKS:
                    logger.debug("Max concurrent chunks reached, waiting...")
                    return None

                # Get the next chunk based on priority
                query = (
                    select(CrawlJob, User)
                    .join(User, CrawlJob.user_id == User.id)
                    .where(
                        and_(
                            CrawlJob.status == 'pending',
                            or_(
                                CrawlJob.retry_count.is_(None),
                                CrawlJob.retry_count < self.MAX_RETRIES
                            ),
                            or_(
                                CrawlJob.scheduled_after.is_(None),
                                CrawlJob.scheduled_after <= datetime.utcnow()
                            )
                        )
                    )
                    .order_by(
                        # Primary sort by priority tier
                        desc(case(
                            (and_(
                                datetime.utcnow() - User.created_at < timedelta(hours=24),
                                True
                            ), self.PRIORITY_TIERS['new_user']),
                            (User.tier == UserTier.ENTERPRISE,
                             self.PRIORITY_TIERS['enterprise']),
                            (User.tier == UserTier.PRO,
                             self.PRIORITY_TIERS['pro']),
                            else_=self.PRIORITY_TIERS['free']
                        )),
                        # Secondary sort by creation time (FIFO within priority)
                        CrawlJob.created_at.asc()
                    )
                    .limit(1)
                    .with_for_update(skip_locked=True)
                )

                result = await self.session.execute(query)
                row = result.first()

                if not row:
                    logger.debug("No pending chunks available")
                    return None

                chunk, user = row
                chunk_id = str(chunk.id)

                # Get user priority and tier
                priority, tier = await self._get_user_priority(user.id)

                # Update chunk status
                chunk.status = 'processing'
                chunk.started_at = datetime.utcnow()
                chunk.priority = priority
                chunk.retry_count = (chunk.retry_count or 0) + 1

                # Generate a unique task ID
                task_id = f"chunk_{chunk_id}_{int(datetime.utcnow().timestamp())}"

                # Track active chunk
                self.active_chunks[task_id] = {
                    'chunk_id': chunk_id,
                    'job_id': chunk.job_id,
                    'user_id': user.id,
                    'priority': priority,
                    'tier': tier,
                    'started_at': datetime.utcnow(),
                    'retry_count': chunk.retry_count
                }

                await self.session.commit()

                # Start processing the chunk asynchronously
                task_started = await self._execute_chunk_task(chunk_id)
                if not task_started:
                    raise Exception("Failed to start chunk processing task")

                logger.info(
                    "Started processing chunk",
                    chunk_id=chunk_id,
                    job_id=chunk.job_id,
                    user_id=user.id,
                    priority=priority,
                    tier=tier,
                    task_id=task_id,
                    active_chunks=len(self.active_chunks)
                )

                return self.active_chunks[task_id]

            except Exception as e:
                logger.error(
                    "Error getting next chunk",
                    error=str(e),
                    exc_info=True
                )
                await self.session.rollback()

                # If we have a chunk but failed to process it, mark it as failed
                if 'chunk' in locals():
                    try:
                        chunk.status = 'failed'
                        chunk.ended_at = datetime.utcnow()
                        chunk.error_message = f"Failed to start processing: {str(e)}"
                        await self.session.commit()
                    except Exception as inner_e:
                        logger.error(
                            "Failed to update failed chunk status",
                            error=str(inner_e),
                            chunk_id=chunk_id if 'chunk_id' in locals() else None
                        )

                return None

    async def _on_task_success(self, sender=None, **kwargs):
        """Handle successful task completion.

        Args:
            sender: The task that sent the signal
            **kwargs: Additional task metadata
        """
        task_id = kwargs.get('task_id')
        if not task_id or task_id not in self.active_chunks:
            return

        chunk_info = self.active_chunks.pop(task_id, {})
        chunk_id = chunk_info.get('chunk_id')

        try:
            # Update chunk status in database
            if chunk_id:
                result = await self.session.execute(
                    update(CrawlJob)
                    .where(CrawlJob.id == chunk_id)
                    .values(
                        status='completed',
                        ended_at=datetime.utcnow(),
                        error_message=None
                    )
                )
                await self.session.commit()

                logger.info(
                    "Chunk processing completed",
                    chunk_id=chunk_id,
                    task_id=task_id,
                    job_id=chunk_info.get('job_id'),
                    duration=(datetime.utcnow(
                    ) - chunk_info.get('started_at', datetime.utcnow())).total_seconds(),
                    active_chunks=len(self.active_chunks)
                )
        except Exception as e:
            logger.error(
                "Failed to update completed chunk status",
                chunk_id=chunk_id,
                error=str(e),
                exc_info=True
            )
            await self.session.rollback()
        finally:
            # Always try to schedule the next chunk
            await self._schedule_next_chunk()

    async def _on_task_failure(self, sender=None, task_id=None, **kwargs):
        """Handle task failure with retry logic and error handling.

        Args:
            sender: The task that sent the signal
            task_id: ID of the failed task
            **kwargs: Additional task metadata including exception
        """
        if not task_id or task_id not in self.active_chunks:
            return

        chunk_info = self.active_chunks.pop(task_id, {})
        chunk_id = chunk_info.get('chunk_id')
        retry_count = chunk_info.get('retry_count', 0)

        try:
            if not chunk_id:
                logger.error("No chunk ID in task info", task_id=task_id)
                return

            exception = kwargs.get('exception')
            error_message = str(exception) if exception else 'Unknown error'

            # Calculate next retry time with exponential backoff
            next_retry = None
            if retry_count < self.MAX_RETRIES:
                backoff = min(self.RETRY_DELAY *
                              (2 ** retry_count), 3600)  # Max 1 hour
                next_retry = datetime.utcnow() + timedelta(seconds=backoff)
                status = 'pending'
                logger.warning(
                    "Chunk processing failed, will retry",
                    chunk_id=chunk_id,
                    task_id=task_id,
                    attempt=f"{retry_count + 1}/{self.MAX_RETRIES}",
                    next_retry=next_retry.isoformat(),
                    error=error_message
                )
            else:
                status = 'failed'
                logger.error(
                    "Chunk processing failed after max retries",
                    chunk_id=chunk_id,
                    task_id=task_id,
                    attempts=retry_count,
                    error=error_message
                )

            # Update chunk status in database
            await self.session.execute(
                update(CrawlJob)
                .where(CrawlJob.id == chunk_id)
                .values(
                    status=status,
                    # Truncate long error messages
                    error_message=error_message[:1000],
                    scheduled_after=next_retry,
                    retry_count=retry_count + 1 if status == 'pending' else retry_count,
                    ended_at=datetime.utcnow() if status == 'failed' else None
                )
            )
            await self.session.commit()

        except Exception as e:
            logger.error(
                "Error handling failed task",
                task_id=task_id,
                chunk_id=chunk_id,
                error=str(e),
                exc_info=True
            )
            await self.session.rollback()
        finally:
            # Always try to schedule the next chunk
            await self._schedule_next_chunk()

    async def _on_task_revoked(self, sender=None, task_id=None, **kwargs):
        """Handle task revocation with proper cleanup and rescheduling.

        Args:
            sender: The task that sent the signal
            task_id: ID of the revoked task
            **kwargs: Additional task metadata
        """
        if not task_id or task_id not in self.active_chunks:
            return

        chunk_info = self.active_chunks.pop(task_id, {})
        chunk_id = chunk_info.get('chunk_id')

        try:
            if not chunk_id:
                logger.error("No chunk ID in task info", task_id=task_id)
                return

            reason = kwargs.get('reason', 'Unknown reason')
            logger.warning(
                "Task was revoked",
                task_id=task_id,
                chunk_id=chunk_id,
                reason=reason,
                active_chunks=len(self.active_chunks)
            )

            # Only reschedule if we're under max retries
            retry_count = chunk_info.get('retry_count', 0)
            if retry_count < self.MAX_RETRIES:
                # Calculate next retry time with exponential backoff
                backoff = min(self.RETRY_DELAY *
                              (2 ** retry_count), 3600)  # Max 1 hour
                next_retry = datetime.utcnow() + timedelta(seconds=backoff)

                await self.session.execute(
                    update(CrawlJob)
                    .where(CrawlJob.id == chunk_id)
                    .values(
                        status='pending',
                        scheduled_after=next_retry,
                        retry_count=retry_count + 1,
                        error_message=f"Task was revoked: {reason}"
                    )
                )
                await self.session.commit()

                logger.info(
                    "Chunk rescheduled after revocation",
                    chunk_id=chunk_id,
                    next_retry=next_retry.isoformat(),
                    attempt=f"{retry_count + 1}/{self.MAX_RETRIES}"
                )
            else:
                # Mark as failed if max retries reached
                await self.session.execute(
                    update(CrawlJob)
                    .where(CrawlJob.id == chunk_id)
                    .values(
                        status='failed',
                        ended_at=datetime.utcnow(),
                        error_message=f"Task was revoked after {retry_count} attempts: {reason}"
                    )
                )
                await self.session.commit()

        except Exception as e:
            logger.error(
                "Error handling revoked task",
                task_id=task_id,
                chunk_id=chunk_id,
                error=str(e),
                exc_info=True
            )
            await self.session.rollback()
        finally:
            # Always try to schedule the next chunk
            await self._schedule_next_chunk()

    def _setup_periodic_tasks(self):
        """Setup periodic tasks for health checks and maintenance."""
        if not self.celery:
            return

        @self.celery.on_after_configure.connect
        def setup_periodic_tasks(sender, **kwargs):
            # Health check every 30 seconds
            sender.add_periodic_task(
                self.HEALTH_CHECK_INTERVAL,
                self._health_check.s(),
                name='scheduler-health-check'
            )

            # Cleanup stale tasks every 5 minutes
            sender.add_periodic_task(
                300,  # 5 minutes
                self._cleanup_stale_tasks.s(),
                name='cleanup-stale-tasks'
            )

    async def _on_beat_init(self, **kwargs):
        """Initialize Celery Beat scheduler."""
        logger.info("Celery Beat scheduler initialized")
        await self._health_check()

    async def _health_check(self):
        """Periodic health check and chunk scheduling."""
        try:
            now = datetime.utcnow()

            # Log health status
            logger.info(
                "Scheduler health check",
                active_chunks=len(self.active_chunks),
                max_concurrent=self.MAX_CONCURRENT_CHUNKS,
                time_since_last_check=(
                    now - self._last_health_check).total_seconds(),
                timestamp=now.isoformat()
            )

            # Try to fill available slots
            await self._schedule_next_chunk()

            self._last_health_check = now
            return True

        except Exception as e:
            logger.error("Health check failed", error=str(e), exc_info=True)
            return False

    async def _cleanup_stale_tasks(self):
        """Clean up stale or orphaned tasks."""
        try:
            # Find tasks that have been running too long (more than 1 hour)
            stale_threshold = datetime.utcnow() - timedelta(hours=1)
            stale_tasks = [
                task_id for task_id, info in self.active_chunks.items()
                if info.get('started_at', datetime.utcnow()) < stale_threshold
            ]

            if stale_tasks:
                logger.warning(
                    f"Found {len(stale_tasks)} stale tasks, cleaning up",
                    stale_tasks=stale_tasks
                )

                for task_id in stale_tasks:
                    if task_id in self.active_chunks:
                        chunk_info = self.active_chunks.pop(task_id)
                        chunk_id = chunk_info.get('chunk_id')

                        # Mark as failed in database
                        if chunk_id:
                            await self.session.execute(
                                update(CrawlJob)
                                .where(CrawlJob.id == chunk_id)
                                .values(
                                    status='failed',
                                    ended_at=datetime.utcnow(),
                                    error_message='Task timed out (stale)'
                                )
                            )

                await self.session.commit()

                # Try to schedule new chunks to replace the failed ones
                await self._schedule_next_chunk()

            return len(stale_tasks)

        except Exception as e:
            logger.error("Failed to clean up stale tasks",
                         error=str(e), exc_info=True)
            return 0

    def get_active_chunks_count(self) -> int:
        """Get current number of active chunks.

        Returns:
            Number of currently active chunks
        """
        return len(self.active_chunks)

    def get_active_chunks_info(self) -> List[dict]:
        """Get detailed information about active chunks.

        Returns:
            List of dictionaries with chunk information
        """
        now = datetime.utcnow()
        return [
            {
                **info,
                'duration_seconds': (now - info.get('started_at', now)).total_seconds(),
                'is_stale': (
                    now - info.get('started_at', now) > timedelta(hours=1)
                ) if 'started_at' in info else False
            }
            for info in self.active_chunks.values()
        ]

    def get_status(self) -> dict:
        """Get current scheduler status.

        Returns:
            Dictionary with scheduler status information
        """
        active_chunks = self.get_active_chunks_info()
        now = datetime.utcnow()

        # Calculate statistics
        by_priority = {}
        for tier, priority in self.PRIORITY_TIERS.items():
            count = sum(1 for c in active_chunks if c.get(
                'priority') == priority)
            if count > 0:
                by_priority[tier] = count

        return {
            'active_chunks': len(active_chunks),
            'max_concurrent': self.MAX_CONCURRENT_CHUNKS,
            'available_slots': self.get_available_slots(),
            'utilization': (len(active_chunks) / self.MAX_CONCURRENT_CHUNKS) * 100,
            'by_priority': by_priority,
            'last_health_check': self._last_health_check.isoformat(),
            'uptime_seconds': (now - self._last_health_check).total_seconds(),
            'settings': {
                'max_retries': self.MAX_RETRIES,
                'retry_delay': self.RETRY_DELAY,
                'health_check_interval': self.HEALTH_CHECK_INTERVAL,
                'lock_timeout': self.LOCK_TIMEOUT
            }
        }

    async def _schedule_next_chunk(self):
        """
        Schedule the next chunk if there's available capacity.

        This method is called in several scenarios:
        1. When a task completes (success/failure)
        2. When a task is revoked
        3. During periodic health checks
        4. When a worker becomes available
        """
        # Check if we have available slots
        if self.get_available_slots() <= 0:
            logger.debug("No available slots, skipping scheduling")
            return

        # Use a lock to prevent concurrent scheduling
        async with self._lock:
            try:
                # Double-check after acquiring lock
                if self.get_available_slots() <= 0:
                    return

                # Get and start the next chunk
                chunk_info = await self.get_next_chunk()
                if not chunk_info:
                    return

                logger.debug(
                    "Scheduled next chunk",
                    chunk_id=chunk_info.get('chunk_id'),
                    active_chunks=len(self.active_chunks)
                )

            except asyncio.CancelledError:
                # Allow task cancellation
                raise

            except Exception as e:
                logger.error(
                    "Error in schedule_next_chunk",
                    error=str(e),
                    exc_info=True
                )

                # If we have a chunk but failed to process it, clean up
                if 'chunk_info' in locals() and chunk_info:
                    self.active_chunks.pop(chunk_info.get('task_id'), None)

                    # Try to mark as failed in database
                    try:
                        await self.session.execute(
                            update(CrawlJob)
                            .where(CrawlJob.id == chunk_info.get('chunk_id'))
                            .values(
                                status='failed',
                                ended_at=datetime.utcnow(),
                                error_message=f"Scheduling error: {str(e)[:1000]}"
                            )
                        )
                        await self.session.commit()
                    except Exception as db_error:
                        logger.error(
                            "Failed to update failed chunk status",
                            error=str(db_error)
                        )
                        await self.session.rollback()


class ResourceMonitor:
    """
    Monitor resources and check capacity for chunk orchestration.

    Uses configuration-based limits and database queries instead of
    runtime metrics like psutil. This approach works consistently
    across all environments (local, Azure, AWS).

    Attributes:
        settings: Resource settings instance
        session: Database session for queries
        scheduler: Priority scheduler instance

    Example:
        >>> monitor = ResourceMonitor(session)
        >>> can_start = await monitor.can_start_chunk()
        >>> if can_start:
        ...     # Start new chunk
    """

    def __init__(
        self,
        session: AsyncSession,
        settings: Optional[ResourceSettings] = None,
        celery_app: Optional[Celery] = None
    ):
        """
        Initialize resource monitor.

        Args:
            session: Database session
            settings: Optional resource settings (uses default if None)
            celery_app: Optional Celery application instance
        """
        self.session = session
        self.settings = settings or get_resource_settings()
        self.scheduler = PriorityScheduler(session, celery_app=celery_app)

        logger.info(
            "ResourceMonitor initialized",
            environment=self.settings.environment,
            max_chunks=self.settings.effective_max_chunks,
        )

    async def get_active_chunk_count(self) -> int:
        """
        Get count of currently active processing chunks across all jobs.

        Queries database for sum of active_chunks across all jobs.

        Returns:
            Total number of active chunks

        Example:
            >>> count = await monitor.get_active_chunk_count()
            >>> print(f"Active chunks: {count}")
        """
        try:
            # Sum active_chunks across all jobs
            result = await self.session.execute(
                select(func.sum(CrawlJob.active_chunks))
            )
            total = result.scalar() or 0

            logger.debug(f"Active chunks: {total}")
            return int(total)

        except Exception as e:
            logger.error(f"Failed to get active chunk count: {e}")
            # Return conservative estimate on error
            return self.settings.effective_max_chunks

    async def get_job_active_chunks(self, job_id: int) -> int:
        """
        Get active chunk count for specific job.

        Args:
            job_id: Job ID to check

        Returns:
            Number of active chunks for the job
        """
        try:
            result = await self.session.execute(
                select(CrawlJob.active_chunks).where(CrawlJob.id == job_id)
            )
            count = result.scalar() or 0
            return int(count)

        except Exception as e:
            logger.error(f"Failed to get job active chunks: {e}")
            return 0

    async def can_start_chunk(self, required_chunks: int = 1) -> bool:
        """
        Check if we can start new chunk(s) based on current capacity.

        Checks:
        1. Current active chunks vs. max limit
        2. Available capacity for required chunks

        Args:
            required_chunks: Number of chunks to start (default: 1)

        Returns:
            True if capacity available, False otherwise

        Example:
            >>> if await monitor.can_start_chunk(5):
            ...     # Start 5 chunks
        """
        try:
            active = await self.get_active_chunk_count()
            max_chunks = self.settings.effective_max_chunks
            available = max_chunks - active

            can_start = available >= required_chunks

            logger.debug(
                "Capacity check",
                active=active,
                max=max_chunks,
                available=available,
                required=required_chunks,
                can_start=can_start,
            )

            return can_start

        except Exception as e:
            logger.error(f"Capacity check failed: {e}")
            # Conservative: don't start on error
            return False

    async def get_available_capacity(self) -> int:
        """
        Get number of chunks that can be started immediately.

        Returns:
            Number of available chunk slots

        Example:
            >>> capacity = await monitor.get_available_capacity()
            >>> print(f"Can start {capacity} chunks")
        """
        try:
            active = await self.get_active_chunk_count()
            max_chunks = self.settings.effective_max_chunks
            return max(0, max_chunks - active)

        except Exception as e:
            logger.error(f"Failed to get available capacity: {e}")
            return 0

    async def get_capacity_info(self) -> dict:
        """
        Get comprehensive capacity information.

        Returns:
            Dictionary with capacity metrics

        Example:
            >>> info = await monitor.get_capacity_info()
            >>> print(info)
            {
                'active_chunks': 25,
                'max_chunks': 35,
                'available': 10,
                'utilization': 71.4,
                'environment': 'azure'
            }
        """
        try:
            active = await self.get_active_chunk_count()
            max_chunks = self.settings.effective_max_chunks
            available = max(0, max_chunks - active)
            utilization = (active / max_chunks * 100) if max_chunks > 0 else 0

            return {
                'active_chunks': active,
                'max_chunks': max_chunks,
                'available': available,
                'utilization': round(utilization, 1),
                'environment': self.settings.environment,
                'chunk_size': self.settings.chunk_size_images,
                'storage_limit_mb': self.settings.max_temp_storage_mb,
            }

        except Exception as e:
            logger.error(f"Failed to get capacity info: {e}")
            return {
                'active_chunks': 0,
                'max_chunks': self.settings.effective_max_chunks,
                'available': 0,
                'utilization': 0,
                'environment': self.settings.environment,
                'error': str(e),
            }

    async def wait_for_capacity(
        self,
        required_chunks: int = 1,
        timeout_seconds: int = 300
    ) -> bool:
        """
        Wait for capacity to become available (for future use).

        Note: This is a placeholder for future implementation.
        Currently returns immediately based on current capacity.

        Args:
            required_chunks: Number of chunks needed
            timeout_seconds: Maximum wait time

        Returns:
            True if capacity became available, False if timeout
        """
        # For now, just check current capacity
        # Future: implement polling with timeout
        return await self.can_start_chunk(required_chunks)
