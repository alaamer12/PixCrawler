"""
Celery tasks for temporary storage cleanup operations.

This module provides Celery tasks for background execution of temp storage
cleanup operations, including scheduled periodic cleanup and emergency cleanup.

Tasks:
    task_scheduled_cleanup: Periodic cleanup task (scheduled via Celery Beat)
    task_emergency_cleanup: Emergency cleanup when storage threshold exceeded
    task_cleanup_orphaned_files: Clean up orphaned temporary files
    task_cleanup_after_crash: Clean up after job crashes/failures
    task_cleanup_after_chunk: Clean up after successful chunk completion

Features:
    - Background execution via Celery
    - Comprehensive error handling and logging
    - Integration with TempStorageCleanupService
    - Automatic retry on failures
    - Statistics tracking and reporting
"""

from typing import Dict, Any, Optional, List
from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession

from celery_core.app import get_celery_app
from celery_core.base import BaseTask
from backend.database.connection import AsyncSessionLocal
from backend.services.temp_storage_cleanup import TempStorageCleanupService, CleanupTrigger
from backend.storage.factory import get_storage_provider
from utility.logging_config import get_logger

# Get Celery app
celery_app = get_celery_app()
logger = get_logger(__name__)

__all__ = [
    'task_scheduled_cleanup',
    'task_emergency_cleanup', 
    'task_cleanup_orphaned_files',
    'task_cleanup_after_crash',
    'task_cleanup_after_chunk'
]


class TempStorageCleanupTask(BaseTask):
    """Base task class for temp storage cleanup operations."""
    
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 60}
    
    async def get_cleanup_service(self, session: AsyncSession) -> TempStorageCleanupService:
        """Get configured cleanup service instance."""
        storage_provider = get_storage_provider()
        return TempStorageCleanupService(
            storage_provider=storage_provider,
            session=session
        )


@celery_app.task(
    bind=True,
    base=TempStorageCleanupTask,
    name="temp_storage.scheduled_cleanup",
    queue="maintenance",
    rate_limit="1/m",  # Once per minute max
    time_limit=1800,   # 30 minutes
    soft_time_limit=1500  # 25 minutes
)
def task_scheduled_cleanup(self) -> Dict[str, Any]:
    """
    Scheduled periodic cleanup task.
    
    This task is executed periodically via Celery Beat to perform
    routine cleanup of temporary storage files.
    
    Returns:
        Cleanup statistics dictionary
    """
    logger.info("Starting scheduled temp storage cleanup task")
    
    try:
        async def _run_cleanup():
            async with AsyncSessionLocal() as session:
                cleanup_service = await self.get_cleanup_service(session)
                return await cleanup_service.scheduled_cleanup()
        
        # Run async cleanup
        import asyncio
        stats = asyncio.run(_run_cleanup())
        
        result = {
            "success": True,
            "stats": stats.to_dict(),
            "message": f"Scheduled cleanup completed: {stats.files_deleted} files deleted, {stats.bytes_freed} bytes freed"
        }
        
        logger.info(f"Scheduled cleanup task completed successfully: {result['message']}")
        return result
        
    except Exception as e:
        logger.error(f"Scheduled cleanup task failed: {e}")
        result = {
            "success": False,
            "error": str(e),
            "message": f"Scheduled cleanup failed: {e}"
        }
        
        # Re-raise for Celery retry mechanism
        raise self.retry(exc=e)


