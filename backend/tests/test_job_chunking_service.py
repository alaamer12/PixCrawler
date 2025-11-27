"""
Tests for Job Chunking Service.

This module provides comprehensive tests for the JobChunkingService,
including chunk creation, status management, and progress tracking.

Test Classes:
    TestJobChunkingService: Tests for chunking operations
    TestChunkStatusManagement: Tests for status tracking
    TestChunkStatistics: Tests for progress tracking
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import CrawlJob, JobChunk
from backend.repositories import JobChunkRepository, CrawlJobRepository
from backend.services.job_chunking import JobChunkingService, CHUNK_SIZE
from backend.core.exceptions import NotFoundError, ValidationError
from backend.schemas.job_chunks import JobChunkStatus


class TestJobChunkingService:
    """Tests for job chunking operations."""

    @pytest.fixture
    async def service(self, session: AsyncSession):
        """Create a JobChunkingService instance."""
        chunk_repo = JobChunkRepository(session)
        job_repo = CrawlJobRepository(session)
        return JobChunkingService(chunk_repo, job_repo, session)

    @pytest.fixture
    async def sample_job(self, session: AsyncSession):
        """Create a sample crawl job."""
        job = CrawlJob(
            project_id=1,
            name="Test Job",
            keywords={"keywords": ["test"]},
            max_images=2500,
            status="pending",
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        return job

    @pytest.mark.asyncio
    async def test_create_chunks_for_job_single_chunk(
        self,
        service: JobChunkingService,
        session: AsyncSession,
    ):
        """Test creating chunks for a job with less than 500 images."""
        # Create a job with 250 images
        job = CrawlJob(
            project_id=1,
            name="Small Job",
            keywords={"keywords": ["test"]},
            max_images=250,
            status="pending",
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)

        # Create chunks
        chunks = await service.create_chunks_for_job(
            job_id=job.id,
            max_images=250,
            priority=5,
        )

        # Verify single chunk created
        assert len(chunks) == 1
        assert chunks[0].job_id == job.id
        assert chunks[0].chunk_index == 0
        assert chunks[0].status == JobChunkStatus.PENDING.value
        assert chunks[0].priority == 5
        assert chunks[0].image_range["start"] == 0
        assert chunks[0].image_range["end"] == 249

    @pytest.mark.asyncio
    async def test_create_chunks_for_job_multiple_chunks(
        self,
        service: JobChunkingService,
        session: AsyncSession,
    ):
        """Test creating chunks for a job with multiple chunks."""
        # Create a job with 2500 images
        job = CrawlJob(
            project_id=1,
            name="Large Job",
            keywords={"keywords": ["test"]},
            max_images=2500,
            status="pending",
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)

        # Create chunks
        chunks = await service.create_chunks_for_job(
            job_id=job.id,
            max_images=2500,
            priority=7,
        )

        # Verify 5 chunks created (2500 / 500)
        assert len(chunks) == 5

        # Verify chunk properties
        for i, chunk in enumerate(chunks):
            assert chunk.job_id == job.id
            assert chunk.chunk_index == i
            assert chunk.status == JobChunkStatus.PENDING.value
            assert chunk.priority == 7
            assert chunk.image_range["start"] == i * CHUNK_SIZE
            assert chunk.image_range["end"] == min(
                (i + 1) * CHUNK_SIZE - 1, 2499
            )

    @pytest.mark.asyncio
    async def test_create_chunks_for_job_exact_boundary(
        self,
        service: JobChunkingService,
        session: AsyncSession,
    ):
        """Test creating chunks when max_images is exact multiple of CHUNK_SIZE."""
        # Create a job with exactly 1000 images
        job = CrawlJob(
            project_id=1,
            name="Boundary Job",
            keywords={"keywords": ["test"]},
            max_images=1000,
            status="pending",
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)

        # Create chunks
        chunks = await service.create_chunks_for_job(
            job_id=job.id,
            max_images=1000,
            priority=5,
        )

        # Verify 2 chunks created
        assert len(chunks) == 2
        assert chunks[0].image_range["end"] == 499
        assert chunks[1].image_range["end"] == 999

    @pytest.mark.asyncio
    async def test_create_chunks_job_not_found(
        self,
        service: JobChunkingService,
    ):
        """Test creating chunks for non-existent job."""
        with pytest.raises(NotFoundError):
            await service.create_chunks_for_job(
                job_id=9999,
                max_images=1000,
                priority=5,
            )

    @pytest.mark.asyncio
    async def test_create_chunks_invalid_max_images(
        self,
        service: JobChunkingService,
        sample_job: CrawlJob,
    ):
        """Test creating chunks with invalid max_images."""
        with pytest.raises(ValidationError):
            await service.create_chunks_for_job(
                job_id=sample_job.id,
                max_images=0,
                priority=5,
            )

        with pytest.raises(ValidationError):
            await service.create_chunks_for_job(
                job_id=sample_job.id,
                max_images=-100,
                priority=5,
            )

    @pytest.mark.asyncio
    async def test_create_chunks_invalid_priority(
        self,
        service: JobChunkingService,
        sample_job: CrawlJob,
    ):
        """Test creating chunks with invalid priority."""
        with pytest.raises(ValidationError):
            await service.create_chunks_for_job(
                job_id=sample_job.id,
                max_images=1000,
                priority=-1,
            )

        with pytest.raises(ValidationError):
            await service.create_chunks_for_job(
                job_id=sample_job.id,
                max_images=1000,
                priority=11,
            )


class TestChunkStatusManagement:
    """Tests for chunk status management."""

    @pytest.fixture
    async def service_with_chunks(self, session: AsyncSession):
        """Create a service with sample chunks."""
        # Create job
        job = CrawlJob(
            project_id=1,
            name="Test Job",
            keywords={"keywords": ["test"]},
            max_images=1500,
            status="pending",
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)

        # Create service
        chunk_repo = JobChunkRepository(session)
        job_repo = CrawlJobRepository(session)
        service = JobChunkingService(chunk_repo, job_repo, session)

        # Create chunks
        chunks = await service.create_chunks_for_job(
            job_id=job.id,
            max_images=1500,
            priority=5,
        )

        return service, job, chunks

    @pytest.mark.asyncio
    async def test_mark_chunk_processing(
        self,
        service_with_chunks,
    ):
        """Test marking a chunk as processing."""
        service, job, chunks = service_with_chunks

        chunk = chunks[0]
        updated = await service.mark_chunk_processing(
            chunk_id=chunk.id,
            task_id="task-123",
        )

        assert updated is not None
        assert updated.status == JobChunkStatus.PROCESSING.value
        assert updated.task_id == "task-123"

    @pytest.mark.asyncio
    async def test_mark_chunk_completed(
        self,
        service_with_chunks,
    ):
        """Test marking a chunk as completed."""
        service, job, chunks = service_with_chunks

        chunk = chunks[0]
        updated = await service.mark_chunk_completed(chunk_id=chunk.id)

        assert updated is not None
        assert updated.status == JobChunkStatus.COMPLETED.value

    @pytest.mark.asyncio
    async def test_mark_chunk_failed(
        self,
        service_with_chunks,
    ):
        """Test marking a chunk as failed."""
        service, job, chunks = service_with_chunks

        chunk = chunks[0]
        error_msg = "Connection timeout"
        updated = await service.mark_chunk_failed(
            chunk_id=chunk.id,
            error_message=error_msg,
        )

        assert updated is not None
        assert updated.status == JobChunkStatus.FAILED.value
        assert updated.error_message == error_msg

    @pytest.mark.asyncio
    async def test_retry_chunk(
        self,
        service_with_chunks,
    ):
        """Test retrying a failed chunk."""
        service, job, chunks = service_with_chunks

        chunk = chunks[0]

        # Mark as failed
        await service.mark_chunk_failed(
            chunk_id=chunk.id,
            error_message="Error",
        )

        # Retry
        updated = await service.retry_chunk(chunk_id=chunk.id)

        assert updated is not None
        assert updated.status == JobChunkStatus.PENDING.value
        assert updated.retry_count == 1

    @pytest.mark.asyncio
    async def test_update_chunk_status_invalid_status(
        self,
        service_with_chunks,
    ):
        """Test updating chunk with invalid status."""
        service, job, chunks = service_with_chunks

        with pytest.raises(ValidationError):
            await service.update_chunk_status(
                chunk_id=chunks[0].id,
                status="invalid_status",
            )


class TestChunkStatistics:
    """Tests for chunk statistics and progress tracking."""

    @pytest.fixture
    async def service_with_mixed_chunks(self, session: AsyncSession):
        """Create a service with chunks in different statuses."""
        # Create job
        job = CrawlJob(
            project_id=1,
            name="Test Job",
            keywords={"keywords": ["test"]},
            max_images=2000,
            status="pending",
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)

        # Create service
        chunk_repo = JobChunkRepository(session)
        job_repo = CrawlJobRepository(session)
        service = JobChunkingService(chunk_repo, job_repo, session)

        # Create chunks
        chunks = await service.create_chunks_for_job(
            job_id=job.id,
            max_images=2000,
            priority=5,
        )

        # Set different statuses
        await service.mark_chunk_processing(chunk_id=chunks[0].id)
        await service.mark_chunk_completed(chunk_id=chunks[1].id)
        await service.mark_chunk_failed(chunk_id=chunks[2].id)
        # chunks[3] remains pending

        return service, job, chunks

    @pytest.mark.asyncio
    async def test_get_chunk_statistics(
        self,
        service_with_mixed_chunks,
    ):
        """Test getting chunk statistics."""
        service, job, chunks = service_with_mixed_chunks

        stats = await service.get_chunk_statistics(job_id=job.id)

        assert stats.job_id == job.id
        assert stats.total == 4
        assert stats.pending == 1
        assert stats.processing == 1
        assert stats.completed == 1
        assert stats.failed == 1

    @pytest.mark.asyncio
    async def test_get_pending_chunks(
        self,
        service_with_mixed_chunks,
    ):
        """Test getting pending chunks."""
        service, job, chunks = service_with_mixed_chunks

        pending = await service.get_pending_chunks(job_id=job.id)

        assert len(pending) == 1
        assert pending[0].status == JobChunkStatus.PENDING.value

    @pytest.mark.asyncio
    async def test_get_processing_chunks(
        self,
        service_with_mixed_chunks,
    ):
        """Test getting processing chunks."""
        service, job, chunks = service_with_mixed_chunks

        processing = await service.get_processing_chunks(job_id=job.id)

        assert len(processing) == 1
        assert processing[0].status == JobChunkStatus.PROCESSING.value

    @pytest.mark.asyncio
    async def test_get_completed_chunks(
        self,
        service_with_mixed_chunks,
    ):
        """Test getting completed chunks."""
        service, job, chunks = service_with_mixed_chunks

        completed = await service.get_completed_chunks(job_id=job.id)

        assert len(completed) == 1
        assert completed[0].status == JobChunkStatus.COMPLETED.value

    @pytest.mark.asyncio
    async def test_get_failed_chunks(
        self,
        service_with_mixed_chunks,
    ):
        """Test getting failed chunks."""
        service, job, chunks = service_with_mixed_chunks

        failed = await service.get_failed_chunks(job_id=job.id)

        assert len(failed) == 1
        assert failed[0].status == JobChunkStatus.FAILED.value

    @pytest.mark.asyncio
    async def test_get_next_pending_chunk(
        self,
        service_with_mixed_chunks,
    ):
        """Test getting next pending chunk."""
        service, job, chunks = service_with_mixed_chunks

        next_chunk = await service.get_next_pending_chunk(job_id=job.id)

        assert next_chunk is not None
        assert next_chunk.status == JobChunkStatus.PENDING.value

    @pytest.mark.asyncio
    async def test_check_job_completion_incomplete(
        self,
        service_with_mixed_chunks,
    ):
        """Test checking job completion when not complete."""
        service, job, chunks = service_with_mixed_chunks

        is_complete = await service.check_job_completion(job_id=job.id)

        assert is_complete is False

    @pytest.mark.asyncio
    async def test_check_job_completion_complete(
        self,
        service_with_mixed_chunks,
    ):
        """Test checking job completion when complete."""
        service, job, chunks = service_with_mixed_chunks

        # Mark all chunks as completed
        for chunk in chunks:
            await service.mark_chunk_completed(chunk_id=chunk.id)

        is_complete = await service.check_job_completion(job_id=job.id)

        assert is_complete is True

    @pytest.mark.asyncio
    async def test_get_job_chunk_progress(
        self,
        service_with_mixed_chunks,
    ):
        """Test getting job chunk progress."""
        service, job, chunks = service_with_mixed_chunks

        progress = await service.get_job_chunk_progress(job_id=job.id)

        assert progress['job_id'] == job.id
        assert progress['total_chunks'] == 4
        assert progress['pending_chunks'] == 1
        assert progress['processing_chunks'] == 1
        assert progress['completed_chunks'] == 1
        assert progress['failed_chunks'] == 1
        assert progress['completion_percentage'] == 25.0
        assert progress['is_complete'] is False
