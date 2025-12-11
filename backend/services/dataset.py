
"""
Dataset service for dataset management and processing operations.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

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

    async def create_dataset(
        self, 
        dataset_create: DatasetCreate, 
        user_id: UUID | str,
        project_id: Optional[int] = None
    ) -> DatasetResponse:
        """
        Create a new dataset generation job.

        Args:
            dataset_create: Dataset creation data
            user_id: Owner user ID
            project_id: Optional project ID. If not provided, uses user's default project.

        Returns:
            Created dataset information

        Raises:
            ValidationError: If dataset data is invalid
            NotFoundError: If specified project not found
        """
        self.log_operation("create_dataset", name=dataset_create.name, user_id=user_id)
        
        # Get or create default project if project_id not provided
        if project_id is None:
            # Get user's default project or create one
            from backend.repositories import ProjectRepository
            project_repo = ProjectRepository(self.dataset_repo.session)
            
            # Try to get user's first project
            from sqlalchemy import select
            from backend.database.models import Project
            result = await self.dataset_repo.session.execute(
                select(Project)
                .where(Project.user_id == user_id)
                .order_by(Project.created_at.asc())
                .limit(1)
            )
            default_project = result.scalar_one_or_none()
            
            if not default_project:
                # Create a default project for the user
                default_project = await project_repo.create(
                    name="Default Project",
                    description="Auto-created default project",
                    user_id=user_id,
                    status="active"
                )
                self.logger.info(f"Created default project {default_project.id} for user {user_id}")
            
            project_id = default_project.id
        else:
            # Verify project exists and belongs to user
            from backend.repositories import ProjectRepository
            project_repo = ProjectRepository(self.dataset_repo.session)
            project = await project_repo.get_by_id(project_id)
            
            if not project:
                raise NotFoundError(f"Project {project_id} not found")
            
            # Convert user_id to UUID for comparison if it's a string
            user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
            if project.user_id != user_uuid:
                raise PermissionError(f"Project {project_id} does not belong to user {user_id}")

        # Create dataset record
        dataset_data = {
            "name": dataset_create.name,
            "description": dataset_create.description,
            "user_id": user_id,
            "project_id": project_id,
            "status": DatasetStatus.PENDING,
            "keywords": dataset_create.keywords,
            "max_images": dataset_create.max_images,
            "search_engines": dataset_create.search_engines
        }
        
        # Create crawl job for the dataset
        # Note: CrawlJob model doesn't have sources field, only keywords
        # Search engines are stored in the Dataset model
        crawl_job_data = {
            "project_id": project_id,  # Use resolved project_id
            "name": f"{dataset_create.name} - Crawl Job",
            "keywords": {"keywords": dataset_create.keywords},  # CrawlJob expects JSONB format
            "max_images": dataset_create.max_images,
            "status": "pending",
        }
        crawl_job = await self.crawl_job_repo.create(**crawl_job_data)
        
        dataset_data["crawl_job_id"] = crawl_job.id
        dataset = await self.dataset_repo.create(**dataset_data)
        
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
            search_engines=dataset_create.search_engines,
            project_id=project_id
        )

    async def list_datasets(
        self,
        user_id: UUID | str,
        project_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 20,
        status: Optional[DatasetStatus] = None
    ) -> List[DatasetResponse]:
        """
        List datasets for a user with pagination.

        Args:
            user_id: User ID to filter datasets
            project_id: Optional project ID to filter by project
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            status: Optional status filter

        Returns:
            List of dataset responses

        Raises:
            ValidationError: If pagination parameters are invalid
        """
        self.log_operation("list_datasets", user_id=user_id, project_id=project_id, skip=skip, limit=limit, status=status)
        
        # Validate pagination parameters
        if skip < 0:
            raise ValidationError("Skip parameter must be non-negative")
        if limit < 1 or limit > 100:
            raise ValidationError("Limit must be between 1 and 100")
        
        user_uuid = UUID(str(user_id)) if isinstance(user_id, (str, int)) else user_id
        
        # Get datasets from repository
        datasets = await self.dataset_repo.list(
            user_id=user_uuid,
            project_id=project_id,
            skip=skip,
            limit=limit
        )
        
        # Convert to response models
        responses = []
        for dataset in datasets:
            # Filter by status if requested (since repo doesn't support it in list method yet)
            if status and dataset.status != status:
                continue
                
            # Get crawl job progress if exists
            progress = 0.0
            images_collected = 0
            
            if dataset.crawl_job_id:
                crawl_job = await self.crawl_job_repo.get_by_id(dataset.crawl_job_id)
                if crawl_job:
                    progress = (crawl_job.downloaded_images / dataset.max_images) * 100 if dataset.max_images > 0 else 0
                    images_collected = crawl_job.valid_images
            
            responses.append(DatasetResponse(
                id=dataset.id,
                user_id=dataset.user_id,
                name=dataset.name,
                description=dataset.description,
                status=dataset.status,
                progress=min(progress, 100.0),
                images_collected=images_collected,
                created_at=dataset.created_at,
                updated_at=dataset.updated_at,
                keywords=dataset.keywords,
                max_images=dataset.max_images,
                search_engines=dataset.search_engines,
                project_id=dataset.project_id
            ))
        
        return responses

    async def get_dataset_by_id(self, dataset_id: int, user_id: Optional[UUID | str] = None) -> DatasetResponse:
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
            
        if user_id:
            user_uuid = UUID(str(user_id)) if isinstance(user_id, (str, int)) else user_id
            if dataset.user_id != user_uuid:
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
                        dataset,
                        status=DatasetStatus(crawl_job.status.upper())
                    )
        
        # Update last_accessed_at
        await self.dataset_repo.update(
            dataset,
            last_accessed_at=datetime.now()
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
            search_engines=dataset.search_engines,
            project_id=dataset.project_id
        )
        
    async def update_dataset(
        self,
        dataset_id: int,
        dataset_update: DatasetUpdate,
        user_id: UUID | str,
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
            
        user_uuid = UUID(str(user_id)) if isinstance(user_id, (str, int)) else user_id
        if dataset.user_id != user_uuid:
            raise PermissionError("Not authorized to update this dataset")
            
        # Only allow updates if not in processing state
        if dataset.status == DatasetStatus.PROCESSING:
            raise ValidationError("Cannot update dataset while it's being processed")
            
        # Prepare update data
        update_data = dataset_update.model_dump(exclude_unset=True)
        
        # Update dataset
        updated_dataset = await self.dataset_repo.update(dataset, **update_data)
        
        return await self.get_dataset_by_id(updated_dataset.id, user_id)

    async def delete_dataset(self, dataset_id: int, user_id: UUID | str) -> None:
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
            
        user_uuid = UUID(str(user_id)) if isinstance(user_id, (str, int)) else user_id
        if dataset.user_id != user_uuid:
            raise PermissionError("Not authorized to delete this dataset")
            
        # Cancel any running crawl job
        if dataset.crawl_job_id:
            crawl_job = await self.crawl_job_repo.get_by_id(dataset.crawl_job_id)
            if crawl_job:
                await self.crawl_job_repo.update(
                    crawl_job,
                    status=CrawlJobStatus.CANCELLED
                )
            
        # Delete dataset (cascade will handle related data)
        await self.dataset_repo.delete(dataset_id)

    async def cancel_dataset(self, dataset_id: int, user_id: UUID | str) -> DatasetResponse:
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
            
        user_uuid = UUID(str(user_id)) if isinstance(user_id, (str, int)) else user_id
        if dataset.user_id != user_uuid:
            raise PermissionError("Not authorized to cancel this dataset")
            
        # Check if dataset can be cancelled
        if dataset.status not in [DatasetStatus.PENDING, DatasetStatus.PROCESSING]:
            raise ValidationError(f"Cannot cancel dataset in {dataset.status} state")
            
        # Cancel associated crawl job if exists
        if dataset.crawl_job_id:
            crawl_job = await self.crawl_job_repo.get_by_id(dataset.crawl_job_id)
            if crawl_job:
                await self.crawl_job_repo.update(
                    crawl_job,
                    status=CrawlJobStatus.CANCELLED
                )
            
        # Update dataset status
        updated_dataset = await self.dataset_repo.update(
            dataset,
            status=DatasetStatus.CANCELLED
        )
        
        return await self.get_dataset_by_id(updated_dataset.id, user_id)

    async def get_dataset_stats(self, user_id: Optional[UUID | str] = None) -> DatasetStats:
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

    async def start_build_job(self, dataset_id: int, user_id: UUID | str) -> DatasetResponse:
        """
        Start building a dataset (trigger Celery task for processing).

        Args:
            dataset_id: Dataset ID
            user_id: User ID for authorization

        Returns:
            Updated dataset information with task ID

        Raises:
            NotFoundError: If dataset not found
            ValidationError: If dataset is not in a startable state
        """
        self.log_operation("start_build_job", dataset_id=dataset_id, user_id=user_id)
        
        # Get dataset
        dataset = await self.dataset_repo.get_by_id(dataset_id)
        if not dataset:
            raise NotFoundError(f"Dataset not found: {dataset_id}")
            
        user_uuid = UUID(str(user_id)) if isinstance(user_id, (str, int)) else user_id
        if dataset.user_id != user_uuid:
            raise PermissionError("Not authorized to start this dataset")
            
        # Check if dataset can be started
        if dataset.status not in [DatasetStatus.PENDING, DatasetStatus.FAILED]:
            raise ValidationError(f"Cannot start dataset in {dataset.status} state")
            
        # Update dataset status to processing
        await self.dataset_repo.update(
            dataset,
            status=DatasetStatus.PROCESSING
        )
        
        # Start associated crawl job if exists
        if dataset.crawl_job_id:
            crawl_job = await self.crawl_job_repo.get_by_id(dataset.crawl_job_id)
            if crawl_job:
                await self.crawl_job_repo.update(
                    crawl_job,
                    status=CrawlJobStatus.RUNNING
                )
            
            # TODO: Dispatch Celery task here
            # from builder.tasks import process_crawl_job_task
            # task = process_crawl_job_task.delay(dataset.crawl_job_id)
            # Store task.id in crawl_job.task_ids
        
        return await self.get_dataset_by_id(dataset_id, user_id)

    async def get_build_status(self, dataset_id: int, user_id: UUID | str) -> Dict[str, Any]:
        """
        Get build status for a dataset.

        Args:
            dataset_id: Dataset ID
            user_id: User ID for authorization

        Returns:
            Build status information including progress and task details

        Raises:
            NotFoundError: If dataset not found
        """
        self.log_operation("get_build_status", dataset_id=dataset_id, user_id=user_id)
        
        # Get dataset
        dataset = await self.dataset_repo.get_by_id(dataset_id)
        if not dataset:
            raise NotFoundError(f"Dataset not found: {dataset_id}")
            
        user_uuid = UUID(str(user_id)) if isinstance(user_id, (str, int)) else user_id
        if dataset.user_id != user_uuid:
            raise PermissionError("Not authorized to access this dataset")
        
        # Get crawl job details
        crawl_job = None
        if dataset.crawl_job_id:
            crawl_job = await self.crawl_job_repo.get_by_id(dataset.crawl_job_id)
        
        # Calculate progress
        progress = 0.0
        images_collected = 0
        estimated_completion = None
        
        if crawl_job:
            if dataset.max_images > 0:
                progress = (crawl_job.downloaded_images / dataset.max_images) * 100
            images_collected = crawl_job.valid_images
            
            # Calculate estimated completion based on progress rate
            if crawl_job.started_at and progress > 0:
                elapsed = (datetime.now() - crawl_job.started_at).total_seconds()
                if elapsed > 0:
                    rate = progress / elapsed  # progress per second
                    if rate > 0:
                        remaining_progress = 100 - progress
                        remaining_seconds = remaining_progress / rate
                        estimated_completion = datetime.now() + timedelta(seconds=remaining_seconds)
        
        return {
            "dataset_id": dataset_id,
            "status": dataset.status,
            "progress": min(progress, 100.0),
            "images_collected": images_collected,
            "max_images": dataset.max_images,
            "estimated_completion": estimated_completion.isoformat() if estimated_completion else None,
            "crawl_job_id": dataset.crawl_job_id,
            "task_ids": crawl_job.task_ids if crawl_job else [],
            "started_at": crawl_job.started_at.isoformat() if crawl_job and crawl_job.started_at else None,
            "updated_at": dataset.updated_at.isoformat()
        }

    async def generate_download_link(self, dataset_id: int, user_id: UUID | str) -> Dict[str, str]:
        """
        Generate a secure download link for a completed dataset.

        Args:
            dataset_id: Dataset ID
            user_id: User ID for authorization

        Returns:
            Dictionary with download_url and expiration time

        Raises:
            NotFoundError: If dataset not found
            ValidationError: If dataset is not completed
        """
        self.log_operation("generate_download_link", dataset_id=dataset_id, user_id=user_id)
        
        # Get dataset
        dataset = await self.dataset_repo.get_by_id(dataset_id)
        if not dataset:
            raise NotFoundError(f"Dataset not found: {dataset_id}")
            
        user_uuid = UUID(str(user_id)) if isinstance(user_id, (str, int)) else user_id
        if dataset.user_id != user_uuid:
            raise PermissionError("Not authorized to download this dataset")
            
        # Check if dataset is completed
        if dataset.status != DatasetStatus.COMPLETED:
            raise ValidationError(f"Dataset is not completed (status: {dataset.status})")
        
        # Generate secure download link (valid for 1 hour)
        # TODO: Integrate with storage service to generate actual signed URL
        # For now, return a placeholder
        from datetime import timedelta
        import secrets
        
        token = secrets.token_urlsafe(32)
        expiration = datetime.now() + timedelta(hours=1)
        
        # Store token in database for validation
        # TODO: Create DownloadToken model and repository
        
        download_url = f"/api/v1/datasets/{dataset_id}/download?token={token}"
        
        return {
            "download_url": download_url,
            "expires_at": expiration.isoformat(),
            "dataset_id": str(dataset_id),
            "file_size_bytes": 0  # TODO: Get actual file size from storage
        }
