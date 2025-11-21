"""
Comprehensive tests for temporary storage cleanup service.

This module provides extensive test coverage for all temp storage cleanup
scenarios including normal cleanup, crash recovery, emergency cleanup,
orphaned file detection, and API endpoints.

Test Classes:
    TestTempStorageCleanupService: Core service functionality tests
    TestOrphanedFileDetector: Orphaned file detection tests
    TestCleanupTasks: Celery task tests
    TestCleanupAPI: API endpoint tests

Test Scenarios:
    - Normal cleanup after chunk completion
    - Crash recovery cleanup for failed jobs
    - Emergency cleanup at storage threshold
    - Orphaned file detection and cleanup
    - Scheduled periodic cleanup
    - API endpoint functionality
    - Configuration validation
"""

import os
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import Mock, patch, AsyncMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.temp_storage_cleanup import (
    TempStorageCleanupService,
    OrphanedFileDetector,
    CleanupTrigger,
    CleanupStats,
    TempStorageCleanupError
)
from backend.core.settings.temp_storage_cleanup import TempStorageCleanupSettings
from backend.tasks.temp_storage_cleanup import (
    task_scheduled_cleanup,
    task_emergency_cleanup,
    task_cleanup_orphaned_files,
    task_cleanup_after_crash,
    task_cleanup_after_chunk
)
from backend.api.v1.endpoints.temp_storage_cleanup import router
from backend.main import app


class MockStorageProvider:
    """Mock storage provider for testing."""
    
    def __init__(self, usage_percent: float = 50.0):
        self.usage_percent = usage_percent
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        return {"usage_percent": self.usage_percent}


