"""
Unit and integration tests for job cancellation functionality.

Tests the cancel_job method in CrawlJobService including:
- Celery task revocation
- Storage cleanup
- Database status updates
- Activity logging
- API endpoint integration
"""

import pytest
import uuid
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from backend.services.crawl_job import CrawlJobService
from backend.core.exceptions import NotFoundError, ValidationError
from backend.models import CrawlJob, Project


class TestCancelJobService:
    """Unit tests for CrawlJobService.cancel_job method."""

    @pytest.fixture
    def mock_job(self):
        """Create a mock crawl job."""
        job = Mock(spec=CrawlJob)
        job.id = 1
        job.name = "Test Job"
        job.status = "running"
        job.task_ids = ["task-1", "task-2", "task-3"]
        job.downloaded_images = 50
        job.valid_images = 45
        job.progress = 50
        job.project_id = 1
        return job

    @pytest.fixture
    def service(self):
        """Create a CrawlJobService instance with mocked dependencies."""
        crawl_job_repo = AsyncMock()
        project_repo = AsyncMock()
        image_repo = AsyncMock()
        activity_log_repo = AsyncMock()
        
        service = CrawlJobService(
            crawl_job_repo=crawl_job_repo,
            project_repo=project_repo,
            image_repo=image_repo,
            activity_log_repo=activity_log_repo
        )
        return service

    @pytest.mark.asyncio
    async def test_cancel_job_success_running(self, service, mock_job):
        """Test successfully cancelling a running job."""
        # Setup
        service.get_job = AsyncMock(return_value=mock_job)
        service.update_job_status = AsyncMock(return_value=mock_job)
        service._revoke_celery_tasks = AsyncMock()
        service._cleanup_job_storage = AsyncMock()
        
        # Execute
        result = await service.cancel_job(
            job_id=1,
            user_id="user-123"
        )
        
        # Assert
        assert result == mock_job
        service._revoke_celery_tasks.assert_called_once_with(
            ["task-1", "task-2", "task-3"],
            terminate=True
        )
        service._cleanup_job_storage.assert_called_once_with(1)
        service.update_job_status.assert_called_once()
        service.activity_log_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_job_success_pending(self, service, mock_job):
        """Test successfully cancelling a pending job."""
        # Setup
        mock_job.status = "pending"
        mock_job.task_ids = []  # No tasks yet
        service.get_job = AsyncMock(return_value=mock_job)
        service.update_job_status = AsyncMock(return_value=mock_job)
        service._revoke_celery_tasks = AsyncMock()
        service._cleanup_job_storage = AsyncMock()
        
        # Execute
        result = await service.cancel_job(job_id=1)
        
        # Assert
        assert result == mock_job
        service._revoke_celery_tasks.assert_called_once_with([], terminate=True)
        service._cleanup_job_storage.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_cancel_job_not_found(self, service):
        """Test cancelling a non-existent job."""
        # Setup
        service.get_job = AsyncMock(return_value=None)
        
        # Execute & Assert
        with pytest.raises(NotFoundError, match="Crawl job not found: 999"):
            await service.cancel_job(job_id=999)

    @pytest.mark.asyncio
    async def test_cancel_job_invalid_status_completed(self, service, mock_job):
        """Test cancelling a completed job (should fail)."""
        # Setup
        mock_job.status = "completed"
        service.get_job = AsyncMock(return_value=mock_job)
        
        # Execute & Assert
        with pytest.raises(ValidationError, match="Cannot cancel job with status"):
            await service.cancel_job(job_id=1)

    @pytest.mark.asyncio
    async def test_cancel_job_invalid_status_failed(self, service, mock_job):
        """Test cancelling a failed job (should fail)."""
        # Setup
        mock_job.status = "failed"
        service.get_job = AsyncMock(return_value=mock_job)
        
        # Execute & Assert
        with pytest.raises(ValidationError, match="Cannot cancel job with status"):
            await service.cancel_job(job_id=1)

    @pytest.mark.asyncio
    async def test_cancel_job_storage_cleanup_fails_gracefully(self, service, mock_job):
        """Test that storage cleanup failure doesn't prevent cancellation."""
        # Setup
        service.get_job = AsyncMock(return_value=mock_job)
        service.update_job_status = AsyncMock(return_value=mock_job)
        service._revoke_celery_tasks = AsyncMock()
        service._cleanup_job_storage = AsyncMock(side_effect=Exception("Storage error"))
        
        # Execute - should not raise exception
        result = await service.cancel_job(job_id=1)
        
        # Assert - job should still be cancelled
        assert result == mock_job
        service.update_job_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_revoke_celery_tasks(self, service):
        """Test Celery task revocation."""
        with patch('backend.services.crawl_job.celery_app') as mock_celery:
            mock_control = Mock()
            mock_celery.control = mock_control
            
            # Execute
            await service._revoke_celery_tasks(
                ["task-1", "task-2"],
                terminate=True
            )
            
            # Assert
            assert mock_control.revoke.call_count == 2
            mock_control.revoke.assert_any_call(
                "task-1",
                terminate=True,
                signal='SIGTERM'
            )
            mock_control.revoke.assert_any_call(
                "task-2",
                terminate=True,
                signal='SIGTERM'
            )

    @pytest.mark.asyncio
    async def test_revoke_celery_tasks_graceful(self, service):
        """Test graceful Celery task revocation."""
        with patch('backend.services.crawl_job.celery_app') as mock_celery:
            mock_control = Mock()
            mock_celery.control = mock_control
            
            # Execute
            await service._revoke_celery_tasks(
                ["task-1"],
                terminate=False
            )
            
            # Assert
            mock_control.revoke.assert_called_once_with(
                "task-1",
                terminate=False,
                signal=None
            )

    @pytest.mark.asyncio
    async def test_cleanup_job_storage(self, service):
        """Test storage cleanup."""
        with patch('backend.services.crawl_job.get_storage_provider') as mock_get_storage:
            mock_storage = Mock()
            mock_storage.list_files.return_value = [
                "job_1/image1.jpg",
                "job_1/image2.jpg",
                "job_1/image3.jpg"
            ]
            mock_get_storage.return_value = mock_storage
            
            # Execute
            await service._cleanup_job_storage(job_id=1)
            
            # Assert
            mock_storage.list_files.assert_called_once_with(prefix="job_1/")
            assert mock_storage.delete.call_count == 3

    @pytest.mark.asyncio
    async def test_cleanup_job_storage_no_files(self, service):
        """Test storage cleanup when no files exist."""
        with patch('backend.services.crawl_job.get_storage_provider') as mock_get_storage:
            mock_storage = Mock()
            mock_storage.list_files.return_value = []
            mock_get_storage.return_value = mock_storage
            
            # Execute
            await service._cleanup_job_storage(job_id=1)
            
            # Assert
            mock_storage.list_files.assert_called_once_with(prefix="job_1/")
            mock_storage.delete.assert_not_called()


class TestCancelJobEndpoint:
    """Integration tests for the cancel job API endpoint."""

    @pytest.mark.asyncio
    async def test_cancel_endpoint_success(self):
        """Test successful job cancellation via API endpoint."""
        # This would require a full integration test setup
        # with database, FastAPI test client, etc.
        # Placeholder for now
        pass

    @pytest.mark.asyncio
    async def test_cancel_endpoint_unauthorized(self):
        """Test cancellation with wrong user."""
        # Placeholder for integration test
        pass

    @pytest.mark.asyncio
    async def test_cancel_endpoint_invalid_status(self):
        """Test cancellation of completed job via API."""
        # Placeholder for integration test
        pass
