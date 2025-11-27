"""
Job chunking service for splitting jobs into manageable chunks.

This module provides services for splitting crawl jobs into 500-image chunks,
managing chunk metadata, and tracking chunk processing status.

Classes:
    JobChunkingService: Service for job chunking operations

Features:
    - Split jobs into 500-image chunks
    - Store chunk metadata in database
    - Track chunk status (PENDING, PROCESSING, COMPLETED, FAILED)
    - Priority inheritance from parent job
    - Bulk chunk creation
    - Chunk statistics and progress tracking
"""

import math
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundError, ValidationError
from backend.models import CrawlJob, JobChunk
from backend.repositories import (
    JobChunkRepository,
    CrawlJobRepository,
)
from backend.schemas.job_chunks import (
    JobChunkCreate,
    JobChunkStatus,
    JobChunkStatistics,
)
from .base import BaseService

__all__ = ['JobChunkingService']

# Chunk size constant: 500 images per chunk
CHUNK_SIZE = 500


class JobChunkingService(BaseService):
    """
    Service for managing job chunking operations.

    Provides functionality for splitting crawl jobs into chunks,
    managing chunk metadata, and tracking processing status.

    Attributes:
        chunk_repo: JobChunk repository
        job_repo: CrawlJob repository
    """

    def __init__(
        self,
        chunk_repo: JobChunkRepository,
        job_repo: CrawlJobRepository,
        session: Optional[AsyncSession] = None
    ) -> None:
        """
        Initialize job chunking service with repositories.

        Args:
            chunk_repo: JobChunk repository
            job_repo: CrawlJob repository
            session: Optional database session
        """
        super().__init__()
        self.chunk_repo = chunk_repo
        self.job_repo = job_repo
        self._session = session

    async def create_chunks_for_job(
        self,
        job_id: int,
        max_images: int,
        priority: int = 5
    ) -> List[JobChunk]:
        """
        Create chunks for a job based on max_images.

        Splits the job into 500-image chunks and creates chunk records
        in the database. Each chunk inherits the priority from the job.

        Args:
            job_id: ID of the job to chunk
            max_images: Maximum number of images for the job
            priority: Priority level (0-10) to assign to chunks

        Returns:
            List of created JobChunk records

        Raises:
            NotFoundError: If job not found
            ValidationError: If max_images is invalid

        Example:
            >>> chunks = await service.create_chunks_for_job(
            ...     job_id=1,
            ...     max_images=2500,
            ...     priority=7
            ... )
            >>> len(chunks)  # Should be 5 chunks (2500 / 500)
            5
        """
        # Validate job exists
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError(f"Job not found: {job_id}")

        # Validate max_images
        if max_images <= 0:
            raise ValidationError("max_images must be greater than 0")

        if priority < 0 or priority > 10:
            raise ValidationError("priority must be between 0 and 10")

        # Calculate number of chunks needed
        num_chunks = math.ceil(max_images / CHUNK_SIZE)

        # Generate chunk data
        chunks_data = []
        for chunk_index in range(num_chunks):
            start_image = chunk_index * CHUNK_SIZE
            end_image = min((chunk_index + 1) * CHUNK_SIZE - 1, max_images - 1)

            chunk_data = {
                'job_id': job_id,
                'chunk_index': chunk_index,
                'status': JobChunkStatus.PENDING.value,
                'priority': priority,
                'image_range': {
                    'start': start_image,
                    'end': end_image,
                },
                'retry_count': 0,
            }
            chunks_data.append(chunk_data)

        # Create chunks in bulk
        chunks = await self.chunk_repo.bulk_create(chunks_data)

        # Update job with chunk tracking info
        await self.job_repo.update(
            job,
            total_chunks=num_chunks,
            active_chunks=num_chunks,
        )

        self.log_operation(
            "create_chunks_for_job",
            job_id=job_id,
            num_chunks=num_chunks,
            max_images=max_images,
        )

        return chunks

    async def get_chunks_for_job(self, job_id: int) -> List[JobChunk]:
        """
        Get all chunks for a job.

        Args:
            job_id: Job ID

        Returns:
            List of JobChunk records ordered by chunk_index
        """
        return await self.chunk_repo.get_by_job(job_id)

    async def get_chunk_by_id(self, chunk_id: int) -> Optional[JobChunk]:
        """
        Get a chunk by ID.

        Args:
            chunk_id: Chunk ID

        Returns:
            JobChunk record or None if not found
        """
        return await self.chunk_repo.get_by_id(chunk_id)

    async def update_chunk_status(
        self,
        chunk_id: int,
        status: str,
        error_message: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> Optional[JobChunk]:
        """
        Update chunk status and optionally set error message.

        Args:
            chunk_id: Chunk ID
            status: New status (pending, processing, completed, failed)
            error_message: Optional error message if failed
            task_id: Optional Celery task ID

        Returns:
            Updated JobChunk or None if not found

        Raises:
            ValidationError: If status is invalid
        """
        # Validate status
        valid_statuses = {s.value for s in JobChunkStatus}
        if status not in valid_statuses:
            raise ValidationError(
                f"Invalid status '{status}'. Must be one of: {valid_statuses}"
            )

        chunk = await self.chunk_repo.update_status(
            chunk_id,
            status,
            error_message,
        )

        if chunk and task_id:
            await self.chunk_repo.set_task_id(chunk_id, task_id)
            chunk.task_id = task_id

        if chunk:
            self.log_operation(
                "update_chunk_status",
                chunk_id=chunk_id,
                status=status,
                error_message=error_message,
            )

        return chunk

    async def mark_chunk_processing(
        self,
        chunk_id: int,
        task_id: Optional[str] = None,
    ) -> Optional[JobChunk]:
        """
        Mark a chunk as processing.

        Args:
            chunk_id: Chunk ID
            task_id: Optional Celery task ID

        Returns:
            Updated JobChunk or None if not found
        """
        return await self.update_chunk_status(
            chunk_id,
            JobChunkStatus.PROCESSING.value,
            task_id=task_id,
        )

    async def mark_chunk_completed(self, chunk_id: int) -> Optional[JobChunk]:
        """
        Mark a chunk as completed.

        Args:
            chunk_id: Chunk ID

        Returns:
            Updated JobChunk or None if not found
        """
        return await self.update_chunk_status(
            chunk_id,
            JobChunkStatus.COMPLETED.value,
        )

    async def mark_chunk_failed(
        self,
        chunk_id: int,
        error_message: Optional[str] = None,
    ) -> Optional[JobChunk]:
        """
        Mark a chunk as failed.

        Args:
            chunk_id: Chunk ID
            error_message: Optional error message

        Returns:
            Updated JobChunk or None if not found
        """
        return await self.update_chunk_status(
            chunk_id,
            JobChunkStatus.FAILED.value,
            error_message=error_message,
        )

    async def retry_chunk(self, chunk_id: int) -> Optional[JobChunk]:
        """
        Retry a failed chunk by resetting status to pending and incrementing retry count.

        Args:
            chunk_id: Chunk ID

        Returns:
            Updated JobChunk or None if not found
        """
        chunk = await self.chunk_repo.get_by_id(chunk_id)
        if not chunk:
            return None

        # Increment retry count
        await self.chunk_repo.increment_retry_count(chunk_id)

        # Reset status to pending
        chunk = await self.update_chunk_status(
            chunk_id,
            JobChunkStatus.PENDING.value,
        )

        self.log_operation(
            "retry_chunk",
            chunk_id=chunk_id,
        )

        return chunk

    async def get_chunk_statistics(self, job_id: int) -> JobChunkStatistics:
        """
        Get statistics for all chunks in a job.

        Args:
            job_id: Job ID

        Returns:
            JobChunkStatistics with counts by status
        """
        stats_dict = await self.chunk_repo.get_chunk_statistics(job_id)

        return JobChunkStatistics(
            job_id=job_id,
            total=stats_dict['total'],
            pending=stats_dict['pending'],
            processing=stats_dict['processing'],
            completed=stats_dict['completed'],
            failed=stats_dict['failed'],
        )

    async def get_pending_chunks(self, job_id: int) -> List[JobChunk]:
        """
        Get all pending chunks for a job.

        Args:
            job_id: Job ID

        Returns:
            List of pending JobChunk records
        """
        return await self.chunk_repo.get_pending_chunks(job_id)

    async def get_processing_chunks(self, job_id: int) -> List[JobChunk]:
        """
        Get all processing chunks for a job.

        Args:
            job_id: Job ID

        Returns:
            List of processing JobChunk records
        """
        return await self.chunk_repo.get_processing_chunks(job_id)

    async def get_completed_chunks(self, job_id: int) -> List[JobChunk]:
        """
        Get all completed chunks for a job.

        Args:
            job_id: Job ID

        Returns:
            List of completed JobChunk records
        """
        return await self.chunk_repo.get_completed_chunks(job_id)

    async def get_failed_chunks(self, job_id: int) -> List[JobChunk]:
        """
        Get all failed chunks for a job.

        Args:
            job_id: Job ID

        Returns:
            List of failed JobChunk records
        """
        return await self.chunk_repo.get_failed_chunks(job_id)

    async def get_next_pending_chunk(self, job_id: int) -> Optional[JobChunk]:
        """
        Get the next pending chunk for a job (by priority and creation order).

        Args:
            job_id: Job ID

        Returns:
            Next pending JobChunk or None if no pending chunks
        """
        pending_chunks = await self.get_pending_chunks(job_id)
        if not pending_chunks:
            return None

        # Sort by priority (descending) then by chunk_index (ascending)
        sorted_chunks = sorted(
            pending_chunks,
            key=lambda c: (-c.priority, c.chunk_index),
        )

        return sorted_chunks[0]

    async def update_job_chunk_tracking(
        self,
        job_id: int,
        active_delta: int = 0,
        completed_delta: int = 0,
        failed_delta: int = 0,
    ) -> Optional[CrawlJob]:
        """
        Update job chunk tracking counters.

        Args:
            job_id: Job ID
            active_delta: Change in active chunks (can be negative)
            completed_delta: Change in completed chunks
            failed_delta: Change in failed chunks

        Returns:
            Updated CrawlJob or None if not found
        """
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            return None

        job.active_chunks = max(0, job.active_chunks + active_delta)
        job.completed_chunks += completed_delta
        job.failed_chunks += failed_delta

        await self._session.commit()
        await self._session.refresh(job)

        self.log_operation(
            "update_job_chunk_tracking",
            job_id=job_id,
            active_delta=active_delta,
            completed_delta=completed_delta,
            failed_delta=failed_delta,
        )

        return job

    async def check_job_completion(self, job_id: int) -> bool:
        """
        Check if all chunks for a job are completed.

        Args:
            job_id: Job ID

        Returns:
            True if all chunks are completed, False otherwise
        """
        stats = await self.get_chunk_statistics(job_id)
        return stats.total > 0 and stats.completed == stats.total

    async def get_job_chunk_progress(self, job_id: int) -> Dict[str, Any]:
        """
        Get detailed progress information for a job's chunks.

        Args:
            job_id: Job ID

        Returns:
            Dictionary with progress information
        """
        stats = await self.get_chunk_statistics(job_id)

        completion_percentage = stats.completion_percentage
        success_rate = stats.success_rate

        return {
            'job_id': job_id,
            'total_chunks': stats.total,
            'pending_chunks': stats.pending,
            'processing_chunks': stats.processing,
            'completed_chunks': stats.completed,
            'failed_chunks': stats.failed,
            'completion_percentage': completion_percentage,
            'success_rate': success_rate,
            'is_complete': completion_percentage == 100.0,
            'timestamp': datetime.utcnow().isoformat(),
        }
