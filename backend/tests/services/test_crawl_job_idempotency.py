"""
Tests for crawl job service idempotency and deduplication features.

Tests cover:
- Job start idempotency (Requirement 11.1)
- Job stop idempotency (Requirement 11.2)
- Result deduplication (Requirement 11.3)
- Retry counter reset (Requirement 11.4)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from backend.core.exceptions import NotFoundError, ValidationError
from backend.models import CrawlJob, Project
from backend.services.crawl_job import CrawlJobService


@pytest.fixture
def mock_repositories():
    """Create mock repositories."""
    return {
        'crawl_job_repo': AsyncMock(),
        'project_repo': AsyncMock(),
        'image_repo': AsyncMock(),
        'activity_log_repo': AsyncMock()
    }


@pytest.fixture
def crawl_job_service(mock_repositories):
    """Create crawl job service with mocked repositories."""
    return CrawlJobService(
        crawl_job_repo=mock_repositories['crawl_job_repo'],
        project_repo=mock_repositories['project_repo'],
        image_repo=mock_repositories['image_repo'],
        activity_log_repo=mock_repositories['activity_log_repo']
    )


@pytest.fixture
def sample_project():
    """Create sample project."""
    user_id = uuid4()
    return Project(
        id=1,
        name="Test Project",
        user_id=user_id,
        status="active"
    )


@pytest.fixture
def pending_job():
    """Create a pending crawl job."""
    return CrawlJob(
        id=1,
        project_id=1,
        name="Test Job",
        keywords={"keywords": ["laptop", "computer"]},
        max_images=1000,
        status="pending",
        progress=0,
        total_chunks=0,
        active_chunks=0,
        completed_chunks=0,
        failed_chunks=0,
        task_ids=[]
    )


@pytest.fixture
def running_job():
    """Create a running crawl job."""
    return CrawlJob(
        id=1,
        project_id=1,
        name="Test Job",
        keywords={"keywords": ["laptop", "computer"]},
        max_images=1000,
        status="running",
        progress=50,
        total_chunks=6,
        active_chunks=3,
        completed_chunks=3,
        failed_chunks=0,
        task_ids=["task-1", "task-2", "task-3", "task-4", "task-5", "task-6"]
    )


@pytest.fixture
def completed_job():
    """Create a completed crawl job."""
    return CrawlJob(
        id=1,
        project_id=1,
        name="Test Job",
        keywords={"keywords": ["laptop", "computer"]},
        max_images=1000,
        status="completed",
        progress=100,
        total_chunks=6,
        active_chunks=0,
        completed_chunks=6,
        failed_chunks=0,
        task_ids=["task-1", "task-2", "task-3", "task-4", "task-5", "task-6"]
    )


@pytest.fixture
def failed_job():
    """Create a failed crawl job."""
    return CrawlJob(
        id=1,
        project_id=1,
        name="Test Job",
        keywords={"keywords": ["laptop", "computer"]},
        max_images=1000,
        status="failed",
        progress=50,
        total_chunks=6,
        active_chunks=0,
        completed_chunks=3,
        failed_chunks=3,
        task_ids=["task-1", "task-2", "task-3", "task-4", "task-5", "task-6"]
    )


class TestJobStartIdempotency:
    """Tests for job start idempotency (Requirement 11.1)."""

    @pytest.mark.asyncio
    async def test_start_already_running_job_returns_existing_tasks(
        self,
        crawl_job_service,
        mock_repositories,
        running_job,
        sample_project
    ):
        """Test that starting an already running job returns existing task IDs."""
        # Setup mocks
        mock_repositories['crawl_job_repo'].get_by_id.return_value = running_job
        mock_repositories['crawl_job_repo'].get_active_tasks.return_value = running_job.task_ids
        mock_repositories['project_repo'].get_by_id.return_value = sample_project
        
        user_id = str(sample_project.user_id)
        
        # Call start_job on already running job
        result = await crawl_job_service.start_job(
            job_id=running_job.id,
            user_id=user_id
        )
        
        # Verify idempotent response
        assert result["status"] == "running"
        assert result["task_ids"] == running_job.task_ids
        assert result["total_chunks"] == running_job.total_chunks
        assert "idempotent" in result["message"].lower()
        
        # Verify no new tasks were dispatched
        mock_repositories['crawl_job_repo'].add_task_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_start_completed_job_raises_validation_error(
        self,
        crawl_job_service,
        mock_repositories,
        completed_job,
        sample_project
    ):
        """Test that starting a completed job raises ValidationError."""
        # Setup mocks
        mock_repositories['crawl_job_repo'].get_by_id.return_value = completed_job
        mock_repositories['project_repo'].get_by_id.return_value = sample_project
        
        user_id = str(sample_project.user_id)
        
        # Attempt to start completed job
        with pytest.raises(ValidationError) as exc_info:
            await crawl_job_service.start_job(
                job_id=completed_job.id,
                user_id=user_id
            )
        
        assert "cannot start job" in str(exc_info.value).lower()
        assert "completed" in str(exc_info.value).lower()


class TestJobStopIdempotency:
    """Tests for job stop idempotency (Requirement 11.2)."""

    @pytest.mark.asyncio
    async def test_cancel_already_cancelled_job_returns_success(
        self,
        crawl_job_service,
        mock_repositories
    ):
        """Test that cancelling an already cancelled job returns success without side effects."""
        cancelled_job = CrawlJob(
            id=1,
            project_id=1,
            name="Test Job",
            status="cancelled",
            task_ids=[]
        )
        
        # Setup mocks
        mock_repositories['crawl_job_repo'].get_by_id.return_value = cancelled_job
        
        # Call cancel_job on already cancelled job
        result = await crawl_job_service.cancel_job(
            job_id=cancelled_job.id,
            user_id=str(uuid4())
        )
        
        # Verify idempotent response
        assert result["status"] == "cancelled"
        assert result["revoked_tasks"] == 0
        assert "idempotent" in result["message"].lower()
        
        # Verify no tasks were revoked
        assert not hasattr(crawl_job_service, '_revoke_celery_tasks') or \
               crawl_job_service._revoke_celery_tasks.call_count == 0

    @pytest.mark.asyncio
    async def test_cancel_completed_job_returns_success(
        self,
        crawl_job_service,
        mock_repositories,
        completed_job
    ):
        """Test that cancelling a completed job returns success without side effects."""
        # Setup mocks
        mock_repositories['crawl_job_repo'].get_by_id.return_value = completed_job
        
        # Call cancel_job on completed job
        result = await crawl_job_service.cancel_job(
            job_id=completed_job.id,
            user_id=str(uuid4())
        )
        
        # Verify idempotent response
        assert result["status"] == "completed"
        assert result["revoked_tasks"] == 0
        assert "idempotent" in result["message"].lower()


class TestResultDeduplication:
    """Tests for result deduplication (Requirement 11.3)."""

    @pytest.mark.asyncio
    async def test_duplicate_task_result_ignored(
        self,
        crawl_job_service,
        mock_repositories
    ):
        """Test that duplicate task results are ignored."""
        # Create a job where all chunks are already processed
        job = CrawlJob(
            id=1,
            project_id=1,
            name="Test Job",
            status="running",
            total_chunks=3,
            active_chunks=0,
            completed_chunks=3,
            failed_chunks=0
        )
        
        # Setup mocks
        mock_repositories['crawl_job_repo'].session.begin_nested = AsyncMock()
        mock_repositories['crawl_job_repo'].session.execute = AsyncMock()
        
        # Mock the SELECT FOR UPDATE query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = job
        mock_repositories['crawl_job_repo'].session.execute.return_value = mock_result
        
        # Attempt to process a duplicate task result
        await crawl_job_service.handle_task_completion(
            job_id=job.id,
            task_id="duplicate-task",
            result={"success": True, "downloaded": 10, "images": []}
        )
        
        # Verify no updates were made (deduplication worked)
        mock_repositories['crawl_job_repo'].update_chunk_counts.assert_not_called()
        mock_repositories['image_repo'].bulk_create.assert_not_called()


class TestRetryCounterReset:
    """Tests for retry counter reset (Requirement 11.4)."""

    @pytest.mark.asyncio
    async def test_retry_resets_all_counters(
        self,
        crawl_job_service,
        mock_repositories,
        failed_job
    ):
        """Test that retry resets all counters including chunk counters."""
        # Setup mocks
        mock_repositories['crawl_job_repo'].get_by_id.return_value = failed_job
        mock_repositories['crawl_job_repo'].session.commit = AsyncMock()
        mock_repositories['crawl_job_repo'].session.refresh = AsyncMock()
        
        # Mock ownership check
        with patch.object(crawl_job_service, 'get_job_with_ownership_check', return_value=failed_job):
            # Call retry_job
            await crawl_job_service.retry_job(
                job_id=failed_job.id,
                user_id=str(uuid4())
            )
        
        # Verify all counters were reset
        assert failed_job.status == "pending"
        assert failed_job.progress == 0
        assert failed_job.total_images == 0
        assert failed_job.downloaded_images == 0
        assert failed_job.valid_images == 0
        assert failed_job.total_chunks == 0
        assert failed_job.active_chunks == 0
        assert failed_job.completed_chunks == 0
        assert failed_job.failed_chunks == 0
        assert failed_job.task_ids == []
        assert failed_job.started_at is None
        assert failed_job.completed_at is None

    @pytest.mark.asyncio
    async def test_retry_only_allows_failed_or_cancelled_jobs(
        self,
        crawl_job_service,
        mock_repositories,
        running_job
    ):
        """Test that only failed or cancelled jobs can be retried."""
        # Setup mocks
        mock_repositories['crawl_job_repo'].get_by_id.return_value = running_job
        
        # Mock ownership check
        with patch.object(crawl_job_service, 'get_job_with_ownership_check', return_value=running_job):
            # Attempt to retry a running job
            with pytest.raises(ValidationError) as exc_info:
                await crawl_job_service.retry_job(
                    job_id=running_job.id,
                    user_id=str(uuid4())
                )
            
            assert "only failed or cancelled" in str(exc_info.value).lower()
