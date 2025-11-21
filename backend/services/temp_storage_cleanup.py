"""
Temporary Storage Cleanup Service for PixCrawler Backend.

This service manages cleanup of temporary storage files across various scenarios:
- Normal cleanup after chunk completion
- Crash recovery cleanup for failed chunks
- Emergency cleanup at storage threshold (95% full)
- Orphaned file detection and cleanup
- Scheduled periodic cleanup via Celery Beat

Classes:
    TempStorageCleanupService: Main service for temp storage cleanup operations
    CleanupStats: Statistics tracking for cleanup operations
    OrphanedFileDetector: Utility for detecting orphaned temporary files

Features:
    - Multi-scenario cleanup support
    - Storage threshold monitoring
    - Orphaned file detection
    - Comprehensive logging and statistics
    - Integration with Celery for background processing
"""

import os
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from backend.core.exceptions import PixCrawlerException
from backend.core.config import get_settings
from backend.storage.base import StorageProvider
from backend.repositories.crawl_job_repository import CrawlJobRepository
from backend.repositories.image_repository import ImageRepository
from backend.models import CrawlJob, Image
from .base import BaseService
from utility.logging_config import get_logger

__all__ = [
    'TempStorageCleanupService',
    'CleanupTrigger',
    'CleanupStats',
    'OrphanedFileDetector',
    'TempStorageCleanupError'
]

logger = get_logger(__name__)


class CleanupTrigger(Enum):
    """Cleanup trigger types."""
    CHUNK_COMPLETION = "chunk_completion"
    CRASH_RECOVERY = "crash_recovery"
    EMERGENCY_THRESHOLD = "emergency_threshold"
    ORPHANED_FILES = "orphaned_files"
    SCHEDULED = "scheduled"
    MANUAL = "manual"


@dataclass
class CleanupStats:
    """Statistics for cleanup operations."""
    trigger: CleanupTrigger
    start_time: datetime
    end_time: Optional[datetime] = None
    files_scanned: int = 0
    files_deleted: int = 0
    bytes_freed: int = 0
    errors: List[str] = field(default_factory=list)
    storage_before_percent: float = 0.0
    storage_after_percent: float = 0.0
    
    @property
    def duration_seconds(self) -> float:
        """Calculate cleanup duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary for logging/API."""
        return {
            "trigger": self.trigger.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "files_scanned": self.files_scanned,
            "files_deleted": self.files_deleted,
            "bytes_freed": self.bytes_freed,
            "storage_before_percent": self.storage_before_percent,
            "storage_after_percent": self.storage_after_percent,
            "errors": self.errors
        }


class TempStorageCleanupError(PixCrawlerException):
    """Exception raised during temp storage cleanup operations."""
    pass


