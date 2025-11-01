"""
User (Profile) repository for data access operations.

This module provides the repository pattern implementation for Profile model,
handling all database queries and data access logic.

Classes:
    UserRepository: Repository for Profile CRUD and queries
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Profile
from .base import BaseRepository

__all__ = ['UserRepository']


class UserRepository(BaseRepository[Profile]):
    """
    Repository for User (Profile) data access.
    
    Provides database operations for user profiles.
    
    Attributes:
        session: Database session
        model: Profile model class
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize User repository.
        
        Args:
            session: Database session
        """
        super().__init__(session, Profile)
    
    async def get_by_uuid(self, user_id: UUID) -> Optional[Profile]:
        """
        Get user by UUID.
        
        Args:
            user_id: User UUID
        
        Returns:
            Profile or None
        """
        result = await self.session.execute(
            select(Profile).where(Profile.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[Profile]:
        """
        Get user by email.
        
        Args:
            email: User email
        
        Returns:
            Profile or None
        """
        result = await self.session.execute(
            select(Profile).where(Profile.email == email)
        )
        return result.scalar_one_or_none()
