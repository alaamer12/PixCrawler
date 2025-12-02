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
    
    async def mark_validated(
        self,
        image_id: int,
        validation_result: dict
    ) -> Optional[Image]:
        """
        Update image with validation results.
        
        This method persists validation results including validity status,
        duplicate detection, and validation metadata. The service layer is
        responsible for determining the validation results.
        
        Args:
            image_id: Image ID
            validation_result: Dictionary with validation data containing:
                - is_valid: Boolean validation status
                - is_duplicate: Boolean duplicate status
                - metadata: Additional validation metadata (optional)
        
        Returns:
            Updated image or None if not found
        """
        image = await self.get_by_id(image_id)
        if not image:
            return None
        
        # Extract validation fields
        update_data = {
            'is_valid': validation_result.get('is_valid', False),
            'is_duplicate': validation_result.get('is_duplicate', False)
        }
        
        # Merge validation metadata if provided
        if 'metadata' in validation_result:
            # Get existing metadata or initialize empty dict
            existing_metadata = image.metadata_ if image.metadata_ else {}
            # Merge with new validation metadata
            existing_metadata.update(validation_result['metadata'])
            update_data['metadata_'] = existing_metadata
        
        return await self.update(image, **update_data)
