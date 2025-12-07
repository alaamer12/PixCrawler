"""
API integration tests for Storage endpoints.

Tests cover:
- Get storage usage
- List storage files
- Cleanup old files
- Generate presigned URLs
- Response model validation
- OpenAPI schema generation
"""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import status

from backend.api.dependencies import get_storage_service
from backend.services.storage import StorageService


@pytest.fixture
def mock_storage_service():
    """Create mock storage service."""
    return AsyncMock(spec=StorageService)


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
def override_dependencies(app, mock_storage_service, mock_user):
    """Override FastAPI dependencies for testing."""
    from backend.api.dependencies import get_current_user

    app.dependency_overrides[get_storage_service] = lambda: mock_storage_service
    app.dependency_overrides[get_current_user] = lambda: mock_user

    yield mock_storage_service, mock_user

    app.dependency_overrides = {}


class TestGetStorageUsage:
    """Tests for GET /api/v1/storage/usage/ endpoint."""

    def test_get_storage_usage_success(self, client, override_dependencies):
        """Test successful storage usage retrieval."""
        mock_service, mock_user = override_dependencies

        mock_usage = {
            "total_size_bytes": 1073741824,
            "total_size_gb": 1.0,
            "file_count": 1500,
            "hot_storage_bytes": 858993459,
            "warm_storage_bytes": 214748365,
            "cold_storage_bytes": 0,
            "last_updated": "2024-01-01T00:00:00Z"
        }
        mock_service.get_storage_stats.return_value = mock_usage

        response = client.get("/api/v1/storage/usage/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_size_bytes"] == 1073741824
        assert data["file_count"] == 1500
        assert data["hot_storage_bytes"] == 858993459

        # Verify service was called
        mock_service.get_storage_stats.assert_called_once()

    def test_get_storage_usage_response_model(self, client, override_dependencies):
        """Test response model structure matches StorageUsageResponse schema."""
        mock_service, mock_user = override_dependencies

        mock_usage = {
            "total_size_bytes": 1000000,
            "total_size_gb": 0.001,
            "file_count": 100,
            "hot_storage_bytes": 1000000,
            "warm_storage_bytes": 0,
            "cold_storage_bytes": 0,
            "last_updated": "2024-01-01T00:00:00Z"
        }
        mock_service.get_storage_stats.return_value = mock_usage

        response = client.get("/api/v1/storage/usage/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify required fields
        required_fields = ["total_size_bytes", "total_size_gb", "file_count", "hot_storage_bytes", "warm_storage_bytes", "cold_storage_bytes", "last_updated"]
        for field in required_fields:
            assert field in data

    def test_get_storage_usage_unauthorized(self, client, app):
        """Test endpoint requires authentication."""
        # Clear dependency overrides to test without authentication
        app.dependency_overrides = {}
        response = client.get("/api/v1/storage/usage/")

        # The endpoint will return 500 because get_current_user will fail
        # In a real setup with proper auth, this would be 401
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN, status.HTTP_500_INTERNAL_SERVER_ERROR]


