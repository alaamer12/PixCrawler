"""
Notification API endpoints.

This module provides the API endpoints for Notification management.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user, get_session
from backend.api.types import CurrentUser
from backend.api.v1.response_models import get_common_responses
from backend.repositories.notification_repository import NotificationRepository
from backend.schemas.notifications import (
    NotificationListResponse,
    NotificationMarkAllReadResponse,
    NotificationMarkReadResponse,
    NotificationResponse,
    NotificationUpdate,
)
from backend.services.notification import NotificationService

__all__ = ['router']

router = APIRouter(
    tags=["Notifications"],
    responses=get_common_responses(401, 403, 404, 500),
)


def get_notification_service(session: AsyncSession = Depends(get_session)) -> NotificationService:
    """
    Dependency injection for NotificationService.

    Creates service with required repository following the pattern:
    get_service(session) -> Service where service receives repository.

    Args:
        session: Database session (injected by FastAPI)

    Returns:
        NotificationService instance with injected repository
    """
    # Create repository instance
    repository = NotificationRepository(session)
    
    # Inject repository into service
    return NotificationService(repository)


@router.get(
    "/",
    response_model=NotificationListResponse,
    summary="List Notifications",
    description="Retrieve a paginated list of notifications for the authenticated user with optional filtering by read status.",
    response_description="Paginated list of notifications with metadata",
    operation_id="listNotifications",
    responses={
        200: {
            "description": "Successfully retrieved notifications",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {
                                "id": 1,
                                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                                "title": "Crawl Job Completed",
                                "message": "Your crawl job 'Animals Dataset' has completed successfully.",
                                "type": "success",
                                "category": "crawl_job",
                                "icon": "check-circle",
                                "color": "#10b981",
                                "action_url": "/dashboard/projects/123",
                                "action_label": "View Project",
                                "is_read": False,
                                "read_at": None,
                                "created_at": "2024-01-27T10:00:00Z",
                                "metadata": {}
                            }
                        ],
                        "meta": {
                            "total": 10,
                            "skip": 0,
                            "limit": 50
                        }
                    }
                }
            }
        },
        **get_common_responses(401, 500)
    }
)
async def list_notifications(
    current_user: CurrentUser,
    service: NotificationService = Depends(get_notification_service),
    skip: int = Query(0, ge=0, description="Number of items to skip for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Maximum items to return (max: 100)"),
    unread_only: bool = Query(False, description="Filter to unread notifications only"),
) -> NotificationListResponse:
    """
    List all notifications for the current user with pagination.
    
    Retrieves notifications filtered by user ownership with optional
    filtering by read status. Results are ordered by creation date
    descending for most recent first.
    
    **Authentication Required:** Bearer token
    
    **Query Parameters:**
    - `skip` (int): Pagination offset (default: 0)
    - `limit` (int): Items per page (default: 50, max: 100)
    - `unread_only` (bool): Show only unread notifications (default: false)
    
    Args:
        skip: Number of items to skip for pagination
        limit: Maximum number of items to return
        unread_only: Filter by unread status
        current_user: Current authenticated user (injected)
        service: Notification service instance (injected)
    
    Returns:
        NotificationListResponse with list of notifications and pagination metadata
    
    Raises:
        HTTPException: 401 if authentication fails
        HTTPException: 500 if database query fails
    """
    try:
        notifications = await service.get_notifications(
            current_user["user_id"], 
            skip, 
            limit, 
            unread_only
        )
        
        # Get total count for pagination metadata
        total = await service.count_notifications(
            current_user["user_id"],
            unread_only
        )
        
        # Transform to response model
        data = [NotificationResponse.model_validate(n) for n in notifications]
        
        return NotificationListResponse(
            data=data,
            meta={"total": total, "skip": skip, "limit": limit}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notifications"
        )


@router.patch(
    "/{notification_id}",
    response_model=NotificationMarkReadResponse,
    summary="Mark Notification As Read",
    description="Mark a specific notification as read for the authenticated user.",
    response_description="Updated notification status",
    operation_id="markNotificationAsRead",
    responses={
        200: {
            "description": "Successfully marked notification as read",
            "content": {
                "application/json": {
                    "example": {
                        "data": {
                            "id": 1,
                            "is_read": True
                        }
                    }
                }
            }
        },
        **get_common_responses(401, 404, 500)
    }
)
async def mark_as_read(
    notification_id: int,
    notification_in: NotificationUpdate,
    current_user: CurrentUser,
    service: NotificationService = Depends(get_notification_service),
) -> NotificationMarkReadResponse:
    """
    Mark a specific notification as read.
    
    Updates the read status of a notification belonging to the current user.
    Only the notification owner can mark their notifications as read.
    
    **Authentication Required:** Bearer token
    
    Args:
        notification_id: Notification ID to mark as read
        notification_in: Update data containing is_read status
        current_user: Current authenticated user (injected)
        service: Notification service instance (injected)
    
    Returns:
        NotificationMarkReadResponse with updated notification status
    
    Raises:
        HTTPException: 401 if authentication fails
        HTTPException: 404 if notification not found or access denied
        HTTPException: 500 if update fails
    """
    try:
        if notification_in.is_read:
            await service.mark_as_read(notification_id, current_user["user_id"])
            
        return NotificationMarkReadResponse(
            data={"id": notification_id, "is_read": True}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read"
        )


@router.post(
    "/mark-all-read",
    response_model=NotificationMarkAllReadResponse,
    summary="Mark All Notifications As Read",
    description="Mark all notifications as read for the authenticated user in a single operation.",
    response_description="Bulk update result with count of notifications marked as read",
    operation_id="markAllNotificationsAsRead",
    responses={
        200: {
            "description": "Successfully marked all notifications as read",
            "content": {
                "application/json": {
                    "example": {
                        "data": {
                            "success": True,
                            "count": 5
                        }
                    }
                }
            }
        },
        **get_common_responses(401, 500)
    }
)
async def mark_all_read(
    current_user: CurrentUser,
    service: NotificationService = Depends(get_notification_service),
) -> NotificationMarkAllReadResponse:
    """
    Mark all notifications as read for the current user.
    
    Performs a bulk update operation to mark all unread notifications
    as read for the authenticated user. This is useful for clearing
    notification badges and marking everything as acknowledged.
    
    **Authentication Required:** Bearer token
    
    Args:
        current_user: Current authenticated user (injected)
        service: Notification service instance (injected)
    
    Returns:
        NotificationMarkAllReadResponse with success status and count of updated notifications
    
    Raises:
        HTTPException: 401 if authentication fails
        HTTPException: 500 if bulk update fails
    """
    try:
        count = await service.mark_all_as_read(current_user["user_id"])
        return NotificationMarkAllReadResponse(
            data={"success": True, "count": count}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark all notifications as read"
        )
