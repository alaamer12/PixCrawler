"""
API integration tests for Authentication endpoints.

Tests cover:
- User profile retrieval
- Token verification
- Profile synchronization
- Response model validation
- OpenAPI schema generation
"""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import status

from backend.services.supabase_auth import SupabaseAuthService


@pytest.fixture
def mock_auth_service():
    """Create mock Supabase auth service."""
    return AsyncMock(spec=SupabaseAuthService)


@pytest.fixture
def mock_user():
    """Create mock authenticated user."""
    user_id = uuid4()
    return {
        "user_id": str(user_id),
        "email": "test@example.com",
        "profile": {
            "id": str(user_id),
            "email": "test@example.com",
            "full_name": "Test User",
            "avatar_url": "https://example.com/avatar.jpg",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        },
        "user_metadata": {
            "full_name": "Test User",
            "avatar_url": "https://example.com/avatar.jpg"
        }
    }


@pytest.fixture
def override_dependencies(app, mock_auth_service, mock_user):
    """Override FastAPI dependencies for testing."""
    from backend.api.dependencies import get_current_user, get_supabase_auth_service, get_auth_service

    app.dependency_overrides[get_supabase_auth_service] = lambda: mock_auth_service
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    app.dependency_overrides[get_current_user] = lambda: mock_user

    yield mock_auth_service, mock_user

    app.dependency_overrides = {}


class TestGetCurrentUserProfile:
    """Tests for GET /api/v1/auth/me endpoint."""

    def test_get_current_user_profile_success(self, client, override_dependencies):
        """Test successful user profile retrieval."""
        mock_service, mock_user = override_dependencies

        response = client.get("/api/v1/auth/me")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == mock_user["profile"]["id"]
        assert data["email"] == mock_user["email"]
        assert data["full_name"] == "Test User"
        assert data["is_active"] is True
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_current_user_profile_response_model(self, client, override_dependencies):
        """Test response model structure matches UserResponse schema."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify all required fields are present
        required_fields = ["id", "email", "full_name", "is_active", "created_at", "updated_at"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_get_current_user_profile_unauthorized(self, client, app):
        """Test endpoint requires authentication."""
        # Don't override dependencies - no auth
        response = client.get("/api/v1/auth/me")

        # Should fail without authentication
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


class TestVerifyToken:
    """Tests for POST /api/v1/auth/verify-token endpoint."""

    def test_verify_token_success(self, client, override_dependencies):
        """Test successful token verification."""
        mock_service, mock_user = override_dependencies

        response = client.post("/api/v1/auth/verify-token")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["valid"] is True
        assert "user" in data
        assert data["user"]["id"] == mock_user["user_id"]
        assert data["user"]["email"] == mock_user["email"]
        assert "profile" in data["user"]

    def test_verify_token_response_model(self, client, override_dependencies):
        """Test response model structure matches TokenVerificationResponse schema."""
        response = client.post("/api/v1/auth/verify-token")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify structure
        assert "valid" in data
        assert isinstance(data["valid"], bool)
        assert "user" in data
        assert "id" in data["user"]
        assert "email" in data["user"]
        assert "profile" in data["user"]

    def test_verify_token_unauthorized(self, client, app):
        """Test endpoint requires authentication."""
        response = client.post("/api/v1/auth/verify-token")

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


class TestSyncUserProfile:
    """Tests for POST /api/v1/auth/sync-profile endpoint."""

    def test_sync_profile_create_new(self, client, override_dependencies):
        """Test profile creation when profile doesn't exist."""
        mock_service, mock_user = override_dependencies

        # Mock sync_profile to return 'created'
        mock_service.sync_profile.return_value = "created"

        response = client.post("/api/v1/auth/sync-profile")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "created" in data["message"].lower()

        # Verify sync_profile was called
        mock_service.sync_profile.assert_called_once()

    def test_sync_profile_update_existing(self, client, override_dependencies):
        """Test profile update when profile exists."""
        mock_service, mock_user = override_dependencies

        # Mock sync_profile to return 'updated'
        mock_service.sync_profile.return_value = "updated"

        response = client.post("/api/v1/auth/sync-profile")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "updated" in data["message"].lower()

        # Verify sync_profile was called
        mock_service.sync_profile.assert_called_once()

    def test_sync_profile_response_model(self, client, override_dependencies):
        """Test response model structure matches ProfileSyncResponse schema."""
        mock_service, mock_user = override_dependencies
        
        # Mock sync_profile to return 'created'
        mock_service.sync_profile.return_value = "created"

        response = client.post("/api/v1/auth/sync-profile")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify structure
        assert "message" in data
        assert isinstance(data["message"], str)

    def test_sync_profile_unauthorized(self, client, app):
        """Test endpoint requires authentication."""
        response = client.post("/api/v1/auth/sync-profile")

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