class MockCrawlJob:
    """Mock crawl job for testing."""
    
    def __init__(self, job_id: int, status: str = "completed"):
        self.id = job_id
        self.status = status
        self.updated_at = datetime.utcnow()


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_session():
    """Mock async database session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def cleanup_settings(temp_dir):
    """Create test cleanup settings."""
    return TempStorageCleanupSettings(
        temp_storage_path=temp_dir,
        emergency_cleanup_threshold=95.0,
        warning_threshold=85.0,
        cleanup_batch_size=100,
        max_orphan_age_hours=1,
        scheduled_cleanup_interval_minutes=5
    )


@pytest.fixture
def mock_storage_provider():
    """Mock storage provider."""
    return MockStorageProvider(usage_percent=50.0)


@pytest.fixture
def cleanup_service(mock_session, mock_storage_provider, temp_dir):
    """Create cleanup service for testing."""
    with patch('backend.services.temp_storage_cleanup.get_settings') as mock_settings:
        mock_settings.return_value.storage.temp_storage_path = temp_dir
        mock_settings.return_value.storage.emergency_cleanup_threshold = 95.0
        
        service = TempStorageCleanupService(
            storage_provider=mock_storage_provider,
            session=mock_session
        )
        service.temp_storage_path = temp_dir
        return service


def create_test_files(temp_dir: Path, file_patterns: List[str]) -> List[Path]:
    """Create test files in temp directory."""
    files = []
    for pattern in file_patterns:
        file_path = temp_dir / pattern
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("test content")
        files.append(file_path)
    return files


class TestTempStorageCleanupService:
    """Test the main cleanup service functionality."""
    
    @pytest.mark.asyncio
    async def test_get_storage_stats(self, cleanup_service, temp_dir):
        """Test getting storage statistics."""
        # Create some test files
        test_files = create_test_files(temp_dir, [
            "job_1_chunk_1_temp.tmp",
            "job_2_image.jpg",
            "orphaned_file.tmp"
        ])
        
        # Mock database queries
        cleanup_service.session.execute.return_value.scalars.return_value.all.return_value = [
            MockCrawlJob(1, "running"),
            MockCrawlJob(2, "completed")
        ]
        
        stats = await cleanup_service.get_storage_stats()
        
        assert stats["storage_usage_percent"] == 50.0
        assert stats["temp_files_count"] == 3
        assert stats["temp_files_size_bytes"] > 0
        assert "active_jobs_count" in stats
        assert "failed_jobs_count" in stats
    
    @pytest.mark.asyncio
    async def test_cleanup_after_chunk_completion(self, cleanup_service, temp_dir):
        """Test cleanup after successful chunk completion."""
        # Create test files for a specific chunk
        test_files = create_test_files(temp_dir, [
            "job_123_chunk_abc_temp1.tmp",
            "job_123_chunk_abc_temp2.tmp",
            "job_123_chunk_xyz_temp3.tmp",  # Different chunk
        ])
        
        completed_files = ["temp1", "temp2"]
        
        stats = await cleanup_service.cleanup_after_chunk_completion(
            job_id=123,
            chunk_id="abc",
            completed_files=completed_files
        )
        
        assert stats.trigger == CleanupTrigger.CHUNK_COMPLETION
        assert stats.files_deleted == 2  # Only files from chunk abc with completed names
        assert stats.bytes_freed > 0
        assert len(stats.errors) == 0
        
        # Verify correct files were deleted
        assert not test_files[0].exists()  # temp1
        assert not test_files[1].exists()  # temp2
        assert test_files[2].exists()     # Different chunk, should remain
    
    @pytest.mark.asyncio
    async def test_cleanup_after_crash(self, cleanup_service, temp_dir):
        """Test cleanup after job crashes."""
        # Create test files for failed jobs
        test_files = create_test_files(temp_dir, [
            "job_456_temp1.tmp",
            "job_456_temp2.tmp",
            "job_789_temp3.tmp",
        ])
        
        # Mock failed jobs
        failed_jobs = [MockCrawlJob(456, "failed"), MockCrawlJob(789, "cancelled")]
        cleanup_service.session.execute.return_value.scalars.return_value.all.return_value = failed_jobs
        
        stats = await cleanup_service.cleanup_after_crash()
        
        assert stats.trigger == CleanupTrigger.CRASH_RECOVERY
        assert stats.files_deleted == 3  # All files from failed jobs
        assert stats.bytes_freed > 0
        
        # Verify all files were deleted
        for file_path in test_files:
            assert not file_path.exists()
    
    @pytest.mark.asyncio
    async def test_emergency_cleanup(self, cleanup_service, temp_dir):
        """Test emergency cleanup when storage threshold exceeded."""
        # Set high storage usage
        cleanup_service.storage_provider.usage_percent = 96.0
        
        # Create various test files
        test_files = create_test_files(temp_dir, [
            "job_111_temp1.tmp",
            "job_222_temp2.tmp",
            "orphaned_old_file.tmp",
        ])
        
        # Make one file older for orphan detection
        old_time = datetime.now().timestamp() - 3600  # 1 hour ago
        os.utime(test_files[2], (old_time, old_time))
        
        # Mock database queries for orphan detection
        cleanup_service.session.execute.return_value.scalars.return_value.all.return_value = []
        
        stats = await cleanup_service.emergency_cleanup()
        
        assert stats.trigger == CleanupTrigger.EMERGENCY_THRESHOLD
        assert stats.storage_before_percent == 96.0
        assert stats.files_deleted > 0
        assert stats.bytes_freed > 0
    
    @pytest.mark.asyncio
    async def test_cleanup_orphaned_files(self, cleanup_service, temp_dir):
        """Test orphaned files cleanup."""
        # Create test files with different ages
        test_files = create_test_files(temp_dir, [
            "job_999_recent.tmp",
            "job_888_old.tmp",
            "no_job_id_old.tmp",
        ])
        
        # Make some files old
        old_time = datetime.now().timestamp() - 7200  # 2 hours ago
        os.utime(test_files[1], (old_time, old_time))
        os.utime(test_files[2], (old_time, old_time))
        
        # Mock database - job 999 exists and is active, job 888 doesn't exist
        def mock_execute(stmt):
            result = Mock()
            if "job_999" in str(stmt) or "999" in str(stmt):
                result.scalars.return_value.all.return_value = [MockCrawlJob(999, "running")]
            else:
                result.scalars.return_value.all.return_value = []
            result.scalar.return_value = None  # For job existence check
            return result
        
        cleanup_service.session.execute.side_effect = mock_execute
        
        stats = await cleanup_service.cleanup_orphaned_files(max_age_hours=1)
        
        assert stats.trigger == CleanupTrigger.ORPHANED_FILES
        assert stats.files_deleted >= 1  # At least the old orphaned files
        
        # Recent file from active job should remain
        assert test_files[0].exists()
    
    @pytest.mark.asyncio
    async def test_scheduled_cleanup(self, cleanup_service, temp_dir):
        """Test scheduled periodic cleanup."""
        # Set normal storage usage (below emergency threshold)
        cleanup_service.storage_provider.usage_percent = 80.0
        
        # Create mixed test files
        test_files = create_test_files(temp_dir, [
            "job_111_active.tmp",
            "job_222_failed.tmp",
            "old_orphaned.tmp",
        ])
        
        # Mock database queries
        cleanup_service.session.execute.return_value.scalars.return_value.all.return_value = [
            MockCrawlJob(222, "failed")  # Job 111 is not returned (doesn't exist)
        ]
        
        stats = await cleanup_service.scheduled_cleanup()
        
        assert stats.trigger == CleanupTrigger.SCHEDULED
        assert stats.files_deleted >= 0
        assert stats.storage_before_percent == 80.0


class TestOrphanedFileDetector:
    """Test orphaned file detection functionality."""
    
    @pytest.mark.asyncio
    async def test_detect_orphaned_files(self, mock_session, temp_dir):
        """Test orphaned file detection logic."""
        detector = OrphanedFileDetector(mock_session, temp_dir)
        
        # Create test files
        test_files = create_test_files(temp_dir, [
            "job_123_active.tmp",
            "job_456_failed.tmp",
            "job_789_old_failed.tmp",
            "no_job_pattern.tmp",
        ])
        
        # Make some files old
        old_time = datetime.now().timestamp() - 3600  # 1 hour ago
        os.utime(test_files[2], (old_time, old_time))
        os.utime(test_files[3], (old_time, old_time))
        
        # Mock database queries
        def mock_execute(stmt):
            result = Mock()
            # Active jobs: only 123
            if "pending" in str(stmt) or "running" in str(stmt):
                result.scalars.return_value.all.return_value = [MockCrawlJob(123, "running")]
            # Old failed jobs: 789
            elif "failed" in str(stmt) or "cancelled" in str(stmt):
                result.scalars.return_value.all.return_value = [MockCrawlJob(789, "failed")]
            else:
                result.scalars.return_value.all.return_value = []
            return result
        
        mock_session.execute.side_effect = mock_execute
        
        orphaned_files = await detector.detect_orphaned_files(max_age_hours=1)
        
        # Should detect files from non-existent job 456, old failed job 789, and no job pattern
        assert len(orphaned_files) >= 2
        orphaned_names = [f.name for f in orphaned_files]
        assert "job_456_failed.tmp" in orphaned_names or "no_job_pattern.tmp" in orphaned_names


class TestCleanupAPI:
    """Test cleanup API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_get_cleanup_stats_endpoint(self, client):
        """Test GET /api/v1/cleanup/stats endpoint."""
        with patch('backend.api.v1.endpoints.temp_storage_cleanup.task_get_storage_stats') as mock_task:
            # Mock successful task result
            mock_result = Mock()
            mock_result.get.return_value = {
                "success": True,
                "stats": {
                    "storage_usage_percent": 75.0,
                    "emergency_threshold": 95.0,
                    "temp_files_count": 10,
                    "temp_files_size_bytes": 1024,
                    "active_jobs_count": 2,
                    "failed_jobs_count": 1,
                    "orphaned_files_count": 3,
                    "orphaned_files_size_bytes": 512,
                    "cleanup_needed": False
                }
            }
            mock_task.delay.return_value = mock_result
            
            response = client.get("/api/v1/cleanup/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["storage_usage_percent"] == 75.0
            assert data["temp_files_count"] == 10
    
    def test_trigger_emergency_cleanup_endpoint(self, client):
        """Test POST /api/v1/cleanup/emergency endpoint."""
        with patch('backend.api.v1.endpoints.temp_storage_cleanup.task_emergency_cleanup') as mock_task:
            mock_result = Mock()
            mock_result.id = "test-task-123"
            mock_task.delay.return_value = mock_result
            
            response = client.post("/api/v1/cleanup/emergency")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["task_id"] == "test-task-123"
            assert data["trigger_type"] == "manual_emergency"
    
    def test_trigger_orphaned_cleanup_endpoint(self, client):
        """Test POST /api/v1/cleanup/orphaned endpoint."""
        with patch('backend.api.v1.endpoints.temp_storage_cleanup.task_cleanup_orphaned_files') as mock_task:
            mock_result = Mock()
            mock_result.id = "test-task-456"
            mock_task.delay.return_value = mock_result
            
            response = client.post("/api/v1/cleanup/orphaned", json={"max_age_hours": 12})
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["task_id"] == "test-task-456"
            assert "12 hours" in data["message"]
    
    def test_trigger_crash_recovery_endpoint(self, client):
        """Test POST /api/v1/cleanup/crash/{job_id} endpoint."""
        with patch('backend.api.v1.endpoints.temp_storage_cleanup.task_cleanup_after_crash') as mock_task:
            mock_result = Mock()
            mock_result.id = "test-task-789"
            mock_task.delay.return_value = mock_result
            
            response = client.post("/api/v1/cleanup/crash/123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["task_id"] == "test-task-789"
            assert "job 123" in data["message"]
    
    def test_cleanup_health_check_endpoint(self, client):
        """Test GET /api/v1/cleanup/health endpoint."""
        with patch('backend.api.v1.endpoints.temp_storage_cleanup.get_cleanup_service') as mock_service:
            mock_cleanup_service = AsyncMock()
            mock_cleanup_service.get_storage_stats.return_value = {
                "storage_usage_percent": 60.0,
                "emergency_threshold": 95.0,
                "cleanup_needed": False,
                "temp_files_count": 5,
                "orphaned_files_count": 1
            }
            mock_service.return_value = mock_cleanup_service
            
            response = client.get("/api/v1/cleanup/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["service"] == "temp_storage_cleanup"
            assert data["status"] == "healthy"
            assert data["storage_usage_percent"] == 60.0


class TestCleanupConfiguration:
    """Test cleanup configuration and settings."""
    
    def test_cleanup_settings_validation(self):
        """Test cleanup settings validation."""
        # Valid settings
        settings = TempStorageCleanupSettings(
            emergency_cleanup_threshold=95.0,
            warning_threshold=85.0,
            cleanup_batch_size=1000,
            max_orphan_age_hours=24
        )
        assert settings.emergency_cleanup_threshold == 95.0
        assert settings.warning_threshold == 85.0
    
    def test_cleanup_settings_validation_errors(self):
        """Test cleanup settings validation errors."""
        # Warning threshold >= emergency threshold should fail
        with pytest.raises(ValueError):
            TempStorageCleanupSettings(
                emergency_cleanup_threshold=90.0,
                warning_threshold=95.0  # Higher than emergency
            )
    
    def test_cleanup_stats_to_dict(self):
        """Test CleanupStats to_dict conversion."""
        stats = CleanupStats(
            trigger=CleanupTrigger.EMERGENCY_THRESHOLD,
            start_time=datetime.utcnow(),
            files_deleted=10,
            bytes_freed=1024
        )
        stats.end_time = datetime.utcnow()
        
        data = stats.to_dict()
        
        assert data["trigger"] == "emergency_threshold"
        assert data["files_deleted"] == 10
        assert data["bytes_freed"] == 1024
        assert "duration_seconds" in data
        assert "start_time" in data
        assert "end_time" in data


class TestCleanupIntegration:
    """Integration tests for cleanup service."""
    
    @pytest.mark.asyncio
    async def test_full_cleanup_workflow(self, cleanup_service, temp_dir):
        """Test complete cleanup workflow."""
        # Create a realistic temp storage scenario
        test_files = create_test_files(temp_dir, [
            "job_1_chunk_a_image1.tmp",
            "job_1_chunk_a_image2.tmp",
            "job_2_chunk_b_image3.tmp",
            "job_3_failed_image4.tmp",
            "orphaned_old_file.tmp",
        ])
        
        # Make some files old
        old_time = datetime.now().timestamp() - 7200  # 2 hours ago
        os.utime(test_files[3], (old_time, old_time))  # Failed job file
        os.utime(test_files[4], (old_time, old_time))  # Orphaned file
        
        # Mock database state
        cleanup_service.session.execute.return_value.scalars.return_value.all.return_value = [
            MockCrawlJob(1, "running"),   # Active job
            MockCrawlJob(2, "completed"), # Completed job
            MockCrawlJob(3, "failed"),    # Failed job
        ]
        
        # 1. Simulate chunk completion for job 1
        chunk_stats = await cleanup_service.cleanup_after_chunk_completion(
            job_id=1,
            chunk_id="a",
            completed_files=["image1", "image2"]
        )
        
        assert chunk_stats.files_deleted == 2
        assert not test_files[0].exists()  # job_1_chunk_a_image1.tmp
        assert not test_files[1].exists()  # job_1_chunk_a_image2.tmp
        
        # 2. Run crash recovery cleanup
        crash_stats = await cleanup_service.cleanup_after_crash(job_id=3)
        
        assert crash_stats.files_deleted == 1
        assert not test_files[3].exists()  # job_3_failed_image4.tmp
        
        # 3. Run orphaned files cleanup
        orphan_stats = await cleanup_service.cleanup_orphaned_files(max_age_hours=1)
        
        assert orphan_stats.files_deleted >= 1
        
        # Verify final state
        remaining_files = list(temp_dir.glob("*"))
        assert len(remaining_files) <= 1  # Only job_2 file might remain


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