class OrphanedFileDetector:
    """Utility for detecting orphaned temporary files."""
    
    def __init__(self, session: AsyncSession, temp_storage_path: Path):
        self.session = session
        self.temp_storage_path = temp_storage_path
        self.logger = get_logger(f"{__name__}.OrphanedFileDetector")
    
    async def detect_orphaned_files(self, max_age_hours: int = 24) -> List[Path]:
        """
        Detect orphaned temporary files.
        
        Files are considered orphaned if:
        1. They exist in temp storage but have no corresponding active crawl job
        2. They belong to failed/cancelled jobs older than max_age_hours
        3. They have no database references
        
        Args:
            max_age_hours: Maximum age for files to be considered for cleanup
            
        Returns:
            List of orphaned file paths
        """
        orphaned_files = []
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        try:
            # Get all temp files
            temp_files = self._scan_temp_files()
            
            # Get active crawl jobs
            active_jobs = await self._get_active_crawl_jobs()
            active_job_ids = {job.id for job in active_jobs}
            
            # Get failed/cancelled jobs older than cutoff
            old_failed_jobs = await self._get_old_failed_jobs(cutoff_time)
            old_failed_job_ids = {job.id for job in old_failed_jobs}
            
            # Check each temp file
            for file_path in temp_files:
                job_id = self._extract_job_id_from_path(file_path)
                
                if job_id is None:
                    # File with no job ID pattern - potential orphan
                    if self._is_file_old_enough(file_path, cutoff_time):
                        orphaned_files.append(file_path)
                        self.logger.debug(f"Orphaned file (no job ID): {file_path}")
                
                elif job_id not in active_job_ids:
                    # File belongs to inactive job
                    if job_id in old_failed_job_ids or not await self._job_exists(job_id):
                        orphaned_files.append(file_path)
                        self.logger.debug(f"Orphaned file (inactive job {job_id}): {file_path}")
            
            self.logger.info(f"Detected {len(orphaned_files)} orphaned files")
            return orphaned_files
            
        except Exception as e:
            self.logger.error(f"Error detecting orphaned files: {e}")
            raise TempStorageCleanupError(f"Failed to detect orphaned files: {e}")
    
    def _scan_temp_files(self) -> List[Path]:
        """Scan temp storage directory for all files."""
        temp_files = []
        
        if not self.temp_storage_path.exists():
            return temp_files
        
        for root, dirs, files in os.walk(self.temp_storage_path):
            for file in files:
                file_path = Path(root) / file
                temp_files.append(file_path)
        
        return temp_files
    
    async def _get_active_crawl_jobs(self) -> List[CrawlJob]:
        """Get all active (running/pending) crawl jobs."""
        stmt = select(CrawlJob).where(
            CrawlJob.status.in_(['pending', 'running', 'processing'])
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def _get_old_failed_jobs(self, cutoff_time: datetime) -> List[CrawlJob]:
        """Get failed/cancelled jobs older than cutoff time."""
        stmt = select(CrawlJob).where(
            and_(
                CrawlJob.status.in_(['failed', 'cancelled', 'error']),
                CrawlJob.updated_at < cutoff_time
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def _job_exists(self, job_id: int) -> bool:
        """Check if a job exists in the database."""
        stmt = select(CrawlJob.id).where(CrawlJob.id == job_id)
        result = await self.session.execute(stmt)
        return result.scalar() is not None
    
    def _extract_job_id_from_path(self, file_path: Path) -> Optional[int]:
        """Extract job ID from file path pattern."""
        try:
            # Look for patterns like: temp_job_123_chunk_1.tmp, job_456_image.jpg, etc.
            parts = file_path.name.split('_')
            for i, part in enumerate(parts):
                if part == 'job' and i + 1 < len(parts):
                    return int(parts[i + 1])
            return None
        except (ValueError, IndexError):
            return None
    
    def _is_file_old_enough(self, file_path: Path, cutoff_time: datetime) -> bool:
        """Check if file is older than cutoff time."""
        try:
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            return file_mtime < cutoff_time
        except OSError:
            return True  # If we can't get mtime, consider it old


class TempStorageCleanupService(BaseService):
    """
    Service for managing temporary storage cleanup operations.
    
    Handles various cleanup scenarios:
    - Normal cleanup after chunk completion
    - Crash recovery cleanup
    - Emergency cleanup at storage threshold
    - Orphaned file cleanup
    - Scheduled periodic cleanup
    """
    
    def __init__(
        self,
        storage_provider: StorageProvider,
        session: AsyncSession,
        crawl_job_repo: Optional[CrawlJobRepository] = None,
        image_repo: Optional[ImageRepository] = None
    ):
        """
        Initialize temp storage cleanup service.
        
        Args:
            storage_provider: Storage provider instance
            session: Database session
            crawl_job_repo: Optional crawl job repository
            image_repo: Optional image repository
        """
        super().__init__()
        self.storage_provider = storage_provider
        self.session = session
        self.crawl_job_repo = crawl_job_repo or CrawlJobRepository(session)
        self.image_repo = image_repo or ImageRepository(session)
        
        settings = get_settings()
        # Try to get temp storage cleanup settings, fallback to defaults
        if hasattr(settings, 'temp_storage_cleanup'):
            cleanup_settings = settings.temp_storage_cleanup
            self.temp_storage_path = cleanup_settings.temp_storage_path
            self.emergency_threshold = cleanup_settings.emergency_cleanup_threshold
            self.cleanup_batch_size = cleanup_settings.cleanup_batch_size
            self.max_orphan_age_hours = cleanup_settings.max_orphan_age_hours
        else:
            # Fallback to storage settings or defaults
            self.temp_storage_path = Path(getattr(settings.storage, 'temp_storage_path', './temp_storage'))
            self.emergency_threshold = getattr(settings.storage, 'emergency_cleanup_threshold', 95.0)
            self.cleanup_batch_size = getattr(settings.storage, 'cleanup_batch_size', 1000)
            self.max_orphan_age_hours = getattr(settings.storage, 'max_orphan_age_hours', 24)
        
        self.orphan_detector = OrphanedFileDetector(session, self.temp_storage_path)
        self.logger = get_logger(f"{__name__}.TempStorageCleanupService")
    
    async def cleanup_after_chunk_completion(
        self,
        job_id: int,
        chunk_id: str,
        completed_files: List[str]
    ) -> CleanupStats:
        """
        Clean up temporary files after successful chunk completion.
        
        Args:
            job_id: Crawl job ID
            chunk_id: Chunk identifier
            completed_files: List of files that were successfully processed
            
        Returns:
            Cleanup statistics
        """
        stats = CleanupStats(
            trigger=CleanupTrigger.CHUNK_COMPLETION,
            start_time=datetime.utcnow()
        )
        
        try:
            self.logger.info(f"Starting chunk completion cleanup for job {job_id}, chunk {chunk_id}")
            
            # Get storage usage before cleanup
            stats.storage_before_percent = await self._get_storage_usage_percent()
            
            # Find temp files for this chunk
            chunk_pattern = f"job_{job_id}_chunk_{chunk_id}_*"
            temp_files = self._find_temp_files(chunk_pattern)
            
            stats.files_scanned = len(temp_files)
            
            # Delete completed temp files
            for file_path in temp_files:
                if any(completed_file in str(file_path) for completed_file in completed_files):
                    try:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        stats.files_deleted += 1
                        stats.bytes_freed += file_size
                        self.logger.debug(f"Deleted temp file: {file_path}")
                    except OSError as e:
                        error_msg = f"Failed to delete {file_path}: {e}"
                        stats.errors.append(error_msg)
                        self.logger.warning(error_msg)
            
            # Get storage usage after cleanup
            stats.storage_after_percent = await self._get_storage_usage_percent()
            stats.end_time = datetime.utcnow()
            
            self.logger.info(
                f"Chunk completion cleanup completed: "
                f"{stats.files_deleted}/{stats.files_scanned} files deleted, "
                f"{stats.bytes_freed} bytes freed"
            )
            
            return stats
            
        except Exception as e:
            stats.errors.append(str(e))
            stats.end_time = datetime.utcnow()
            self.logger.error(f"Chunk completion cleanup failed: {e}")
            raise TempStorageCleanupError(f"Chunk completion cleanup failed: {e}")
    
    async def cleanup_after_crash(self, job_id: Optional[int] = None) -> CleanupStats:
        """
        Clean up temporary files after crashes or failures.
        
        Args:
            job_id: Optional specific job ID to clean up. If None, cleans all failed jobs.
            
        Returns:
            Cleanup statistics
        """
        stats = CleanupStats(
            trigger=CleanupTrigger.CRASH_RECOVERY,
            start_time=datetime.utcnow()
        )
        
        try:
            self.logger.info(f"Starting crash recovery cleanup for job {job_id or 'all failed jobs'}")
            
            stats.storage_before_percent = await self._get_storage_usage_percent()
            
            # Get failed jobs to clean up
            if job_id:
                failed_jobs = [await self.crawl_job_repo.get_by_id(job_id)]
                failed_jobs = [job for job in failed_jobs if job and job.status in ['failed', 'cancelled', 'error']]
            else:
                failed_jobs = await self._get_failed_jobs()
            
            # Clean up temp files for each failed job
            for job in failed_jobs:
                job_pattern = f"job_{job.id}_*"
                temp_files = self._find_temp_files(job_pattern)
                
                stats.files_scanned += len(temp_files)
                
                for file_path in temp_files:
                    try:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        stats.files_deleted += 1
                        stats.bytes_freed += file_size
                        self.logger.debug(f"Deleted crashed job temp file: {file_path}")
                    except OSError as e:
                        error_msg = f"Failed to delete {file_path}: {e}"
                        stats.errors.append(error_msg)
                        self.logger.warning(error_msg)
            
            stats.storage_after_percent = await self._get_storage_usage_percent()
            stats.end_time = datetime.utcnow()
            
            self.logger.info(
                f"Crash recovery cleanup completed: "
                f"{stats.files_deleted}/{stats.files_scanned} files deleted, "
                f"{stats.bytes_freed} bytes freed"
            )
            
            return stats
            
        except Exception as e:
            stats.errors.append(str(e))
            stats.end_time = datetime.utcnow()
            self.logger.error(f"Crash recovery cleanup failed: {e}")
            raise TempStorageCleanupError(f"Crash recovery cleanup failed: {e}")
    
    async def emergency_cleanup(self) -> CleanupStats:
        """
        Perform emergency cleanup when storage threshold is exceeded.
        
        Returns:
            Cleanup statistics
        """
        stats = CleanupStats(
            trigger=CleanupTrigger.EMERGENCY_THRESHOLD,
            start_time=datetime.utcnow()
        )
        
        try:
            stats.storage_before_percent = await self._get_storage_usage_percent()
            
            if stats.storage_before_percent < self.emergency_threshold:
                self.logger.info(f"Storage usage {stats.storage_before_percent:.1f}% below emergency threshold {self.emergency_threshold}%")
                stats.end_time = datetime.utcnow()
                return stats
            
            self.logger.warning(
                f"Emergency cleanup triggered! Storage usage: {stats.storage_before_percent:.1f}% "
                f"(threshold: {self.emergency_threshold}%)"
            )
            
            # Priority cleanup order:
            # 1. Orphaned files
            # 2. Failed job temp files
            # 3. Oldest temp files
            
            # Clean orphaned files first
            orphaned_files = await self.orphan_detector.detect_orphaned_files(max_age_hours=1)  # More aggressive for emergency
            stats.files_scanned += len(orphaned_files)
            
            for file_path in orphaned_files:
                if await self._delete_file_safely(file_path, stats):
                    # Check if we're below threshold
                    current_usage = await self._get_storage_usage_percent()
                    if current_usage < self.emergency_threshold - 5:  # 5% buffer
                        break
            
            # If still above threshold, clean failed job files
            current_usage = await self._get_storage_usage_percent()
            if current_usage >= self.emergency_threshold - 5:
                failed_job_files = await self._get_failed_job_temp_files()
                stats.files_scanned += len(failed_job_files)
                
                for file_path in failed_job_files:
                    if await self._delete_file_safely(file_path, stats):
                        current_usage = await self._get_storage_usage_percent()
                        if current_usage < self.emergency_threshold - 5:
                            break
            
            # If still above threshold, clean oldest temp files
            current_usage = await self._get_storage_usage_percent()
            if current_usage >= self.emergency_threshold - 5:
                oldest_files = self._get_oldest_temp_files(limit=self.cleanup_batch_size)
                stats.files_scanned += len(oldest_files)
                
                for file_path in oldest_files:
                    if await self._delete_file_safely(file_path, stats):
                        current_usage = await self._get_storage_usage_percent()
                        if current_usage < self.emergency_threshold - 10:  # 10% buffer for oldest files
                            break
            
            stats.storage_after_percent = await self._get_storage_usage_percent()
            stats.end_time = datetime.utcnow()
            
            if stats.storage_after_percent >= self.emergency_threshold:
                self.logger.error(
                    f"Emergency cleanup completed but storage still at {stats.storage_after_percent:.1f}% "
                    f"(threshold: {self.emergency_threshold}%)"
                )
            else:
                self.logger.info(
                    f"Emergency cleanup successful: storage reduced from {stats.storage_before_percent:.1f}% "
                    f"to {stats.storage_after_percent:.1f}%"
                )
            
            return stats
            
        except Exception as e:
            stats.errors.append(str(e))
            stats.end_time = datetime.utcnow()
            self.logger.error(f"Emergency cleanup failed: {e}")
            raise TempStorageCleanupError(f"Emergency cleanup failed: {e}")
    
    async def cleanup_orphaned_files(self, max_age_hours: int = None) -> CleanupStats:
        """
        Clean up orphaned temporary files.
        
        Args:
            max_age_hours: Maximum age for files to be considered orphaned
            
        Returns:
            Cleanup statistics
        """
        stats = CleanupStats(
            trigger=CleanupTrigger.ORPHANED_FILES,
            start_time=datetime.utcnow()
        )
        
        try:
            max_age = max_age_hours or self.max_orphan_age_hours
            self.logger.info(f"Starting orphaned files cleanup (max age: {max_age} hours)")
            
            stats.storage_before_percent = await self._get_storage_usage_percent()
            
            # Detect orphaned files
            orphaned_files = await self.orphan_detector.detect_orphaned_files(max_age_hours=max_age)
            stats.files_scanned = len(orphaned_files)
            
            # Delete orphaned files
            for file_path in orphaned_files:
                await self._delete_file_safely(file_path, stats)
            
            stats.storage_after_percent = await self._get_storage_usage_percent()
            stats.end_time = datetime.utcnow()
            
            self.logger.info(
                f"Orphaned files cleanup completed: "
                f"{stats.files_deleted}/{stats.files_scanned} files deleted, "
                f"{stats.bytes_freed} bytes freed"
            )
            
            return stats
            
        except Exception as e:
            stats.errors.append(str(e))
            stats.end_time = datetime.utcnow()
            self.logger.error(f"Orphaned files cleanup failed: {e}")
            raise TempStorageCleanupError(f"Orphaned files cleanup failed: {e}")
    
    async def scheduled_cleanup(self) -> CleanupStats:
        """
        Perform scheduled periodic cleanup.
        
        Returns:
            Cleanup statistics
        """
        stats = CleanupStats(
            trigger=CleanupTrigger.SCHEDULED,
            start_time=datetime.utcnow()
        )
        
        try:
            self.logger.info("Starting scheduled cleanup")
            
            stats.storage_before_percent = await self._get_storage_usage_percent()
            
            # Check if emergency cleanup is needed
            if stats.storage_before_percent >= self.emergency_threshold:
                emergency_stats = await self.emergency_cleanup()
                # Merge stats
                stats.files_scanned += emergency_stats.files_scanned
                stats.files_deleted += emergency_stats.files_deleted
                stats.bytes_freed += emergency_stats.bytes_freed
                stats.errors.extend(emergency_stats.errors)
                stats.storage_after_percent = emergency_stats.storage_after_percent
            else:
                # Normal scheduled cleanup
                # 1. Clean orphaned files
                orphan_stats = await self.cleanup_orphaned_files()
                stats.files_scanned += orphan_stats.files_scanned
                stats.files_deleted += orphan_stats.files_deleted
                stats.bytes_freed += orphan_stats.bytes_freed
                stats.errors.extend(orphan_stats.errors)
                
                # 2. Clean failed job files older than 1 hour
                failed_stats = await self.cleanup_after_crash()
                stats.files_scanned += failed_stats.files_scanned
                stats.files_deleted += failed_stats.files_deleted
                stats.bytes_freed += failed_stats.bytes_freed
                stats.errors.extend(failed_stats.errors)
                
                stats.storage_after_percent = await self._get_storage_usage_percent()
            
            stats.end_time = datetime.utcnow()
            
            self.logger.info(
                f"Scheduled cleanup completed: "
                f"{stats.files_deleted}/{stats.files_scanned} files deleted, "
                f"{stats.bytes_freed} bytes freed, "
                f"storage: {stats.storage_before_percent:.1f}% → {stats.storage_after_percent:.1f}%"
            )
            
            return stats
            
        except Exception as e:
            stats.errors.append(str(e))
            stats.end_time = datetime.utcnow()
            self.logger.error(f"Scheduled cleanup failed: {e}")
            raise TempStorageCleanupError(f"Scheduled cleanup failed: {e}")
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get current storage statistics.
        
        Returns:
            Dictionary with storage statistics
        """
        try:
            usage_percent = await self._get_storage_usage_percent()
            temp_files = self._find_temp_files("*")
            total_temp_size = sum(f.stat().st_size for f in temp_files if f.exists())
            
            # Get job-related stats
            active_jobs_count = len(await self._get_active_jobs())
            failed_jobs_count = len(await self._get_failed_jobs())
            
            # Get orphaned files count
            orphaned_files = await self.orphan_detector.detect_orphaned_files()
            orphaned_count = len(orphaned_files)
            orphaned_size = sum(f.stat().st_size for f in orphaned_files if f.exists())
            
            return {
                "storage_usage_percent": usage_percent,
                "emergency_threshold": self.emergency_threshold,
                "temp_files_count": len(temp_files),
                "temp_files_size_bytes": total_temp_size,
                "active_jobs_count": active_jobs_count,
                "failed_jobs_count": failed_jobs_count,
                "orphaned_files_count": orphaned_count,
                "orphaned_files_size_bytes": orphaned_size,
                "cleanup_needed": usage_percent >= self.emergency_threshold or orphaned_count > 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get storage stats: {e}")
            raise TempStorageCleanupError(f"Failed to get storage stats: {e}")
    
    # Helper methods
    
    async def _get_storage_usage_percent(self) -> float:
        """Get current storage usage percentage."""
        try:
            if hasattr(self.storage_provider, 'get_usage_stats'):
                stats = await self.storage_provider.get_usage_stats()
                return stats.get('usage_percent', 0.0)
            else:
                # Fallback to disk usage for local storage
                statvfs = os.statvfs(self.temp_storage_path.parent)
                total = statvfs.f_frsize * statvfs.f_blocks
                available = statvfs.f_frsize * statvfs.f_available
                used = total - available
                return (used / total) * 100.0 if total > 0 else 0.0
        except Exception as e:
            self.logger.warning(f"Failed to get storage usage: {e}")
            return 0.0
    
    def _find_temp_files(self, pattern: str) -> List[Path]:
        """Find temporary files matching pattern."""
        temp_files = []
        
        if not self.temp_storage_path.exists():
            return temp_files
        
        try:
            temp_files = list(self.temp_storage_path.glob(pattern))
            # Also search in subdirectories
            temp_files.extend(self.temp_storage_path.glob(f"**/{pattern}"))
        except Exception as e:
            self.logger.warning(f"Failed to find temp files with pattern {pattern}: {e}")
        
        return temp_files
    
    async def _get_active_jobs(self) -> List[CrawlJob]:
        """Get all active crawl jobs."""
        stmt = select(CrawlJob).where(
            CrawlJob.status.in_(['pending', 'running', 'processing'])
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def _get_failed_jobs(self) -> List[CrawlJob]:
        """Get all failed crawl jobs."""
        stmt = select(CrawlJob).where(
            CrawlJob.status.in_(['failed', 'cancelled', 'error'])
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def _get_failed_job_temp_files(self) -> List[Path]:
        """Get temp files for failed jobs."""
        failed_jobs = await self._get_failed_jobs()
        temp_files = []
        
        for job in failed_jobs:
            job_pattern = f"job_{job.id}_*"
            job_files = self._find_temp_files(job_pattern)
            temp_files.extend(job_files)
        
        return temp_files
    
    def _get_oldest_temp_files(self, limit: int = 1000) -> List[Path]:
        """Get oldest temporary files up to limit."""
        temp_files = self._find_temp_files("*")
        
        # Sort by modification time (oldest first)
        try:
            temp_files.sort(key=lambda f: f.stat().st_mtime)
        except OSError:
            # If we can't get mtime, keep original order
            pass
        
        return temp_files[:limit]
    
    async def _delete_file_safely(self, file_path: Path, stats: CleanupStats) -> bool:
        """
        Safely delete a file and update stats.
        
        Returns:
            True if file was deleted successfully, False otherwise
        """
        try:
            if file_path.exists():
                file_size = file_path.stat().st_size
                file_path.unlink()
                stats.files_deleted += 1
                stats.bytes_freed += file_size
                self.logger.debug(f"Deleted temp file: {file_path}")
                return True
        except OSError as e:
            error_msg = f"Failed to delete {file_path}: {e}"
            stats.errors.append(error_msg)
            self.logger.warning(error_msg)
        
        return False
