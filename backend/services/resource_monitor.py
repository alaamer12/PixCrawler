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

from typing import Optional

from backend.core.settings.resources import get_resource_settings, ResourceSettings
from backend.repositories import CrawlJobRepository
from utility.logging_config import get_logger

logger = get_logger(__name__)

__all__ = [
    'ResourceMonitor',
]


class ResourceMonitor:
    """
    Monitor resources and check capacity for chunk orchestration.
    
    Uses configuration-based limits and repository pattern instead of
    direct database access. This approach works consistently
    across all environments (local, Azure, AWS).
    
    Attributes:
        settings: Resource settings instance
        crawl_job_repo: CrawlJob repository for data access
    
    Example:
        >>> monitor = ResourceMonitor(crawl_job_repo)
        >>> can_start = await monitor.can_start_chunk()
        >>> if can_start:
        ...     # Start new chunk
    """
    
    def __init__(
        self,
        crawl_job_repo: CrawlJobRepository,
        settings: Optional[ResourceSettings] = None
    ):
        """
        Initialize resource monitor.
        
        Args:
            crawl_job_repo: CrawlJob repository instance
            settings: Optional resource settings (uses default if None)
        """
        self.crawl_job_repo = crawl_job_repo
        self.settings = settings or get_resource_settings()
        
        logger.info(
            "ResourceMonitor initialized",
            environment=self.settings.environment,
            max_chunks=self.settings.effective_max_chunks,
        )
    
    async def get_active_chunk_count(self) -> int:
        """
        Get count of currently active processing chunks across all jobs.
        
        Uses repository to query sum of active_chunks across all jobs.
        
        Returns:
            Total number of active chunks
        
        Example:
            >>> count = await monitor.get_active_chunk_count()
            >>> print(f"Active chunks: {count}")
        """
        try:
            # Get total active chunks from repository
            total = await self.crawl_job_repo.get_total_active_chunks()
            
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
            job = await self.crawl_job_repo.get_by_id(job_id)
            if not job:
                return 0
            return int(job.active_chunks or 0)
            
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
