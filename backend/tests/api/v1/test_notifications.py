"""
API integration tests for Notifications endpoints.

Tests cover:
- List notifications with pagination
- Mark notification as read
- Mark all notifications as read
- Response model validation
- OpenAPI schema generation
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import status

from backend.models import Notification
from backend.services.notification import NotificationService


@pytest.fixture
def mock_notification_service():
    """Create mock notification service."""
    return AsyncMock(spec=NotificationService)


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
def sample_notification(mock_user):
    """Create sample notification for testing."""
    return Notification(
        id=1,
        user_id=uuid4(),
        title="Test Notification",
        message="Test message",
        type="info",
        category="system",
        is_read=False,
        created_at=datetime(2024, 1, 1, 10, 0, 0),
    )


@pytest.fixture
def override_dependencies(app, mock_notification_service, mock_user):
    """Override FastAPI dependencies for testing."""
    from backend.api.v1.endpoints.notifications import get_notification_service
    from backend.api.dependencies import get_current_user

    app.dependency_overrides[get_notification_service] = lambda: mock_notification_service
    app.dependency_overrides[get_current_user] = lambda: mock_user

    yield mock_notification_service, mock_user

    app.dependency_overrides = {}


class TestListNotifications:
    """Tests for GET /api/v1/notifications endpoint."""

    def test_list_notifications_success(self, client, override_dependencies, sample_notification):
        """Test successful notifications listing."""
        mock_service, mock_user = override_dependencies
        mock_service.get_notifications.return_value = [sample_notification]
        mock_service.count_notifications.return_value = 1

        response = client.get("/api/v1/notifications")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert "meta" in data
        assert len(data["data"]) == 1
        assert data["data"][0]["title"] == "Test Notification"
        assert data["meta"]["total"] == 1
        
        # Verify service was called
        mock_service.get_notifications.assert_called_once()

    def test_list_notifications_with_pagination(self, client, override_dependencies):
        """Test notifications listing with pagination parameters."""
        mock_service, mock_user = override_dependencies
        mock_service.get_notifications.return_value = []
        mock_service.count_notifications.return_value = 0

        response = client.get("/api/v1/notifications?skip=10&limit=25")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["meta"]["skip"] == 10
        assert data["meta"]["limit"] == 25

    def test_list_notifications_unread_only(self, client, override_dependencies):
        """Test filtering unread notifications only."""
        mock_service, mock_user = override_dependencies
        mock_service.get_notifications.return_value = []
        mock_service.count_notifications.return_value = 0

        response = client.get("/api/v1/notifications?unread_only=true")

        assert response.status_code == status.HTTP_200_OK
        
        # Verify service was called with unread_only=True
        call_args = mock_service.get_notifications.call_args
        assert call_args[1]["unread_only"] is True

    def test_list_notifications_response_model(self, client, override_dependencies, sample_notification):
        """Test response model structure matches NotificationListResponse schema."""
        mock_service, mock_user = override_dependencies
        mock_service.get_notifications.return_value = [sample_notification]
        mock_service.count_notifications.return_value = 1

        response = client.get("/api/v1/notifications")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify structure
        assert "data" in data
        assert "meta" in data
        assert isinstance(data["data"], list)
        assert isinstance(data["meta"], dict)
        assert "total" in data["meta"]
        assert "skip" in data["meta"]
        assert "limit" in data["meta"]

    def test_list_notifications_unauthorized(self, client, app):
        """Test endpoint requires authentication."""
        response = client.get("/api/v1/notifications")

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


class TestMarkAsRead:
    """Tests for PATCH /api/v1/notifications/{notification_id} endpoint."""

    def test_mark_as_read_success(self, client, override_dependencies):
        """Test successfully marking notification as read."""
        mock_service, mock_user = override_dependencies
        mock_service.mark_as_read.return_value = True

        response = client.patch("/api/v1/notifications/1", json={"is_read": True})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert data["data"]["id"] == 1
        assert data["data"]["is_read"] is True
        
        # Verify service was called
        mock_service.mark_as_read.assert_called_once()

    def test_mark_as_read_not_found(self, client, override_dependencies):
        """Test marking non-existent notification as read."""
        mock_service, mock_user = override_dependencies
        mock_service.mark_as_read.return_value = False

        response = client.patch("/api/v1/notifications/999", json={"is_read": True})

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_mark_as_read_response_model(self, client, override_dependencies):
        """Test response model structure."""
        mock_service, mock_user = override_dependencies
        mock_service.mark_as_read.return_value = True

        response = client.patch("/api/v1/notifications/1", json={"is_read": True})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify structure
        assert "data" in data
        assert "id" in data["data"]
        assert "is_read" in data["data"]


class TestMarkAllRead:
    """Tests for POST /api/v1/notifications/mark-all-read endpoint."""

    def test_mark_all_read_success(self, client, override_dependencies):
        """Test successfully marking all notifications as read."""
        mock_service, mock_user = override_dependencies
        mock_service.mark_all_as_read.return_value = 5

        response = client.post("/api/v1/notifications/mark-all-read")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert data["data"]["success"] is True
        assert data["data"]["count"] == 5
        
        # Verify service was called
        mock_service.mark_all_as_read.assert_called_once()

    def test_mark_all_read_no_notifications(self, client, override_dependencies):
        """Test marking all as read when no unread notifications exist."""
        mock_service, mock_user = override_dependencies
        mock_service.mark_all_as_read.return_value = 0

        response = client.post("/api/v1/notifications/mark-all-read")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert data["data"]["success"] is True
        assert data["data"]["count"] == 0

    def test_mark_all_read_response_model(self, client, override_dependencies):
        """Test response model structure."""
        mock_service, mock_user = override_dependencies
        mock_service.mark_all_as_read.return_value = 3

        response = client.post("/api/v1/notifications/mark-all-read")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify structure
        assert "data" in data
        assert "success" in data["data"]
        assert "count" in data["data"]


class TestOpenAPISchema:
    """Tests for OpenAPI schema generation."""

    def test_notifications_endpoints_in_openapi(self, client):
        """Test that all notification endpoints are documented."""
        response = client.get("/openapi.json")
        
        assert response.status_code == status.HTTP_200_OK
        openapi_schema = response.json()
        paths = openapi_schema.get("paths", {})
        
        # Check endpoints exist
        assert "/api/v1/notifications" in paths
        assert "/api/v1/notifications/{notification_id}" in paths
        assert "/api/v1/notifications/mark-all-read" in paths

    def test_notifications_endpoints_have_operation_ids(self, client):
        """Test that all endpoints have operation IDs."""
        response = client.get("/openapi.json")
        openapi_schema = response.json()
        paths = openapi_schema.get("paths", {})
        
        # Check operation IDs
        assert paths["/api/v1/notifications"]["get"]["operationId"] == "listNotifications"
        assert paths["/api/v1/notifications/{notification_id}"]["patch"]["operationId"] == "markNotificationAsRead"
        assert paths["/api/v1/notifications/mark-all-read"]["post"]["operationId"] == "markAllNotificationsAsRead"

    def test_notifications_endpoints_have_response_models(self, client):
        """Test that all endpoints have response models defined."""
        response = client.get("/openapi.json")
        openapi_schema = response.json()
        paths = openapi_schema.get("paths", {})
        
        # Check response models exist
        assert "200" in paths["/api/v1/notifications"]["get"]["responses"]
        assert "200" in paths["/api/v1/notifications/{notification_id}"]["patch"]["responses"]
        assert "200" in paths["/api/v1/notifications/mark-all-read"]["post"]["responses"]


class TestIntegrationFlow:
    """Integration tests for complete notification workflows."""

    def test_complete_notification_workflow(self, client, override_dependencies, sample_notification):
        """Test complete notification workflow: list -> mark one -> mark all."""
        mock_service, mock_user = override_dependencies
        
        # Mock responses
        mock_service.get_notifications.return_value = [sample_notification]
        mock_service.count_notifications.return_value = 1
        mock_service.mark_as_read.return_value = True
        mock_service.mark_all_as_read.return_value = 5

        # Step 1: List notifications
        response1 = client.get("/api/v1/notifications")
        assert response1.status_code == status.HTTP_200_OK
        notifications = response1.json()
        assert len(notifications["data"]) == 1

        # Step 2: Mark one as read
        response2 = client.patch("/api/v1/notifications/1", json={"is_read": True})
        assert response2.status_code == status.HTTP_200_OK

        # Step 3: Mark all as read
        response3 = client.post("/api/v1/notifications/mark-all-read")
        assert response3.status_code == status.HTTP_200_OK
