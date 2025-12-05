"""
API integration tests for Crawl Jobs endpoints.

Tests cover:
- List crawl jobs with pagination
- Create crawl job
- Get crawl job details
- Cancel crawl job
- Retry failed job
- Get job logs
- Get job progress
- Response model validation
- OpenAPI schema generation
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import status

from backend.models import CrawlJob, ActivityLog
from backend.services.crawl_job import CrawlJobService


@pytest.fixture
def mock_crawl_job_service():
    """Create mock crawl job service."""
    return AsyncMock(spec=CrawlJobService)


@pytest.fixture
def mock_user():
    """Create mock authenticated user."""
    user_id = uuid4()
    return {
        "user_id": str(user_id),
        "email": "test@example.com",
        "profile": {"id": str(user_id), "email": "test@example.com"}
    }


@pytest.fixture
def sample_crawl_job(mock_user):
    """Create sample crawl job for testing."""
    user_id = uuid4()
    project_id = 1
    return CrawlJob(
        id=1,
        project_id=project_id,
        name="Test Crawl Job",
        max_images=1000,
        status="running",
        progress=50,
        total_images=500,
        downloaded_images=500,
        valid_images=475,
        total_chunks=10,
        active_chunks=2,
        completed_chunks=7,
        failed_chunks=1,
        created_at=datetime(2024, 1, 1, 10, 0, 0),
        updated_at=datetime(2024, 1, 1, 10, 30, 0),
        started_at=datetime(2024, 1, 1, 10, 5, 0),
        completed_at=None
    )


@pytest.fixture
def override_dependencies(app, mock_crawl_job_service, mock_user):
    """Override FastAPI dependencies for testing."""
    from backend.api.dependencies import get_current_user, get_session, get_crawl_job_service

    # Mock database session
    mock_session = AsyncMock()

    app.dependency_overrides[get_crawl_job_service] = lambda: mock_crawl_job_service
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_session] = lambda: mock_session

    yield mock_crawl_job_service, mock_user, mock_session

    app.dependency_overrides = {}


class TestListCrawlJobs:
    """Tests for GET /api/v1/crawl-jobs/ endpoint."""

    def test_list_crawl_jobs_success(self, client, override_dependencies, sample_crawl_job):
        """Test successful crawl jobs listing."""
        mock_service, mock_user, mock_session = override_dependencies

        # Mock paginate function
        with patch('backend.api.v1.endpoints.crawl_jobs.paginate') as mock_paginate:
            mock_paginate.return_value = {
                "items": [sample_crawl_job],
                "total": 1,
                "page": 1,
                "size": 50
            }

            response = client.get("/api/v1/crawl-jobs/")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "items" in data
            assert len(data["items"]) == 1
            assert data["items"][0]["name"] == "Test Crawl Job"

    def test_list_crawl_jobs_pagination(self, client, override_dependencies):
        """Test pagination parameters."""
        with patch('backend.api.v1.endpoints.crawl_jobs.paginate') as mock_paginate:
            mock_paginate.return_value = {"items": [], "total": 0, "page": 2, "size": 25}

            response = client.get("/api/v1/crawl-jobs/?page=2&size=25")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["page"] == 2
            assert data["size"] == 25

    def test_list_crawl_jobs_response_model(self, client, override_dependencies, sample_crawl_job):
        """Test response model structure."""
        with patch('backend.api.v1.endpoints.crawl_jobs.paginate') as mock_paginate:
            mock_paginate.return_value = {"items": [sample_crawl_job], "total": 1}

            response = client.get("/api/v1/crawl-jobs/")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Verify pagination structure
            assert "items" in data
            assert "total" in data


class TestCreateCrawlJob:
    """Tests for POST /api/v1/crawl-jobs/ endpoint."""

    def test_create_crawl_job_success(self, client, override_dependencies, sample_crawl_job):
        """Test successful crawl job creation."""
        mock_service, mock_user, mock_session = override_dependencies
        mock_service.create_job.return_value = sample_crawl_job

        job_data = {
            "project_id": 1,
            "name": "New Crawl Job",
            "keywords": ["cats", "dogs"],
            "max_images": 1000
        }

        response = client.post("/api/v1/crawl-jobs/", json=job_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Test Crawl Job"
        assert data["status"] == "running"
        assert "id" in data

        # Verify service was called
        mock_service.create_job.assert_called_once()

    def test_create_crawl_job_validation(self, client, override_dependencies):
        """Test request validation."""
        # Missing required fields
        response = client.post("/api/v1/crawl-jobs/", json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_crawl_job_response_model(self, client, override_dependencies, sample_crawl_job):
        """Test response model structure."""
        mock_service, mock_user, mock_session = override_dependencies
        mock_service.create_job.return_value = sample_crawl_job

        job_data = {
            "project_id": 1,
            "name": "New Job",
            "keywords": ["test"],
            "max_images": 100
        }

        response = client.post("/api/v1/crawl-jobs/", json=job_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        # Verify required fields
        required_fields = ["id", "project_id", "name", "keywords", "status", "progress"]
        for field in required_fields:
            assert field in data


class TestGetCrawlJob:
    """Tests for GET /api/v1/crawl-jobs/{job_id} endpoint."""

    def test_get_crawl_job_success(self, client, override_dependencies, sample_crawl_job, mock_user):
        """Test successful crawl job retrieval."""
        mock_service, user, mock_session = override_dependencies
        mock_service.get_job.return_value = sample_crawl_job

        # Mock ownership check
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = uuid.UUID(mock_user["user_id"])
        mock_session.execute.return_value = mock_result

        response = client.get("/api/v1/crawl-jobs/1")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Test Crawl Job"
        assert data["status"] == "running"

    def test_get_crawl_job_not_found(self, client, override_dependencies):
        """Test job not found."""
        mock_service, mock_user, mock_session = override_dependencies
        mock_service.get_job.return_value = None

        response = client.get("/api/v1/crawl-jobs/999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_crawl_job_unauthorized_access(self, client, override_dependencies, sample_crawl_job):
        """Test unauthorized access to another user's job."""
        mock_service, mock_user, mock_session = override_dependencies
        mock_service.get_job.return_value = sample_crawl_job

        # Mock ownership check - different user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = uuid4()  # Different user
        mock_session.execute.return_value = mock_result

        response = client.get("/api/v1/crawl-jobs/1")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestStartCrawlJob:
    """Tests for POST /api/v1/crawl-jobs/{job_id}/start endpoint."""

    def test_start_crawl_job_success(self, client, override_dependencies, sample_crawl_job):
        """Test successful job start."""
        mock_service, mock_user, mock_session = override_dependencies
        sample_crawl_job.status = "pending"
        
        # Mock start_job to return expected result
        mock_service.start_job.return_value = {
            "job_id": 1,
            "status": "running",
            "task_ids": ["task-uuid-1", "task-uuid-2", "task-uuid-3"],
            "total_chunks": 6,
            "message": "Job started with 6 tasks"
        }

        response = client.post("/api/v1/crawl-jobs/1/start")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["job_id"] == 1
        assert data["status"] == "running"
        assert "task_ids" in data
        assert len(data["task_ids"]) == 3
        assert data["total_chunks"] == 6
        assert "message" in data

        # Verify service was called
        mock_service.start_job.assert_called_once_with(
            job_id=1,
            user_id=mock_user["user_id"]
        )

    def test_start_crawl_job_wrong_status(self, client, override_dependencies):
        """Test starting a job that's not pending fails."""
        mock_service, mock_user, mock_session = override_dependencies
        
        from backend.core.exceptions import ValidationError
        mock_service.start_job.side_effect = ValidationError(
            "Cannot start job with status 'running'. Only pending jobs can be started."
        )

        response = client.post("/api/v1/crawl-jobs/1/start")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "cannot start" in data["detail"].lower()

    def test_start_crawl_job_not_found(self, client, override_dependencies):
        """Test starting a non-existent job."""
        mock_service, mock_user, mock_session = override_dependencies
        
        from backend.core.exceptions import NotFoundError
        mock_service.start_job.side_effect = NotFoundError("Crawl job not found: 999")

        response = client.post("/api/v1/crawl-jobs/999/start")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_start_crawl_job_response_model(self, client, override_dependencies):
        """Test response model structure."""
        mock_service, mock_user, mock_session = override_dependencies
        
        mock_service.start_job.return_value = {
            "job_id": 1,
            "status": "running",
            "task_ids": ["task-1", "task-2"],
            "total_chunks": 4,
            "message": "Job started with 4 tasks"
        }

        response = client.post("/api/v1/crawl-jobs/1/start")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify required fields
        required_fields = ["job_id", "status", "task_ids", "total_chunks", "message"]
        for field in required_fields:
            assert field in data


