"""
Dataset repository for data access operations.

This module provides the repository pattern implementation for Dataset model,
handling all database queries and data access logic.

Classes:
    DatasetRepository: Repository for Dataset CRUD and queries

Features:
    - CRUD operations via BaseRepository
    - User-specific dataset queries
    - Status-based filtering
    - Statistics aggregation
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Dataset
from .base import BaseRepository

__all__ = ['DatasetRepository']


class DatasetRepository(BaseRepository[Dataset]):
    """
    Repository for Dataset data access.
    
    Provides database operations for datasets including CRUD,
    filtering by user and status, and statistics queries.
    
    Attributes:
        session: Database session
        model: Dataset model class
    
    Example:
        >>> repo = DatasetRepository(session)
        >>> dataset = await repo.create(user_id=user_uuid, name="My Dataset")
        >>> datasets = await repo.get_by_user(user_id=user_uuid)
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize Dataset repository.
        
        Args:
            session: Database session
        """
        super().__init__(session, Dataset)
    
    async def get_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dataset]:
        """
        Get all datasets for a specific user.
        
        Args:
            user_id: User UUID
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
        
        Returns:
            List of datasets
        """
        result = await self.session.execute(
            select(Dataset)
            .where(Dataset.user_id == user_id)
            .order_by(Dataset.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_status(
        self,
        status: str,
        user_id: Optional[UUID] = None
    ) -> List[Dataset]:
        """
        Get all datasets with specific status.
        
        Args:
            status: Dataset status (pending, processing, completed, failed, cancelled)
            user_id: Optional user UUID to filter by user
        
        Returns:
            List of datasets
        """
        query = select(Dataset).where(Dataset.status == status)
        
        if user_id:
            query = query.where(Dataset.user_id == user_id)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count_by_user(self, user_id: UUID) -> int:
        """
        Count total datasets for a user.
        
        Args:
            user_id: User UUID
        
        Returns:
            Total number of datasets
        """
        result = await self.session.execute(
            select(func.count(Dataset.id))
            .where(Dataset.user_id == user_id)
        )
        return result.scalar() or 0
    
    async def get_stats(self, user_id: Optional[UUID] = None) -> dict:
        """
        Get dataset statistics.
        
        Returns aggregate statistics about datasets, optionally
        filtered by user.
        
        Args:
            user_id: Optional user UUID to filter statistics
        
        Returns:
            Dictionary with statistics:
                - total: Total number of datasets
                - active: Number of processing datasets
                - completed: Number of completed datasets
                - failed: Number of failed datasets
                - pending: Number of pending datasets
                - cancelled: Number of cancelled datasets
        """
        # Base query
        base_query = select(Dataset)
        if user_id:
            base_query = base_query.where(Dataset.user_id == user_id)
        
        # Count total
        total_result = await self.session.execute(
            select(func.count(Dataset.id))
            .select_from(base_query.subquery())
        )
        total = total_result.scalar() or 0
        
        # Count by status
        stats = {
            "total": total,
            "active": 0,
            "completed": 0,
            "failed": 0,
            "pending": 0,
            "cancelled": 0,
        }
        
        # Get counts for each status
        for status in ["processing", "completed", "failed", "pending", "cancelled"]:
            query = select(func.count(Dataset.id)).where(Dataset.status == status)
            if user_id:
                query = query.where(Dataset.user_id == user_id)
            
            result = await self.session.execute(query)
            count = result.scalar() or 0
            
            # Map 'processing' to 'active' for consistency
            key = "active" if status == "processing" else status
            stats[key] = count
        
        return stats
    
    async def list(
        self,
        user_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dataset]:
        """
        List datasets with optional user filter.
        
        Args:
            user_id: Optional user UUID to filter by user
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
        
        Returns:
            List of datasets
        """
        query = select(Dataset).order_by(Dataset.created_at.desc())
        
        if user_id:
            query = query.where(Dataset.user_id == user_id)
        
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
