
"""
Dataset service for dataset management and processing operations.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from backend.core.exceptions import NotFoundError, ValidationError, ExternalServiceError
from backend.schemas.dataset import (
    DatasetCreate, DatasetResponse, DatasetStats, DatasetUpdate, DatasetStatus
)
from backend.schemas.crawl_jobs import CrawlJobCreate, CrawlJobStatus
from backend.repositories import DatasetRepository, CrawlJobRepository
from .base import BaseService


class DatasetService(BaseService):
    """Service for handling dataset operations."""

    def __init__(
        self,
        dataset_repository: DatasetRepository,
        crawl_job_repository: CrawlJobRepository
    ) -> None:
        """
        Initialize dataset service with required repositories.

        Args:
            dataset_repository: Dataset repository instance
            crawl_job_repository: CrawlJob repository instance
        """
        super().__init__()
        self._dataset_repo = dataset_repository
        self._crawl_job_repo = crawl_job_repository
        
    @property
    def dataset_repo(self) -> DatasetRepository:
        """Get dataset repository."""
        return self._dataset_repo
        
    @property
    def crawl_job_repo(self) -> CrawlJobRepository:
        """Get crawl job repository."""
        return self._crawl_job_repo

    async def create_dataset(self, dataset_create: DatasetCreate, user_id: int) -> DatasetResponse:
        """
        Create a new dataset generation job.

        Args:
            dataset_create: Dataset creation data
            user_id: Owner user ID

        Returns:
            Created dataset information

        Raises:
            ValidationError: If dataset data is invalid
        """
        self.log_operation("create_dataset", name=dataset_create.name, user_id=user_id)

        # Create dataset record
        dataset_data = {
            "name": dataset_create.name,
            "description": dataset_create.description,
            "user_id": user_id,
            "status": DatasetStatus.PENDING,
            "keywords": dataset_create.keywords,
            "max_images": dataset_create.max_images,
            "search_engines": dataset_create.search_engines
        }
        
        # Create crawl job for the dataset
        # Note: CrawlJob model doesn't have sources field, only keywords
        # Search engines are stored in the Dataset model
        crawl_job_data = {
            "project_id": 1,  # TODO: Get from context or create project
            "name": f"{dataset_create.name} - Crawl Job",
            "keywords": {"keywords": dataset_create.keywords},  # CrawlJob expects JSONB format
            "max_images": dataset_create.max_images,
            "status": "pending",
        }
        crawl_job = await self.crawl_job_repo.create(crawl_job_data)
        
        dataset_data["crawl_job_id"] = crawl_job.id
        dataset = await self.dataset_repo.create(dataset_data)
        
        return DatasetResponse(
            id=dataset.id,
            user_id=user_id,
            name=dataset.name,
            status=dataset.status,
            images_collected=0,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at
        )

    async def get_dataset_by_id(self, dataset_id: int, user_id: Optional[int] = None) -> DatasetResponse:
        """
        Get dataset by ID.

        Args:
            dataset_id: Dataset ID
            user_id: Optional user ID for authorization

        Returns:
            Dataset information

        Raises:
            NotFoundError: If dataset not found
        """
        self.log_operation("get_dataset_by_id", dataset_id=dataset_id, user_id=user_id)
        
        dataset = await self.dataset_repo.get_by_id(dataset_id)
        if not dataset:
            raise NotFoundError(f"Dataset not found: {dataset_id}")
            
        if user_id and dataset.user_id != user_id:
            raise PermissionError("Not authorized to access this dataset")
            
        # Get crawl job progress if exists
        progress = 0.0
        images_collected = 0
        
        if dataset.crawl_job_id:
            crawl_job = await self.crawl_job_repo.get_by_id(dataset.crawl_job_id)
            if crawl_job:
                progress = (crawl_job.downloaded_images / dataset.max_images) * 100 if dataset.max_images > 0 else 0
                images_collected = crawl_job.valid_images
                
                # Update dataset status based on crawl job status
                if dataset.status != crawl_job.status and crawl_job.status in ["completed", "failed", "cancelled"]:
                    dataset = await self.dataset_repo.update(
                        dataset_id,
                        {"status": DatasetStatus(crawl_job.status.upper())}
                    )
        
        return DatasetResponse(
            id=dataset.id,
            user_id=dataset.user_id,
            name=dataset.name,
            description=dataset.description,
            status=dataset.status,
            progress=min(progress, 100.0),  # Cap at 100%
            images_collected=images_collected,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at
        )
        
    async def update_dataset(
        self,
        dataset_id: int,
        dataset_update: DatasetUpdate,
        user_id: int,
    ) -> DatasetResponse:
        """
        Update dataset information.

        Args:
            dataset_id: Dataset ID
            dataset_update: Dataset update data
            user_id: User ID for authorization

        Returns:
            Updated dataset information

        Raises:
            NotFoundError: If dataset not found
            ValidationError: If update data is invalid
        """
        self.log_operation("update_dataset", dataset_id=dataset_id, user_id=user_id)
        
        # Get existing dataset
        dataset = await self.dataset_repo.get_by_id(dataset_id)
        if not dataset:
            raise NotFoundError(f"Dataset not found: {dataset_id}")
            
        if dataset.user_id != user_id:
            raise PermissionError("Not authorized to update this dataset")
            
        # Only allow updates if not in processing state
        if dataset.status == DatasetStatus.PROCESSING:
            raise ValidationError("Cannot update dataset while it's being processed")
            
        # Prepare update data
        update_data = dataset_update.model_dump(exclude_unset=True)
        
        # Update dataset
        updated_dataset = await self.dataset_repo.update(dataset_id, update_data)
        
        return await self.get_dataset_by_id(updated_dataset.id, user_id)

    async def delete_dataset(self, dataset_id: int, user_id: int) -> None:
        """
        Delete dataset.

        Args:
            dataset_id: Dataset ID
            user_id: User ID for authorization

        Raises:
            NotFoundError: If dataset not found
            PermissionError: If user is not authorized
        """
        self.log_operation("delete_dataset", dataset_id=dataset_id, user_id=user_id)
        
        # Verify dataset exists and user has permission
        dataset = await self.dataset_repo.get_by_id(dataset_id)
        if not dataset:
            raise NotFoundError(f"Dataset not found: {dataset_id}")
            
        if dataset.user_id != user_id:
            raise PermissionError("Not authorized to delete this dataset")
            
        # Cancel any running crawl job
        if dataset.crawl_job_id:
            await self.crawl_job_repo.update(
                dataset.crawl_job_id,
                {"status": CrawlJobStatus.CANCELLED}
            )
            
        # Delete dataset (cascade will handle related data)
        await self.dataset_repo.delete(dataset_id)

    async def cancel_dataset(self, dataset_id: int, user_id: int) -> DatasetResponse:
        """
        Cancel dataset processing.

        Args:
            dataset_id: Dataset ID
            user_id: User ID for authorization

        Returns:
            Updated dataset information

        Raises:
            NotFoundError: If dataset not found
            ValidationError: If dataset is not in a cancellable state
        """
        self.log_operation("cancel_dataset", dataset_id=dataset_id, user_id=user_id)
        
        # Get dataset
        dataset = await self.dataset_repo.get_by_id(dataset_id)
        if not dataset:
            raise NotFoundError(f"Dataset not found: {dataset_id}")
            
        if dataset.user_id != user_id:
            raise PermissionError("Not authorized to cancel this dataset")
            
        # Check if dataset can be cancelled
        if dataset.status not in [DatasetStatus.PENDING, DatasetStatus.PROCESSING]:
            raise ValidationError(f"Cannot cancel dataset in {dataset.status} state")
            
        # Cancel associated crawl job if exists
        if dataset.crawl_job_id:
            await self.crawl_job_repo.update(
                dataset.crawl_job_id,
                {"status": CrawlJobStatus.CANCELLED}
            )
            
        # Update dataset status
        updated_dataset = await self.dataset_repo.update(
            dataset_id,
            {"status": DatasetStatus.CANCELLED}
        )
        
        return await self.get_dataset_by_id(updated_dataset.id, user_id)

    async def get_dataset_stats(self, user_id: Optional[int] = None) -> DatasetStats:
        """
        Get dataset statistics.

        Args:
            user_id: Optional user ID to filter stats

        Returns:
            Dataset statistics

        Raises:
            NotFoundError: If user not found
            ExternalServiceError: If there's an error fetching statistics
        """
        from backend.core.exceptions import NotFoundError, ExternalServiceError
        from sqlalchemy.exc import SQLAlchemyError

        self.log_operation("get_dataset_stats", user_id=user_id)
        
        try:
            # Get dataset statistics
            stats = await self.dataset_repo.get_stats(user_id)
            
            # Get dataset IDs for the user if user_id is provided
            dataset_ids = None
            if user_id:
                try:
                    datasets = await self.dataset_repo.list(user_id=user_id)
                    dataset_ids = [d.id for d in datasets]
                except Exception as e:
                    raise ExternalServiceError(
                        f"Failed to fetch datasets for user {user_id}: {str(e)}"
                    ) from e
            
            # Get image statistics from crawl jobs
            try:
                image_stats = await self.crawl_job_repo.get_image_stats(
                    user_id=user_id,
                    dataset_ids=dataset_ids
                )
            except Exception as e:
                raise ExternalServiceError(
                    f"Failed to fetch image statistics: {str(e)}"
                ) from e
            
            # Calculate average images per dataset
            avg_images = 0
            if stats["total"] > 0 and "total_images" in image_stats:
                avg_images = image_stats["total_images"] / stats["total"]
            # Take care of silent Zeros, this could lead to a bug where you wonder why it is zero
            return DatasetStats(
                total_datasets=stats.get("total", 0),
                processing_datasets=stats.get("active", 0),
                completed_datasets=stats.get("completed", 0),
                failed_datasets=stats.get("failed", 0),
                total_images=image_stats.get("total_images", 0)
            )
            
        except SQLAlchemyError as e:
            raise ExternalServiceError(
                f"Database error while fetching dataset stats: {str(e)}"
            ) from e
        except NotFoundError:
            raise
        except Exception as e:
            raise ExternalServiceError(
                f"Failed to get dataset statistics: {str(e)}"
            ) from e