class TestCancelCrawlJob:
    """Tests for POST /api/v1/crawl-jobs/{job_id}/cancel endpoint."""

    def test_cancel_crawl_job_success(self, client, override_dependencies, sample_crawl_job):
        """Test successful job cancellation."""
        mock_service, mock_user, mock_session = override_dependencies
        sample_crawl_job.status = "running"
        mock_service.get_job.return_value = sample_crawl_job
        
        # Mock the cancel_job method to return the expected dictionary
        mock_service.cancel_job.return_value = {
            "job_id": 1,
            "status": "cancelled",
            "revoked_tasks": 5,
            "message": "Job cancelled successfully. 5 task(s) revoked."
        }

        response = client.post("/api/v1/crawl-jobs/1/cancel")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["job_id"] == 1
        assert data["status"] == "cancelled"
        assert data["revoked_tasks"] == 5
        assert "message" in data
        assert "cancelled" in data["message"].lower()

    def test_cancel_crawl_job_wrong_status(self, client, override_dependencies, sample_crawl_job):
        """Test cancellation of completed job fails."""
        mock_service, mock_user, mock_session = override_dependencies
        sample_crawl_job.status = "completed"
        mock_service.get_job.return_value = sample_crawl_job

        response = client.post("/api/v1/crawl-jobs/1/cancel")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "cannot cancel" in data["detail"].lower()

    def test_cancel_crawl_job_not_found(self, client, override_dependencies):
        """Test cancellation of non-existent job."""
        mock_service, mock_user, mock_session = override_dependencies
        mock_service.get_job.return_value = None

        response = client.post("/api/v1/crawl-jobs/999/cancel")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRetryCrawlJob:
    """Tests for POST /api/v1/crawl-jobs/{job_id}/retry endpoint."""

    def test_retry_crawl_job_success(self, client, override_dependencies, sample_crawl_job, mock_user):
        """Test successful job retry."""
        mock_service, user, mock_session = override_dependencies
        sample_crawl_job.status = "failed"
        mock_service.get_job.return_value = sample_crawl_job

        # Mock ownership check
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = uuid.UUID(mock_user["user_id"])
        mock_session.execute.return_value = mock_result

        response = client.post("/api/v1/crawl-jobs/1/retry")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "pending"
        assert data["progress"] == 0

    def test_retry_crawl_job_wrong_status(self, client, override_dependencies, sample_crawl_job, mock_user):
        """Test retry of running job fails."""
        mock_service, user, mock_session = override_dependencies
        sample_crawl_job.status = "running"
        mock_service.get_job.return_value = sample_crawl_job

        # Mock ownership check
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = uuid.UUID(mock_user["user_id"])
        mock_session.execute.return_value = mock_result

        response = client.post("/api/v1/crawl-jobs/1/retry")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestGetCrawlJobLogs:
    """Tests for GET /api/v1/crawl-jobs/{job_id}/logs endpoint."""

    def test_get_job_logs_success(self, client, override_dependencies, sample_crawl_job, mock_user):
        """Test successful log retrieval."""
        mock_service, user, mock_session = override_dependencies
        mock_service.get_job.return_value = sample_crawl_job

        # Mock ownership check
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = uuid.UUID(mock_user["user_id"])

        # Mock logs query
        mock_logs = [
            ActivityLog(
                id=1,
                user_id=uuid.UUID(mock_user["user_id"]),
                action="Job started",
                resource_type="crawl_job",
                resource_id="1",
                timestamp=datetime(2024, 1, 1, 10, 0, 0),
                metadata_={"images_target": 1000}
            )
        ]
        mock_logs_result = MagicMock()
        mock_logs_result.scalars.return_value.all.return_value = mock_logs

        mock_session.execute.side_effect = [mock_result, mock_logs_result]

        response = client.get("/api/v1/crawl-jobs/1/logs")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["action"] == "Job started"