@celery_app.task(
    bind=True,
    base=TempStorageCleanupTask,
    name="temp_storage.emergency_cleanup",
    queue="maintenance",
    priority=9,  # High priority
    rate_limit="5/m",  # Up to 5 per minute for emergencies
    time_limit=3600,   # 1 hour
    soft_time_limit=3300  # 55 minutes
)
def task_emergency_cleanup(self) -> Dict[str, Any]:
    """
    Emergency cleanup task when storage threshold exceeded.
    
    This task is triggered when storage usage exceeds the emergency
    threshold (default 95%) to prevent storage overflow.
    
    Returns:
        Cleanup statistics dictionary
    """
    logger.warning("Starting emergency temp storage cleanup task")
    
    try:
        async def _run_cleanup():
            async with AsyncSessionLocal() as session:
                cleanup_service = await self.get_cleanup_service(session)
                return await cleanup_service.emergency_cleanup()
        
        # Run async cleanup
        import asyncio
        stats = asyncio.run(_run_cleanup())
        
        result = {
            "success": True,
            "stats": stats.to_dict(),
            "message": f"Emergency cleanup completed: {stats.files_deleted} files deleted, {stats.bytes_freed} bytes freed",
            "storage_before": stats.storage_before_percent,
            "storage_after": stats.storage_after_percent
        }
        
        # Log as warning if still above threshold
        if stats.storage_after_percent >= 90:
            logger.warning(f"Emergency cleanup completed but storage still high: {result['message']}")
        else:
            logger.info(f"Emergency cleanup task completed successfully: {result['message']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Emergency cleanup task failed: {e}")
        result = {
            "success": False,
            "error": str(e),
            "message": f"Emergency cleanup failed: {e}"
        }
        
        # Re-raise for Celery retry mechanism
        raise self.retry(exc=e)


@celery_app.task(
    bind=True,
    base=TempStorageCleanupTask,
    name="temp_storage.cleanup_orphaned_files",
    queue="maintenance",
    rate_limit="10/h",  # 10 per hour
    time_limit=1800,    # 30 minutes
    soft_time_limit=1500  # 25 minutes
)
def task_cleanup_orphaned_files(self, max_age_hours: Optional[int] = None) -> Dict[str, Any]:
    """
    Clean up orphaned temporary files.
    
    Args:
        max_age_hours: Maximum age for files to be considered orphaned
        
    Returns:
        Cleanup statistics dictionary
    """
    logger.info(f"Starting orphaned files cleanup task (max_age_hours: {max_age_hours})")
    
    try:
        async def _run_cleanup():
            async with AsyncSessionLocal() as session:
                cleanup_service = await self.get_cleanup_service(session)
                return await cleanup_service.cleanup_orphaned_files(max_age_hours=max_age_hours)
        
        # Run async cleanup
        import asyncio
        stats = asyncio.run(_run_cleanup())
        
        result = {
            "success": True,
            "stats": stats.to_dict(),
            "message": f"Orphaned files cleanup completed: {stats.files_deleted} files deleted, {stats.bytes_freed} bytes freed",
            "max_age_hours": max_age_hours
        }
        
        logger.info(f"Orphaned files cleanup task completed successfully: {result['message']}")
        return result
        
    except Exception as e:
        logger.error(f"Orphaned files cleanup task failed: {e}")
        result = {
            "success": False,
            "error": str(e),
            "message": f"Orphaned files cleanup failed: {e}"
        }
        
        # Re-raise for Celery retry mechanism
        raise self.retry(exc=e)


