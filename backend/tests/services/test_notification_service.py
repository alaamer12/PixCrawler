"""
Unit tests for NotificationService.
"""

import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import HTTPException

from backend.models import Notification
from backend.schemas.notifications import NotificationCreate
from backend.services.notification import NotificationService


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def notification_service(mock_repo):
    return NotificationService(mock_repo)


@pytest.mark.asyncio
async def test_get_notifications(notification_service, mock_repo):
    user_id = uuid4()
    mock_notifications = [Notification(id=1, user_id=user_id, title="Test", message="Test message", type_="info")]
    mock_repo.get_by_user.return_value = mock_notifications

    result = await notification_service.get_notifications(user_id)

    assert result == mock_notifications
    mock_repo.get_by_user.assert_called_once_with(user_id, 0, 50, False)


@pytest.mark.asyncio
async def test_create_notification(notification_service, mock_repo):
    user_id = uuid4()
    notification_in = NotificationCreate(
        user_id=user_id, 
        title="Test", 
        message="Message", 
        type="info"
    )
    # Convert type to type_ for model
    data = notification_in.model_dump()
    data['type_'] = data.pop('type')
    mock_notification = Notification(id=1, **data)
    mock_repo.create.return_value = mock_notification

    result = await notification_service.create_notification(notification_in)

    assert result == mock_notification
    mock_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_mark_as_read_success(notification_service, mock_repo):
    user_id = uuid4()
    notification_id = 1
    mock_repo.mark_as_read.return_value = True

    result = await notification_service.mark_as_read(notification_id, user_id)

    assert result is True
    mock_repo.mark_as_read.assert_called_once_with(notification_id, user_id)


@pytest.mark.asyncio
async def test_mark_as_read_not_found(notification_service, mock_repo):
    user_id = uuid4()
    notification_id = 1
    mock_repo.mark_as_read.return_value = False
    mock_repo.get.return_value = None

    with pytest.raises(HTTPException) as exc:
        await notification_service.mark_as_read(notification_id, user_id)
    
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_mark_as_read_forbidden(notification_service, mock_repo):
    user_id = uuid4()
    other_user_id = uuid4()
    notification_id = 1
    mock_repo.mark_as_read.return_value = False
    mock_repo.get.return_value = Notification(id=notification_id, user_id=other_user_id, title="Test", message="Test", type_="info")

    with pytest.raises(HTTPException) as exc:
        await notification_service.mark_as_read(notification_id, user_id)
    
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_mark_all_as_read(notification_service, mock_repo):
    user_id = uuid4()
    mock_repo.mark_all_as_read.return_value = 5

    result = await notification_service.mark_all_as_read(user_id)

    assert result == 5
    mock_repo.mark_all_as_read.assert_called_once_with(user_id)
