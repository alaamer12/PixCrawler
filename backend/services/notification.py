"""
Notification service for business logic.

This module provides the service layer for Notification operations,
coordinating between the API and Repository layers.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status

from backend.models import Notification
from backend.repositories.notification_repository import NotificationRepository
from backend.schemas.notifications import NotificationCreate, NotificationUpdate

__all__ = ['NotificationService']


class NotificationService:
    """
    Service for Notification business logic.
    
    Handles notification retrieval, creation, and status updates.
    """
    
    def __init__(self, notification_repository: NotificationRepository):
        """
        Initialize Notification service.
        
        Args:
            notification_repository: Notification repository instance
        """
        self.repository = notification_repository
    
    async def get_notifications(
        self, 
        user_id: UUID, 
        skip: int = 0, 
        limit: int = 50,
        unread_only: bool = False
    ) -> List[Notification]:
        """
        Get notifications for a user.
        
        Args:
            user_id: User UUID
            skip: Pagination skip
            limit: Pagination limit
            unread_only: Filter by unread status
            
        Returns:
            List of notifications
        """
        return await self.repository.get_by_user(user_id, skip, limit, unread_only)
    
    async def get_unread_count(self, user_id: UUID) -> int:
        """
        Get count of unread notifications.
        
        Args:
            user_id: User UUID
            
        Returns:
            Count of unread notifications
        """
        return await self.repository.get_unread_count(user_id)
    
    async def count_notifications(
        self, 
        user_id: UUID,
        unread_only: bool = False
    ) -> int:
        """
        Get total count of notifications for a user.
        
        Args:
            user_id: User UUID
            unread_only: Filter by unread status
            
        Returns:
            Total count of notifications
        """
        return await self.repository.count_by_user(user_id, unread_only)
    
    async def create_notification(self, notification_in: NotificationCreate) -> Notification:
        """
        Create a new notification.
        
        Args:
            notification_in: Notification creation data
            
        Returns:
            Created notification
        """
        return await self.repository.create(notification_in.model_dump())
    
    async def mark_as_read(self, notification_id: int, user_id: UUID) -> bool:
        """
        Mark a notification as read.
        
        Args:
            notification_id: Notification ID
            user_id: User UUID
            
        Returns:
            True if updated
            
        Raises:
            HTTPException: If notification not found or access denied
        """
        updated = await self.repository.mark_as_read(notification_id, user_id)
        
        if not updated:
            # Check if it exists but belongs to another user or doesn't exist
            notification = await self.repository.get(notification_id)
            if not notification:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Notification not found"
                )
            if notification.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this notification"
                )
                
        return True
    
    async def mark_all_as_read(self, user_id: UUID) -> int:
        """
        Mark all notifications as read for a user.
        
        Args:
            user_id: User UUID
            
        Returns:
            Number of notifications updated
        """
        return await self.repository.mark_all_as_read(user_id)
