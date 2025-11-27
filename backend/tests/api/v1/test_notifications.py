"""
API integration tests for Notifications.
"""

import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from backend.models import Notification
from backend.services.notification import NotificationService


@pytest.fixture
def mock_notification_service():
    return AsyncMock(spec=NotificationService)


@pytest.fixture
def override_dependencies(app, mock_notification_service):
    from backend.api.v1.endpoints.notifications import get_notification_service
    from backend.api.dependencies import get_current_user

    user_id = uuid4()
    mock_user = {
        "user_id": user_id,
        "email": "test@example.com",
        "profile": {"id": str(user_id), "email": "test@example.com"}
    }

    app.dependency_overrides[get_notification_service] = lambda: mock_notification_service
    app.dependency_overrides[get_current_user] = lambda: mock_user

    yield mock_notification_service, user_id

    app.dependency_overrides = {}


def test_list_notifications(client, override_dependencies):
    mock_service, user_id = override_dependencies
    mock_notifications = [
        Notification(
            id=1,
            user_id=user_id,
            title="Test",
            message="Msg",
            type="info",
            is_read=False,
            created_at=datetime("2024-01-01T00:00:00Z"),
        )
    ]
    mock_service.get_notifications.return_value = mock_notifications

    response = client.get("/api/v1/notifications")

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["title"] == "Test"
    mock_service.get_notifications.assert_called_once_with(user_id, 0, 50, False)


def test_mark_as_read(client, override_dependencies):
    mock_service, user_id = override_dependencies
    mock_service.mark_as_read.return_value = True

    response = client.patch("/api/v1/notifications/1", json={"is_read": True})

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["is_read"] is True
    mock_service.mark_as_read.assert_called_once_with(1, user_id)


def test_mark_all_read(client, override_dependencies):
    mock_service, user_id = override_dependencies
    mock_service.mark_all_as_read.return_value = 5

    response = client.post("/api/v1/notifications/mark-all-read")

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["count"] == 5
    mock_service.mark_all_as_read.assert_called_once_with(user_id)