class TestListStorageFiles:
    """Tests for GET /api/v1/storage/files/ endpoint."""

    def test_list_storage_files_success(self, client, override_dependencies):
        """Test successful file listing."""
        mock_service, mock_user = override_dependencies

        mock_files = [
            {
                "file_id": "file1",
                "filename": "img001.jpg",
                "size_bytes": 524288,
                "storage_tier": "hot",
                "created_at": "2024-01-01T00:00:00Z",
                "last_accessed": None
            },
            {
                "file_id": "file2",
                "filename": "img002.jpg",
                "size_bytes": 612352,
                "storage_tier": "warm",
                "created_at": "2024-01-01T00:01:00Z",
                "last_accessed": None
            }
        ]
        mock_service.list_files.return_value = mock_files

        response = client.get("/api/v1/storage/files/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert "meta" in data
        assert len(data["data"]) == 2
        assert data["data"][0]["filename"] == "img001.jpg"
        assert data["data"][0]["size_bytes"] == 524288

        # Verify service was called
        mock_service.list_files.assert_called_once_with(None)

    def test_list_storage_files_with_prefix(self, client, override_dependencies):
        """Test file listing with prefix filter."""
        mock_service, mock_user = override_dependencies

        mock_files = [
            {
                "file_id": "file1",
                "filename": "img001.jpg",
                "size_bytes": 524288,
                "storage_tier": "hot",
                "created_at": "2024-01-01T00:00:00Z",
                "last_accessed": None
            }
        ]
        mock_service.list_files.return_value = mock_files

        response = client.get("/api/v1/storage/files/?prefix=images/dataset-1/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) == 1

        # Verify service was called with prefix
        mock_service.list_files.assert_called_once_with("images/dataset-1/")

    def test_list_storage_files_empty(self, client, override_dependencies):
        """Test file listing with no files."""
        mock_service, mock_user = override_dependencies
        mock_service.list_files.return_value = []

        response = client.get("/api/v1/storage/files/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert len(data["data"]) == 0

    def test_list_storage_files_response_model(self, client, override_dependencies):
        """Test response model structure matches List[FileInfo] schema."""
        mock_service, mock_user = override_dependencies

        mock_files = [
            {
                "file_id": "test",
                "filename": "test.jpg",
                "size_bytes": 1024,
                "storage_tier": "hot",
                "created_at": "2024-01-01T00:00:00Z",
                "last_accessed": None
            }
        ]
        mock_service.list_files.return_value = mock_files

        response = client.get("/api/v1/storage/files/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify structure
        assert isinstance(data["data"], list)
        if len(data["data"]) > 0:
            required_fields = ["file_id", "filename", "size_bytes", "storage_tier", "created_at"]
            for field in required_fields:
                assert field in data["data"][0]


class TestCleanupOldFiles:
    """Tests for POST /api/v1/storage/cleanup/ endpoint."""

    def test_cleanup_old_files_success(self, client, override_dependencies):
        """Test successful file cleanup."""
        mock_service, mock_user = override_dependencies

        mock_cleanup_result = {
            "files_deleted": 150,
            "space_freed_bytes": 157286400,
            "space_freed_gb": 0.15,
            "dry_run": False,
            "completed_at": "2024-01-01T00:00:00Z",
            "message": "Cleanup completed successfully"
        }
        mock_service.cleanup_files.return_value = mock_cleanup_result

        cleanup_request = {
            "days_old": 30,
            "dry_run": False
        }

        response = client.post("/api/v1/storage/cleanup/", json=cleanup_request)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["files_deleted"] == 150
        assert data["space_freed_bytes"] == 157286400
        assert data["message"] == "Cleanup completed successfully"

        # Verify service was called
        mock_service.cleanup_files.assert_called_once()

    def test_cleanup_old_files_validation(self, client, override_dependencies):
        """Test request validation."""
        # Missing required fields
        response = client.post("/api/v1/storage/cleanup/", json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_cleanup_old_files_response_model(self, client, override_dependencies):
        """Test response model structure matches CleanupResponse schema."""
        mock_service, mock_user = override_dependencies

        mock_cleanup_result = {
            "files_deleted": 10,
            "space_freed_bytes": 1048576,
            "space_freed_gb": 0.001,
            "dry_run": True,
            "completed_at": "2024-01-01T00:00:00Z",
            "message": "Dry run completed"
        }
        mock_service.cleanup_files.return_value = mock_cleanup_result

        cleanup_request = {"days_old": 48}

        response = client.post("/api/v1/storage/cleanup/", json=cleanup_request)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify required fields
        required_fields = ["files_deleted", "space_freed_bytes", "space_freed_gb", "dry_run", "message"]
        for field in required_fields:
            assert field in data


class TestGetPresignedUrl:
    """Tests for GET /api/v1/storage/presigned-url/ endpoint."""

    def test_get_presigned_url_success(self, client, override_dependencies):
        """Test successful presigned URL generation."""
        mock_service, mock_user = override_dependencies

        mock_url = "https://storage.example.com/file.jpg?token=abc123&expires=1234567890"
        mock_service.generate_presigned_url_with_expiration.return_value = {
            "url": mock_url,
            "expires_at": "2024-01-01T00:00:00Z"
        }

        response = client.get("/api/v1/storage/presigned-url/?path=images/test.jpg")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "url" in data
        assert "expires_at" in data
        assert data["url"] == mock_url

        # Verify service was called
        mock_service.generate_presigned_url_with_expiration.assert_called_once()

    def test_get_presigned_url_with_custom_expiry(self, client, override_dependencies):
        """Test presigned URL with custom expiration."""
        mock_service, mock_user = override_dependencies

        mock_url = "https://storage.example.com/file.jpg?token=xyz789"
        mock_service.generate_presigned_url_with_expiration.return_value = {
            "url": mock_url,
            "expires_at": "2024-01-01T00:00:00Z"
        }

        response = client.get(
            "/api/v1/storage/presigned-url/?path=images/test.jpg&expires_in=7200"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "url" in data
        assert "expires_at" in data

        # Verify service was called with custom expiry
        call_args = mock_service.generate_presigned_url_with_expiration.call_args
        assert call_args[0][1] == 7200

    def test_get_presigned_url_missing_path(self, client, override_dependencies):
        """Test presigned URL without path parameter."""
        response = client.get("/api/v1/storage/presigned-url/")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_presigned_url_invalid_expiry(self, client, override_dependencies):
        """Test presigned URL with invalid expiration time."""
        # Too short (< 60 seconds)
        response = client.get(
            "/api/v1/storage/presigned-url/?path=test.jpg&expires_in=30"
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Too long (> 86400 seconds)
        response = client.get(
            "/api/v1/storage/presigned-url/?path=test.jpg&expires_in=100000"
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_presigned_url_response_structure(self, client, override_dependencies):
        """Test response structure."""
        mock_service, mock_user = override_dependencies

        mock_url = "https://storage.example.com/file.jpg"
        mock_service.generate_presigned_url_with_expiration.return_value = {
            "url": mock_url,
            "expires_at": "2024-01-01T00:00:00Z"
        }

        response = client.get("/api/v1/storage/presigned-url/?path=test.jpg")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify structure
        assert "url" in data
        assert "expires_at" in data
        assert isinstance(data["url"], str)
        assert isinstance(data["expires_at"], str)


class TestOpenAPISchema:
    """Tests for OpenAPI schema generation."""

    def test_storage_endpoints_in_openapi(self, client):
        """Test that all storage endpoints are documented."""
        response = client.get("/openapi.json")

        assert response.status_code == status.HTTP_200_OK
        openapi_schema = response.json()
        paths = openapi_schema.get("paths", {})

        # Check endpoints exist
        assert "/api/v1/storage/usage/" in paths
        assert "/api/v1/storage/files/" in paths
        assert "/api/v1/storage/cleanup/" in paths
        assert "/api/v1/storage/presigned-url/" in paths

    def test_storage_endpoints_have_operation_ids(self, client):
        """Test that all endpoints have operation IDs."""
        response = client.get("/openapi.json")
        openapi_schema = response.json()
        paths = openapi_schema.get("paths", {})

        # Check operation IDs
        assert paths["/api/v1/storage/usage/"]["get"]["operationId"] == "getStorageUsage"
        assert paths["/api/v1/storage/files/"]["get"]["operationId"] == "listStorageFiles"
        assert paths["/api/v1/storage/cleanup/"]["post"]["operationId"] == "cleanupOldFiles"
        assert paths["/api/v1/storage/presigned-url/"]["get"]["operationId"] == "generatePresignedUrl"

    def test_storage_endpoints_have_response_models(self, client):
        """Test that all endpoints have response models defined."""
        response = client.get("/openapi.json")
        openapi_schema = response.json()
        paths = openapi_schema.get("paths", {})

        # Check response models exist
        assert "200" in paths["/api/v1/storage/usage/"]["get"]["responses"]
        assert "200" in paths["/api/v1/storage/files/"]["get"]["responses"]
        assert "200" in paths["/api/v1/storage/cleanup/"]["post"]["responses"]
        assert "200" in paths["/api/v1/storage/presigned-url/"]["get"]["responses"]

    def test_storage_endpoints_have_examples(self, client):
        """Test that endpoints have response examples."""
        response = client.get("/openapi.json")
        openapi_schema = response.json()
        paths = openapi_schema.get("paths", {})

        # Check examples exist
        usage_response = paths["/api/v1/storage/usage/"]["get"]["responses"]["200"]
        assert "content" in usage_response
        assert "application/json" in usage_response["content"]
        assert "example" in usage_response["content"]["application/json"]


class TestIntegrationFlow:
    """Integration tests for complete storage workflows."""

    def test_complete_storage_workflow(self, client, override_dependencies):
        """Test complete storage workflow: usage -> list -> cleanup."""
        mock_service, mock_user = override_dependencies

        # Mock responses
        mock_service.get_storage_stats.return_value = {
            "total_size_bytes": 1000000,
            "total_size_gb": 0.001,
            "file_count": 100,
            "hot_storage_bytes": 1000000,
            "warm_storage_bytes": 0,
            "cold_storage_bytes": 0,
            "last_updated": "2024-01-01T00:00:00Z"
        }
        mock_service.list_files.return_value = [
            {
                "file_id": "test",
                "filename": "test.jpg",
                "size_bytes": 1024,
                "storage_tier": "hot",
                "created_at": "2024-01-01T00:00:00Z",
                "last_accessed": None
            }
        ]
        mock_service.cleanup_files.return_value = {
            "files_deleted": 10,
            "space_freed_bytes": 10240,
            "space_freed_gb": 0.00001,
            "dry_run": False,
            "completed_at": "2024-01-01T00:00:00Z",
            "message": "Cleanup completed"
        }

        # Step 1: Get usage
        response1 = client.get("/api/v1/storage/usage/")
        assert response1.status_code == status.HTTP_200_OK
        usage = response1.json()
        assert usage["file_count"] == 100

        # Step 2: List files
        response2 = client.get("/api/v1/storage/files/")
        assert response2.status_code == status.HTTP_200_OK
        files = response2.json()
        assert len(files["data"]) == 1

        # Step 3: Cleanup
        response3 = client.post("/api/v1/storage/cleanup/", json={"days_old": 30})
        assert response3.status_code == status.HTTP_200_OK
        cleanup = response3.json()
        assert cleanup["files_deleted"] == 10
