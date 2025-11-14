"""
Image repository for data access operations.

This module provides the repository pattern implementation for Image model,
handling all database queries and data access logic.

Classes:
    ImageRepository: Repository for Image CRUD and queries
"""

from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Image
from .base import BaseRepository

__all__ = ['ImageRepository']


class ImageRepository(BaseRepository[Image]):
    """
    Repository for Image data access.
    
    Provides database operations for images including CRUD
    and job-specific filtering.
    
    Attributes:
        session: Database session
        model: Image model class
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize Image repository.
        
        Args:
            session: Database session
        """
        super().__init__(session, Image)
    
    async def get_by_crawl_job(self, crawl_job_id: int) -> List[Image]:
        """
        Get all images for a specific crawl job.
        
        Args:
            crawl_job_id: Crawl job ID
        
        Returns:
            List of images
        """
        result = await self.session.execute(
            select(Image)
            .where(Image.crawl_job_id == crawl_job_id)
            .order_by(Image.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def count_by_job(self, crawl_job_id: int) -> int:
        """
        Count images for a specific job.
        
        Args:
            crawl_job_id: Crawl job ID
        
        Returns:
            Number of images
        """
        result = await self.session.execute(
            select(func.count(Image.id))
            .where(Image.crawl_job_id == crawl_job_id)
        )
        return result.scalar() or 0
    
    async def bulk_create(self, images_data: List[dict]) -> List[Image]:
        """
        Create multiple images in bulk.
        
        Args:
            images_data: List of image dictionaries
        
        Returns:
            List of created images
        """
        images = [Image(**data) for data in images_data]
        self.session.add_all(images)
        await self.session.commit()
        
        for image in images:
            await self.session.refresh(image)
        
        return images
