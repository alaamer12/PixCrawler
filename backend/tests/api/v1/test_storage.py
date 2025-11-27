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

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi import status

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
    from backend.api.v1.endpoints.storage import get_storage_service
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
            "total_files": 1500,
            "used_percentage": 45.5,
            "breakdown": {
                "images": {"count": 1200, "size_bytes": 858993459},
                "exports": {"count": 300, "size_bytes": 214748365}
            }
        }
        mock_service.get_storage_stats.return_value = mock_usage

        response = client.get("/api/v1/storage/usage/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_size_bytes"] == 1073741824
        assert data["total_files"] == 1500
        assert data["used_percentage"] == 45.5
        assert "breakdown" in data
        
        # Verify service was called
        mock_service.get_storage_stats.assert_called_once()

    def test_get_storage_usage_response_model(self, client, override_dependencies):
        """Test response model structure matches StorageUsageResponse schema."""
        mock_service, mock_user = override_dependencies
        
        mock_usage = {
            "total_size_bytes": 1000000,
            "total_files": 100,
            "used_percentage": 10.0,
            "breakdown": {}
        }
        mock_service.get_storage_stats.return_value = mock_usage

        response = client.get("/api/v1/storage/usage/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify required fields
        required_fields = ["total_size_bytes", "total_files", "used_percentage", "breakdown"]
        for field in required_fields:
            assert field in data

    def test_get_storage_usage_unauthorized(self, client, app):
        """Test endpoint requires authentication."""
        response = client.get("/api/v1/storage/usage/")

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


class TestListStorageFiles:
    """Tests for GET /api/v1/storage/files/ endpoint."""

    def test_list_storage_files_success(self, client, override_dependencies):
        """Test successful file listing."""
        mock_service, mock_user = override_dependencies
        
        mock_files = [
            {
                "path": "images/dataset-1/img001.jpg",
                "size_bytes": 524288,
                "created_at": "2024-01-01T00:00:00Z",
                "content_type": "image/jpeg"
            },
            {
                "path": "images/dataset-1/img002.jpg",
                "size_bytes": 612352,
                "created_at": "2024-01-01T00:01:00Z",
                "content_type": "image/jpeg"
            }
        ]
        mock_service.list_files.return_value = mock_files

        response = client.get("/api/v1/storage/files/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["path"] == "images/dataset-1/img001.jpg"
        assert data[0]["size_bytes"] == 524288
        
        # Verify service was called
        mock_service.list_files.assert_called_once_with(None)

    def test_list_storage_files_with_prefix(self, client, override_dependencies):
        """Test file listing with prefix filter."""
        mock_service, mock_user = override_dependencies
        
        mock_files = [
            {
                "path": "images/dataset-1/img001.jpg",
                "size_bytes": 524288,
                "created_at": "2024-01-01T00:00:00Z",
                "content_type": "image/jpeg"
            }
        ]
        mock_service.list_files.return_value = mock_files

        response = client.get("/api/v1/storage/files/?prefix=images/dataset-1/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        
        # Verify service was called with prefix
        mock_service.list_files.assert_called_once_with("images/dataset-1/")

    def test_list_storage_files_empty(self, client, override_dependencies):
        """Test file listing with no files."""
        mock_service, mock_user = override_dependencies
        mock_service.list_files.return_value = []

        response = client.get("/api/v1/storage/files/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_storage_files_response_model(self, client, override_dependencies):
        """Test response model structure matches List[FileInfo] schema."""
        mock_service, mock_user = override_dependencies
        
        mock_files = [
            {
                "path": "test.jpg",
                "size_bytes": 1024,
                "created_at": "2024-01-01T00:00:00Z",
                "content_type": "image/jpeg"
            }
        ]
        mock_service.list_files.return_value = mock_files

        response = client.get("/api/v1/storage/files/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify structure
        assert isinstance(data, list)
        if len(data) > 0:
            required_fields = ["path", "size_bytes", "created_at", "content_type"]
            for field in required_fields:
                assert field in data[0]


class TestCleanupOldFiles:
    """Tests for POST /api/v1/storage/cleanup/ endpoint."""

    def test_cleanup_old_files_success(self, client, override_dependencies):
        """Test successful file cleanup."""
        mock_service, mock_user = override_dependencies
        
        mock_cleanup_result = {
            "deleted_count": 150,
            "freed_bytes": 157286400,
            "duration_seconds": 2.5
        }
        mock_service.cleanup_files.return_value = mock_cleanup_result

        cleanup_request = {
            "age_hours": 24,
            "prefix": "temp/"
        }

        response = client.post("/api/v1/storage/cleanup/", json=cleanup_request)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["deleted_count"] == 150
        assert data["freed_bytes"] == 157286400
        assert data["duration_seconds"] == 2.5
        
        # Verify service was called
        mock_service.cleanup_files.assert_called_once_with(
            age_hours=24,
            prefix="temp/"
        )

    def test_cleanup_old_files_validation(self, client, override_dependencies):
        """Test request validation."""
        # Missing required fields
        response = client.post("/api/v1/storage/cleanup/", json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_cleanup_old_files_response_model(self, client, override_dependencies):
        """Test response model structure matches CleanupResponse schema."""
        mock_service, mock_user = override_dependencies
        
        mock_cleanup_result = {
            "deleted_count": 10,
            "freed_bytes": 1048576,
            "duration_seconds": 0.5
        }
        mock_service.cleanup_files.return_value = mock_cleanup_result

        cleanup_request = {"age_hours": 48}

        response = client.post("/api/v1/storage/cleanup/", json=cleanup_request)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify required fields
        required_fields = ["deleted_count", "freed_bytes", "duration_seconds"]
        for field in required_fields:
            assert field in data


class TestGetPresignedUrl:
    """Tests for GET /api/v1/storage/presigned-url/ endpoint."""

    def test_get_presigned_url_success(self, client, override_dependencies):
        """Test successful presigned URL generation."""
        mock_service, mock_user = override_dependencies
        
        mock_url = "https://storage.example.com/file.jpg?token=abc123&expires=1234567890"
        mock_service.storage.generate_presigned_url.return_value = mock_url

        response = client.get("/api/v1/storage/presigned-url/?path=images/test.jpg")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "url" in data
        assert "expires_at" in data
        assert data["url"] == mock_url
        
        # Verify service was called
        mock_service.storage.generate_presigned_url.assert_called_once()

    def test_get_presigned_url_with_custom_expiry(self, client, override_dependencies):
        """Test presigned URL with custom expiration."""
        mock_service, mock_user = override_dependencies
        
        mock_url = "https://storage.example.com/file.jpg?token=xyz789"
        mock_service.storage.generate_presigned_url.return_value = mock_url

        response = client.get(
            "/api/v1/storage/presigned-url/?path=images/test.jpg&expires_in=7200"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "url" in data
        assert "expires_at" in data
        
        # Verify service was called with custom expiry
        call_args = mock_service.storage.generate_presigned_url.call_args
        assert call_args[1]["expires_in"] == 7200

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
        mock_service.storage.generate_presigned_url.return_value = mock_url

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
            "total_files": 100,
            "used_percentage": 50.0,
            "breakdown": {}
        }
        mock_service.list_files.return_value = [
            {"path": "test.jpg", "size_bytes": 1024, "created_at": "2024-01-01T00:00:00Z", "content_type": "image/jpeg"}
        ]
        mock_service.cleanup_files.return_value = {
            "deleted_count": 10,
            "freed_bytes": 10240,
            "duration_seconds": 0.5
        }

        # Step 1: Get usage
        response1 = client.get("/api/v1/storage/usage/")
        assert response1.status_code == status.HTTP_200_OK
        usage = response1.json()
        assert usage["total_files"] == 100

        # Step 2: List files
        response2 = client.get("/api/v1/storage/files/")
        assert response2.status_code == status.HTTP_200_OK
        files = response2.json()
        assert len(files) == 1

        # Step 3: Cleanup
        response3 = client.post("/api/v1/storage/cleanup/", json={"age_hours": 24})
        assert response3.status_code == status.HTTP_200_OK
        cleanup = response3.json()
        assert cleanup["deleted_count"] == 10
