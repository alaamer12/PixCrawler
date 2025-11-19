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

from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import CrawlJob
from .base import BaseRepository

__all__ = ['CrawlJobRepository']


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
    
    async def update_progress(
        self,
        job_id: int,
        progress: int,
        downloaded_images: int,
        valid_images: Optional[int] = None
    ) -> Optional[CrawlJob]:
        """
        Update job progress metrics.
        
        Args:
            job_id: Job ID
            progress: Progress percentage (0-100)
            downloaded_images: Number of downloaded images
            valid_images: Number of valid images (optional)
        
        Returns:
            Updated job or None if not found
        """
        job = await self.get_by_id(job_id)
        if not job:
            return None
        
        job.progress = progress
        job.downloaded_images = downloaded_images
        if valid_images is not None:
            job.valid_images = valid_images
        
        await self.session.commit()
        await self.session.refresh(job)
        return job
    
    async def update_chunk_status(
        self,
        job_id: int,
        active_delta: int = 0,
        completed_delta: int = 0,
        failed_delta: int = 0
    ) -> Optional[CrawlJob]:
        """
        Update chunk tracking counters.
        
        Args:
            job_id: Job ID
            active_delta: Change in active chunks (can be negative)
            completed_delta: Change in completed chunks
            failed_delta: Change in failed chunks
        
        Returns:
            Updated job or None if not found
        """
        job = await self.get_by_id(job_id)
        if not job:
            return None
        
        job.active_chunks = max(0, job.active_chunks + active_delta)
        job.completed_chunks += completed_delta
        job.failed_chunks += failed_delta
        
        await self.session.commit()
        await self.session.refresh(job)
        return job
    
    async def mark_completed(self, job_id: int) -> Optional[CrawlJob]:
        """
        Mark job as completed.
        
        Args:
            job_id: Job ID
        
        Returns:
            Updated job or None if not found
        """
        job = await self.get_by_id(job_id)
        if not job:
            return None
        
        from datetime import datetime
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        job.progress = 100
        
        await self.session.commit()
        await self.session.refresh(job)
        return job
    
    async def mark_failed(self, job_id: int, error: Optional[str] = None) -> Optional[CrawlJob]:
        """
        Mark job as failed.
        
        Args:
            job_id: Job ID
            error: Error message (optional)
        
        Returns:
            Updated job or None if not found
        """
        job = await self.get_by_id(job_id)
        if not job:
            return None
        
        from datetime import datetime
        job.status = "failed"
        job.completed_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(job)
        return job