@celery_app.task(
    bind=True,
    base=TempStorageCleanupTask,
    name="temp_storage.cleanup_after_crash",
    queue="maintenance",
    rate_limit="20/h",  # 20 per hour
    time_limit=900,     # 15 minutes
    soft_time_limit=750   # 12.5 minutes
)
def task_cleanup_after_crash(self, job_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Clean up temporary files after job crashes or failures.
    
    Args:
        job_id: Optional specific job ID to clean up
        
    Returns:
        Cleanup statistics dictionary
    """
    logger.info(f"Starting crash recovery cleanup task for job {job_id or 'all failed jobs'}")
    
    try:
        async def _run_cleanup():
            async with AsyncSessionLocal() as session:
                cleanup_service = await self.get_cleanup_service(session)
                return await cleanup_service.cleanup_after_crash(job_id=job_id)
        
        # Run async cleanup
        import asyncio
        stats = asyncio.run(_run_cleanup())
        
        result = {
            "success": True,
            "stats": stats.to_dict(),
            "message": f"Crash recovery cleanup completed: {stats.files_deleted} files deleted, {stats.bytes_freed} bytes freed",
            "job_id": job_id
        }
        
        logger.info(f"Crash recovery cleanup task completed successfully: {result['message']}")
        return result
        
    except Exception as e:
        logger.error(f"Crash recovery cleanup task failed: {e}")
        result = {
            "success": False,
            "error": str(e),
            "message": f"Crash recovery cleanup failed: {e}"
        }
        
        # Re-raise for Celery retry mechanism
        raise self.retry(exc=e)


@celery_app.task(
    bind=True,
    base=TempStorageCleanupTask,
    name="temp_storage.cleanup_after_chunk",
    queue="maintenance",
    rate_limit="100/h",  # 100 per hour (more frequent for chunk completions)
    time_limit=300,      # 5 minutes
    soft_time_limit=240    # 4 minutes
)
def task_cleanup_after_chunk(
    self,
    job_id: int,
    chunk_id: str,
    completed_files: List[str]
) -> Dict[str, Any]:
    """
    Clean up temporary files after successful chunk completion.
    
    Args:
        job_id: Crawl job ID
        chunk_id: Chunk identifier
        completed_files: List of files that were successfully processed
        
    Returns:
        Cleanup statistics dictionary
    """
    logger.info(f"Starting chunk completion cleanup task for job {job_id}, chunk {chunk_id}")
    
    try:
        async def _run_cleanup():
            async with AsyncSessionLocal() as session:
                cleanup_service = await self.get_cleanup_service(session)
                return await cleanup_service.cleanup_after_chunk_completion(
                    job_id=job_id,
                    chunk_id=chunk_id,
                    completed_files=completed_files
                )
        
        # Run async cleanup
        import asyncio
        stats = asyncio.run(_run_cleanup())
        
        result = {
            "success": True,
            "stats": stats.to_dict(),
            "message": f"Chunk completion cleanup completed: {stats.files_deleted} files deleted, {stats.bytes_freed} bytes freed",
            "job_id": job_id,
            "chunk_id": chunk_id,
            "completed_files_count": len(completed_files)
        }
        
        logger.info(f"Chunk completion cleanup task completed successfully: {result['message']}")
        return result
        
    except Exception as e:
        logger.error(f"Chunk completion cleanup task failed: {e}")
        result = {
            "success": False,
            "error": str(e),
            "message": f"Chunk completion cleanup failed: {e}",
            "job_id": job_id,
            "chunk_id": chunk_id
        }
        
        # Re-raise for Celery retry mechanism
        raise self.retry(exc=e)


@celery_app.task(
    bind=True,
    base=BaseTask,
    name="temp_storage.get_storage_stats",
    queue="maintenance",
    rate_limit="30/m",  # 30 per minute for monitoring
    time_limit=60,      # 1 minute
    soft_time_limit=45    # 45 seconds
)
def task_get_storage_stats(self) -> Dict[str, Any]:
    """
    Get current storage statistics.
    
    Returns:
        Storage statistics dictionary
    """
    logger.debug("Getting temp storage statistics")
    
    try:
        async def _get_stats():
            storage_provider = get_storage_provider()
            async with AsyncSessionLocal() as session:
                cleanup_service = TempStorageCleanupService(
                    storage_provider=storage_provider,
                    session=session
                )
                return await cleanup_service.get_storage_stats()
        
        # Run async operation
        import asyncio
        stats = asyncio.run(_get_stats())
        
        result = {
            "success": True,
            "stats": stats,
            "message": "Storage statistics retrieved successfully"
        }
        
        # Log warning if cleanup is needed
        if stats.get("cleanup_needed", False):
            logger.warning(f"Storage cleanup needed: {stats}")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get storage stats: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to get storage stats: {e}"
        }


# Helper function to trigger emergency cleanup if needed
def trigger_emergency_cleanup_if_needed():
    """
    Check storage usage and trigger emergency cleanup if needed.
    
    This function can be called from other parts of the application
    to automatically trigger emergency cleanup when storage is full.
    """
    try:
        # Get current stats
        stats_result = task_get_storage_stats.delay()
        stats = stats_result.get(timeout=30)
        
        if stats.get("success") and stats.get("stats", {}).get("cleanup_needed", False):
            storage_usage = stats["stats"].get("storage_usage_percent", 0)
            emergency_threshold = stats["stats"].get("emergency_threshold", 95)
            
            if storage_usage >= emergency_threshold:
                logger.warning(f"Triggering emergency cleanup: storage at {storage_usage}%")
                task_emergency_cleanup.delay()
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"Failed to check/trigger emergency cleanup: {e}")
        return False