class TestOpenAPISchema:
    """Tests for OpenAPI schema generation."""

    def test_auth_endpoints_in_openapi(self, client):
        """Test that all auth endpoints are documented in OpenAPI schema."""
        response = client.get("/openapi.json")

        assert response.status_code == status.HTTP_200_OK
        openapi_schema = response.json()

        # Check that auth endpoints exist
        paths = openapi_schema.get("paths", {})
        assert "/api/v1/auth/me" in paths
        assert "/api/v1/auth/verify-token" in paths
        assert "/api/v1/auth/sync-profile" in paths

    def test_auth_endpoints_have_operation_ids(self, client):
        """Test that all auth endpoints have operation IDs."""
        response = client.get("/openapi.json")
        openapi_schema = response.json()
        paths = openapi_schema.get("paths", {})

        # Check operation IDs
        assert paths["/api/v1/auth/me"]["get"]["operationId"] == "getCurrentUserProfile"
        assert paths["/api/v1/auth/verify-token"]["post"]["operationId"] == "verifyAuthToken"
        assert paths["/api/v1/auth/sync-profile"]["post"]["operationId"] == "syncUserProfile"

    def test_auth_endpoints_have_response_models(self, client):
        """Test that all auth endpoints have response models defined."""
        response = client.get("/openapi.json")
        openapi_schema = response.json()
        paths = openapi_schema.get("paths", {})

        # Check response models exist
        assert "200" in paths["/api/v1/auth/me"]["get"]["responses"]
        assert "200" in paths["/api/v1/auth/verify-token"]["post"]["responses"]
        assert "200" in paths["/api/v1/auth/sync-profile"]["post"]["responses"]

    def test_auth_endpoints_have_examples(self, client):
        """Test that auth endpoints have response examples."""
        response = client.get("/openapi.json")
        openapi_schema = response.json()
        paths = openapi_schema.get("paths", {})

        # Check examples exist
        me_response = paths["/api/v1/auth/me"]["get"]["responses"]["200"]
        assert "content" in me_response
        assert "application/json" in me_response["content"]
        assert "example" in me_response["content"]["application/json"]


class TestIntegrationFlow:
    """Integration tests for complete authentication flows."""

    def test_complete_auth_flow(self, client, override_dependencies):
        """Test complete authentication flow: profile -> verify -> sync."""
        mock_service, mock_user = override_dependencies
        mock_service.get_user_profile.return_value = {"id": mock_user["user_id"]}

        # Step 1: Get profile
        response1 = client.get("/api/v1/auth/me")
        assert response1.status_code == status.HTTP_200_OK
        profile = response1.json()
        assert profile["email"] == mock_user["email"]

        # Step 2: Verify token
        response2 = client.post("/api/v1/auth/verify-token")
        assert response2.status_code == status.HTTP_200_OK
        verification = response2.json()
        assert verification["valid"] is True

        # Step 3: Sync profile
        mock_service.sync_profile.return_value = "updated"
        
        response3 = client.post("/api/v1/auth/sync-profile")
        assert response3.status_code == status.HTTP_200_OK
        sync_result = response3.json()
        assert "message" in sync_result
