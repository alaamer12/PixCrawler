"""
Notification API endpoints.

This module provides the API endpoints for Notification management.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user, get_session
from backend.api.types import CurrentUser
from backend.api.v1.response_models import get_common_responses
from backend.repositories.notification_repository import NotificationRepository
from backend.schemas.notifications import (
    NotificationResponse,
    NotificationUpdate,
)
from backend.services.notification import NotificationService

__all__ = ['router']

router = APIRouter(
    tags=["Notifications"],
    responses=get_common_responses(401, 403, 404, 500),
)


async def get_notification_service(session = Depends(get_session)) -> NotificationService:
    """Dependency to get NotificationService instance."""
    repository = NotificationRepository(session)
    return NotificationService(repository)


@router.get(
    "",
    summary="List Notifications",
    description="Get notifications for the current user.",
)
async def list_notifications(
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
    current_user: CurrentUser = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> dict:
    """
    List notifications.
    
    Args:
        skip: Pagination skip
        limit: Pagination limit
        unread_only: Filter by unread status
        current_user: Current authenticated user
        service: Notification service
        
    Returns:
        List of notifications
    """
    notifications = await service.get_notifications(
        current_user["user_id"], 
        skip, 
        limit, 
        unread_only
    )
    
    # Transform to response model
    data = [NotificationResponse.model_validate(n) for n in notifications]
    
    return {"data": data}


@router.patch(
    "/{notification_id}",
    summary="Mark As Read",
    description="Mark a notification as read.",
)
async def mark_as_read(
    notification_id: int,
    notification_in: NotificationUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> dict:
    """
    Mark a notification as read.
    
    Args:
        notification_id: Notification ID
        notification_in: Update data (is_read=True)
        current_user: Current authenticated user
        service: Notification service
        
    Returns:
        Updated notification status
    """
    if notification_in.is_read:
        await service.mark_as_read(notification_id, current_user["user_id"])
        
    return {"data": {"id": notification_id, "is_read": True}}


@router.post(
    "/mark-all-read",
    summary="Mark All Read",
    description="Mark all notifications as read for the current user.",
)
async def mark_all_read(
    current_user: CurrentUser = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> dict:
    """
    Mark all notifications as read.
    
    Args:
        current_user: Current authenticated user
        service: Notification service
        
    Returns:
        Success status and count
    """
    count = await service.mark_all_as_read(current_user["user_id"])
    return {"data": {"success": True, "count": count}}