class TestGetCrawlJobProgress:
    """Tests for GET /api/v1/crawl-jobs/{job_id}/progress endpoint."""

    def test_get_job_progress_success(self, client, override_dependencies, sample_crawl_job, mock_user):
        """Test successful progress retrieval."""
        mock_service, user, mock_session = override_dependencies
        mock_service.get_job_with_ownership_check.return_value = sample_crawl_job

        response = client.get("/api/v1/crawl-jobs/1/progress")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["job_id"] == 1
        assert data["status"] == "running"
        assert data["progress"] == 50
        assert data["total_chunks"] == 10
        assert data["active_chunks"] == 2
        assert data["completed_chunks"] == 7
        assert data["failed_chunks"] == 1
        assert data["downloaded_images"] == 500
        assert data["estimated_completion"] is None
        assert "started_at" in data
        assert "updated_at" in data


class TestOpenAPISchema:
    """Tests for OpenAPI schema generation."""

    def test_crawl_jobs_endpoints_in_openapi(self, client):
        """Test that all crawl job endpoints are documented."""
        response = client.get("/openapi.json")

        assert response.status_code == status.HTTP_200_OK
        openapi_schema = response.json()
        paths = openapi_schema.get("paths", {})

        # Check endpoints exist
        assert "/api/v1/crawl-jobs/" in paths
        assert "/api/v1/crawl-jobs/{job_id}" in paths
        assert "/api/v1/crawl-jobs/{job_id}/start" in paths
        assert "/api/v1/crawl-jobs/{job_id}/cancel" in paths
        assert "/api/v1/crawl-jobs/{job_id}/retry" in paths
        assert "/api/v1/crawl-jobs/{job_id}/logs" in paths
        assert "/api/v1/crawl-jobs/{job_id}/progress" in paths

    def test_crawl_jobs_endpoints_have_operation_ids(self, client):
        """Test that all endpoints have operation IDs."""
        response = client.get("/openapi.json")
        openapi_schema = response.json()
        paths = openapi_schema.get("paths", {})

        # Check operation IDs
        assert paths["/api/v1/crawl-jobs/"]["get"]["operationId"] == "listCrawlJobs"
        assert paths["/api/v1/crawl-jobs/"]["post"]["operationId"] == "createCrawlJob"
        assert paths["/api/v1/crawl-jobs/{job_id}"]["get"]["operationId"] == "getCrawlJob"
        assert paths["/api/v1/crawl-jobs/{job_id}/start"]["post"]["operationId"] == "startCrawlJob"
        assert paths["/api/v1/crawl-jobs/{job_id}/cancel"]["post"]["operationId"] == "cancelCrawlJob"
        assert paths["/api/v1/crawl-jobs/{job_id}/retry"]["post"]["operationId"] == "retryCrawlJob"
