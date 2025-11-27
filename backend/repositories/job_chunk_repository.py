"""
JobChunk repository for data access operations.

This module provides the repository pattern implementation for JobChunk model,
handling all database queries and data access logic for job chunks.

Classes:
    JobChunkRepository: Repository for JobChunk CRUD and queries

Features:
    - CRUD operations via BaseRepository
    - Chunk status queries and filtering
    - Bulk chunk creation
    - Progress tracking queries
"""

from typing import List, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import JobChunk
from .base import BaseRepository

__all__ = ['JobChunkRepository']


class JobChunkRepository(BaseRepository[JobChunk]):
    """
    Repository for JobChunk data access.
    
    Provides database operations for job chunks including CRUD,
    filtering, and progress tracking queries.
    
    Attributes:
        session: Database session
        model: JobChunk model class
    
    Example:
        >>> repo = JobChunkRepository(session)
        >>> chunks = await repo.get_by_job(job_id=1)
        >>> chunk = await repo.get_by_id(chunk_id=1)
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize JobChunk repository.
        
        Args:
            session: Database session
        """
        super().__init__(session, JobChunk)
    
    async def get_by_job(self, job_id: int) -> List[JobChunk]:
        """
        Get all chunks for a specific job.
        
        Args:
            job_id: Job ID
        
        Returns:
            List of job chunks ordered by chunk_index
        """
        result = await self.session.execute(
            select(JobChunk)
            .where(JobChunk.job_id == job_id)
            .order_by(JobChunk.chunk_index)
        )
        return list(result.scalars().all())
    
    async def get_by_status(self, status: str) -> List[JobChunk]:
        """
        Get all chunks with specific status.
        
        Args:
            status: Chunk status (pending, processing, completed, failed)
        
        Returns:
            List of job chunks
        """
        result = await self.session.execute(
            select(JobChunk).where(JobChunk.status == status)
        )
        return list(result.scalars().all())
    
    async def get_by_job_and_status(self, job_id: int, status: str) -> List[JobChunk]:
        """
        Get chunks for a job with specific status.
        
        Args:
            job_id: Job ID
            status: Chunk status
        
        Returns:
            List of job chunks
        """
        result = await self.session.execute(
            select(JobChunk)
            .where(and_(JobChunk.job_id == job_id, JobChunk.status == status))
            .order_by(JobChunk.chunk_index)
        )
        return list(result.scalars().all())
    
    async def get_pending_chunks(self, job_id: int) -> List[JobChunk]:
        """
        Get all pending chunks for a job.
        
        Args:
            job_id: Job ID
        
        Returns:
            List of pending chunks
        """
        return await self.get_by_job_and_status(job_id, "pending")
    
    async def get_processing_chunks(self, job_id: int) -> List[JobChunk]:
        """
        Get all processing chunks for a job.
        
        Args:
            job_id: Job ID
        
        Returns:
            List of processing chunks
        """
        return await self.get_by_job_and_status(job_id, "processing")
    
    async def get_completed_chunks(self, job_id: int) -> List[JobChunk]:
        """
        Get all completed chunks for a job.
        
        Args:
            job_id: Job ID
        
        Returns:
            List of completed chunks
        """
        return await self.get_by_job_and_status(job_id, "completed")
    
    async def get_failed_chunks(self, job_id: int) -> List[JobChunk]:
        """
        Get all failed chunks for a job.
        
        Args:
            job_id: Job ID
        
        Returns:
            List of failed chunks
        """
        return await self.get_by_job_and_status(job_id, "failed")
    
    async def count_by_status(self, job_id: int, status: str) -> int:
        """
        Count chunks for a job with specific status.
        
        Args:
            job_id: Job ID
            status: Chunk status
        
        Returns:
            Count of chunks
        """
        result = await self.session.execute(
            select(func.count(JobChunk.id))
            .where(and_(JobChunk.job_id == job_id, JobChunk.status == status))
        )
        return result.scalar() or 0
    
    async def get_chunk_statistics(self, job_id: int) -> dict:
        """
        Get chunk statistics for a job.
        
        Args:
            job_id: Job ID
        
        Returns:
            Dictionary with chunk counts by status
        """
        result = await self.session.execute(
            select(
                JobChunk.status,
                func.count(JobChunk.id).label('count')
            )
            .where(JobChunk.job_id == job_id)
            .group_by(JobChunk.status)
        )
        
        stats = {
            'pending': 0,
            'processing': 0,
            'completed': 0,
            'failed': 0,
            'total': 0
        }
        
        for status, count in result.all():
            if status in stats:
                stats[status] = count
            stats['total'] += count
        
        return stats
    
    async def bulk_create(self, chunks_data: List[dict]) -> List[JobChunk]:
        """
        Create multiple chunks in bulk.
        
        Args:
            chunks_data: List of chunk data dictionaries
        
        Returns:
            List of created chunks
        """
        chunks = [JobChunk(**data) for data in chunks_data]
        self.session.add_all(chunks)
        await self.session.commit()
        
        # Refresh all instances to get IDs and timestamps
        for chunk in chunks:
            await self.session.refresh(chunk)
        
        return chunks
    
    async def update_status(
        self,
        chunk_id: int,
        status: str,
        error_message: Optional[str] = None
    ) -> Optional[JobChunk]:
        """
        Update chunk status.
        
        Args:
            chunk_id: Chunk ID
            status: New status
            error_message: Optional error message
        
        Returns:
            Updated chunk or None if not found
        """
        chunk = await self.get_by_id(chunk_id)
        if not chunk:
            return None
        
        chunk.status = status
        if error_message:
            chunk.error_message = error_message
        
        await self.session.commit()
        await self.session.refresh(chunk)
        return chunk
    
    async def increment_retry_count(self, chunk_id: int) -> Optional[JobChunk]:
        """
        Increment retry count for a chunk.
        
        Args:
            chunk_id: Chunk ID
        
        Returns:
            Updated chunk or None if not found
        """
        chunk = await self.get_by_id(chunk_id)
        if not chunk:
            return None
        
        chunk.retry_count += 1
        await self.session.commit()
        await self.session.refresh(chunk)
        return chunk
    
    async def set_task_id(self, chunk_id: int, task_id: str) -> Optional[JobChunk]:
        """
        Set Celery task ID for a chunk.
        
        Args:
            chunk_id: Chunk ID
            task_id: Celery task ID
        
        Returns:
            Updated chunk or None if not found
        """
        chunk = await self.get_by_id(chunk_id)
        if not chunk:
            return None
        
        chunk.task_id = task_id
        await self.session.commit()
        await self.session.refresh(chunk)
        return chunk
    
    async def delete_by_job(self, job_id: int) -> int:
        """
        Delete all chunks for a job.
        
        Args:
            job_id: Job ID
        
        Returns:
            Number of deleted chunks
        """
        result = await self.session.execute(
            select(func.count(JobChunk.id))
            .where(JobChunk.job_id == job_id)
        )
        count = result.scalar() or 0
        
        await self.session.execute(
            select(JobChunk).where(JobChunk.job_id == job_id)
        )
        
        await self.session.commit()
        return count
