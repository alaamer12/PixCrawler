
"""
Dataset service for dataset management and processing operations.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from backend.core.exceptions import NotFoundError, ValidationError, ExternalServiceError
from backend.schemas.dataset import (
    DatasetCreate, DatasetResponse, DatasetStats, DatasetUpdate, DatasetStatus,
    DatasetVersionResponse
)
from backend.schemas.crawl_jobs import CrawlJobCreate, CrawlJobStatus
from backend.repositories import DatasetRepository, CrawlJobRepository
from backend.models import DatasetVersion
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
        
        # Create initial dataset version (v1)
        version_data = {
            "dataset_id": dataset.id,
            "version_number": 1,
            "keywords": dataset_create.keywords,
            "search_engines": dataset_create.search_engines,
            "max_images": dataset_create.max_images,
            "crawl_job_id": crawl_job.id,
            "change_summary": "Initial dataset creation",
            "created_by": user_id
        }
        
        # We need a repository or direct session access for DatasetVersion
        # For now, assuming dataset_repo has a method or we add a version repo.
        # Ideally, we should inject DatasetVersionRepository. 
        # But to keep it simple and given restrictions, I'll add a helper in DatasetRepository or just use the session if available.
        # Let's assume we can add `create_version` to DatasetRepository.
        await self.dataset_repo.create_version(version_data)
        
        return DatasetResponse(
            id=dataset.id,
            user_id=user_id,
            name=dataset.name,
            status=dataset.status,
            images_collected=0,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at,
            keywords=dataset_create.keywords,
            max_images=dataset_create.max_images,
            search_engines=dataset_create.search_engines
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
        
        # Update last_accessed_at
        await self.dataset_repo.update(
            dataset_id,
            {"last_accessed_at": datetime.now()}
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
            updated_at=dataset.updated_at,
            keywords=dataset.keywords,
            max_images=dataset.max_images,
            search_engines=dataset.search_engines
        )
        
    async def update_dataset(
        self,
        dataset_id: int,
        dataset_update: DatasetUpdate,
        user_id: int,
    ) -> DatasetResponse:
        """
        Update dataset information.
        
        If configuration (keywords, search engines, max images) changes,
        creates a new version and potentially a new crawl job.
        """
        self.log_operation("update_dataset", dataset_id=dataset_id, user_id=user_id)
        
        # Get existing dataset
        dataset = await self.dataset_repo.get_by_id(dataset_id)
        if not dataset:
            raise NotFoundError(f"Dataset not found: {dataset_id}")
            
        if dataset.user_id != user_id:
            raise PermissionError("Not authorized to update this dataset")
            
        # Prepare update data
        update_data = dataset_update.model_dump(exclude_unset=True)
        
        # Check for config changes
        is_config_changed = self._is_config_change(dataset, update_data)
        
        # Only allow updates if not in processing state (unless we are creating a new version)
        if dataset.status == DatasetStatus.PROCESSING and not is_config_changed:
            raise ValidationError("Cannot update dataset metadata while it's being processed")
            
        # If config changed, handle versioning
        if is_config_changed:
            # 1. Get current max version number
            versions = await self.dataset_repo.get_versions(dataset_id)
            current_version = versions[0].version_number if versions else 0
            new_version_enum = current_version + 1
            
            # 2. Create new CrawlJob
            # We need to construct the crawl job data from the NEW config (merged)
            merged_config = {
                "keywords": update_data.get("keywords", dataset.keywords),
                "max_images": update_data.get("max_images", dataset.max_images),
                # Search engines are not part of CrawlJob model directly (only keywords JSONB) but we store them in Dataset
            }
            
            crawl_job_data = {
                "project_id": 1, # TODO: Fix project ID resolution
                "name": f"{update_data.get('name', dataset.name)} - v{new_version_enum}",
                "keywords": {"keywords": merged_config["keywords"]},
                "max_images": merged_config["max_images"],
                "status": "pending",
            }
            new_crawl_job = await self.crawl_job_repo.create(crawl_job_data)
            
            # 3. Create DatasetVersion
            # Store the config that THIS version is using (the new config)
            version_data = {
                "dataset_id": dataset.id,
                "version_number": new_version_enum,
                "keywords": merged_config["keywords"],
                "search_engines": update_data.get("search_engines", dataset.search_engines),
                "max_images": merged_config["max_images"],
                "crawl_job_id": new_crawl_job.id,
                "change_summary": "Configuration update",
                "created_by": user_id
            }
            await self.dataset_repo.create_version(version_data)
            
            # 4. Update Dataset pointer to new crawl job and update fields
            update_data["crawl_job_id"] = new_crawl_job.id
            update_data["status"] = DatasetStatus.PENDING # Reset status for new run
            update_data["progress"] = 0
            update_data["images_collected"] = 0
            
            # If there was an old running job, should we cancel it?
            # Requirement says "Track all dataset changes".
            # If I update config, I am effectively restarting the process with new params.
            # So yes, cancel old job if running.
            if dataset.crawl_job_id and dataset.status == DatasetStatus.PROCESSING:
                await self.crawl_job_repo.update(
                    dataset.crawl_job_id,
                    {"status": CrawlJobStatus.CANCELLED}
                )

        updated_dataset = await self.dataset_repo.update(dataset_id, update_data)
        return await self.get_dataset_by_id(updated_dataset.id, user_id)

    def _is_config_change(self, dataset: Dataset, update_data: dict) -> bool:
        """Check if update contains configuration changes."""
        config_fields = ["keywords", "search_engines", "max_images"]
        for field in config_fields:
            if field in update_data and update_data[field] != getattr(dataset, field):
                return True
        return False

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

    async def get_dataset_versions(self, dataset_id: int, user_id: int) -> List[DatasetVersionResponse]:
        """
        Get all versions of a dataset.
        
        Args:
            dataset_id: Dataset ID
            user_id: User ID for authorization
            
        Returns:
            List of dataset versions
        """
        self.log_operation("get_dataset_versions", dataset_id=dataset_id, user_id=user_id)
        
        # Verify dataset access
        await self.get_dataset_by_id(dataset_id, user_id)
        
        versions = await self.dataset_repo.get_versions(dataset_id)
        return versions # Pydantic config will handle ORM to dictionary conversion if needed, or we explicitly map

    async def get_dataset_version(self, dataset_id: int, version_number: int, user_id: int) -> DatasetVersionResponse:
        """
        Get specific version of a dataset.
        
        Args:
            dataset_id: Dataset ID
            version_number: Version number
            user_id: User ID for authorization
            
        Returns:
            Dataset version details
        """
        self.log_operation("get_dataset_version", dataset_id=dataset_id, version_number=version_number, user_id=user_id)
        
        # Verify dataset access
        await self.get_dataset_by_id(dataset_id, user_id)
        
        version = await self.dataset_repo.get_version_by_number(dataset_id, version_number)
        if not version:
            raise NotFoundError(f"Version {version_number} not found for dataset {dataset_id}")
            
        return version

    async def rollback_dataset(self, dataset_id: int, version_number: int, user_id: int) -> DatasetResponse:
        """
        Rollback dataset to a specific version.
        
        This creates a NEW version with the configuration from the target version.
        
        Args:
            dataset_id: Dataset ID
            version_number: Target version number
            user_id: User ID for authorization
            
        Returns:
            Updated dataset information
        """
        self.log_operation("rollback_dataset", dataset_id=dataset_id, version_number=version_number, user_id=user_id)
        
        # Get target version
        target_version = await self.get_dataset_version(dataset_id, version_number, user_id)
        
        # Create update object with config from target version
        dataset_update = DatasetUpdate(
            name=f"Rollback to v{version_number}", # Optional naming
            keywords=target_version.keywords,
            search_engines=target_version.search_engines,
            max_images=target_version.max_images
        )
        
        # Update dataset (this will trigger new version creation)
        return await self.update_dataset(dataset_id, dataset_update, user_id)
