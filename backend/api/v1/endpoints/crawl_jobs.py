"""
Crawl job management endpoints.

This module provides API endpoints for managing image crawling jobs,
including creation, status monitoring, and execution control.
"""

from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user
from backend.database.connection import get_session
from backend.services.crawl_job import CrawlJobService, execute_crawl_job

__all__ = ['router']

router = APIRouter()


class CrawlJobCreate(BaseModel):
    """Schema for creating a new crawl job."""

    model_config = {
        'str_strip_whitespace': True,
        'validate_assignment': True,
        'extra': 'forbid'
    }

    project_id: int = Field(
        ...,
        gt=0,
        description="Project ID",
        examples=[1, 42, 123]
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r'^[a-zA-Z0-9_\-\s]+$',
        description="Job name (alphanumeric, spaces, hyphens, underscores only)",
        examples=["Animal Photos Job", "car_images_crawl", "dataset-2024"]
    )
    keywords: List[str] = Field(
        ...,
        min_items=1,
        max_items=20,
        description="Search keywords",
        examples=[["cats", "dogs"], ["red car", "blue car"]]
    )
    max_images: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Maximum images to collect",
        examples=[100, 500, 1000]
    )
    search_engine: str = Field(
        default="duckduckgo",
        pattern=r'^(google|bing|baidu|duckduckgo)$',
        description="Search engine to use",
        examples=["google", "bing", "duckduckgo", "baidu"]
    )
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional configuration options",
        examples=[{}, {"quality": "high", "format": "jpg"}]
    )

    @field_validator('keywords')
    @classmethod
    def validate_keywords(cls, v: List[str]) -> List[str]:
        """Validate and clean keywords."""
        cleaned = []
        for keyword in v:
            cleaned_keyword = keyword.strip()
            if not cleaned_keyword:
                continue
            if len(cleaned_keyword) < 2:
                raise ValueError(f"Keyword '{cleaned_keyword}' is too short (minimum 2 characters)")
            if len(cleaned_keyword) > 100:
                raise ValueError(f"Keyword '{cleaned_keyword}' is too long (maximum 100 characters)")
            cleaned.append(cleaned_keyword)

        if not cleaned:
            raise ValueError("At least one valid keyword is required")

        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in cleaned:
            if keyword.lower() not in seen:
                seen.add(keyword.lower())
                unique_keywords.append(keyword)

        return unique_keywords


class CrawlJobResponse(BaseModel):
    """Schema for crawl job response."""

    model_config = {
        'str_strip_whitespace': True,
        'validate_assignment': True,
        'extra': 'forbid',
        'use_enum_values': True
    }

    id: int = Field(
        ...,
        gt=0,
        description="Job ID",
        examples=[1, 42, 123]
    )
    project_id: int = Field(
        ...,
        gt=0,
        description="Project ID",
        examples=[1, 42, 123]
    )
    name: str = Field(
        ...,
        min_length=1,
        description="Job name",
        examples=["Animal Photos Job"]
    )
    keywords: List[str] = Field(
        ...,
        min_items=1,
        description="Search keywords",
        examples=[["cats", "dogs"]]
    )
    max_images: int = Field(
        ...,
        ge=1,
        description="Maximum images to collect",
        examples=[100, 500]
    )
    search_engine: str = Field(
        ...,
        description="Search engine used",
        examples=["google", "duckduckgo"]
    )
    status: str = Field(
        ...,
        pattern=r'^(pending|running|completed|failed|cancelled)$',
        description="Job status",
        examples=["pending", "running", "completed", "failed", "cancelled"]
    )
    progress: int = Field(
        ...,
        ge=0,
        le=100,
        description="Progress percentage",
        examples=[0, 45, 100]
    )
    total_images: int = Field(
        ...,
        ge=0,
        description="Total images found",
        examples=[0, 150, 1000]
    )
    downloaded_images: int = Field(
        ...,
        ge=0,
        description="Images successfully downloaded",
        examples=[0, 120, 950]
    )
    valid_images: int = Field(
        ...,
        ge=0,
        description="Valid images after processing",
        examples=[0, 100, 900]
    )
    config: Dict[str, Any] = Field(
        ...,
        description="Job configuration",
        examples=[{}]
    )
    created_at: str = Field(
        ...,
        description="Creation timestamp",
        examples=["2024-01-15T10:30:00Z"]
    )
    updated_at: str = Field(
        ...,
        description="Last update timestamp",
        examples=["2024-01-15T14:45:30Z"]
    )
    started_at: Optional[str] = Field(
        None,
        description="Job start timestamp",
        examples=["2024-01-15T10:35:00Z", None]
    )
    completed_at: Optional[str] = Field(
        None,
        description="Job completion timestamp",
        examples=["2024-01-15T15:00:00Z", None]
    )

    @model_validator(mode='after')
    def validate_job_consistency(self) -> 'CrawlJobResponse':
        """Ensure job data is consistent."""
        if self.downloaded_images > self.total_images:
            raise ValueError("Downloaded images cannot exceed total images")

        if self.valid_images > self.downloaded_images:
            raise ValueError("Valid images cannot exceed downloaded images")

        if self.status == "completed" and self.progress != 100:
            raise ValueError("Completed jobs must have 100% progress")

        if self.status == "pending" and self.progress > 0:
            raise ValueError("Pending jobs should have 0% progress")

        return self


@router.post("/", response_model=CrawlJobResponse, status_code=status.HTTP_201_CREATED)
async def create_crawl_job(
    job_create: CrawlJobCreate,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CrawlJobResponse:
    """
    Create a new crawl job.

    Creates a new image crawling job and optionally starts it immediately.
    The job will be executed in the background using the PixCrawler builder.

    Args:
        job_create: Crawl job creation data
        background_tasks: FastAPI background tasks
        current_user: Current authenticated user
        session: Database session

    Returns:
        Created crawl job information

    Raises:
        HTTPException: If job creation fails
    """
    try:
        service = CrawlJobService(session)

        job = await service.create_job(
            project_id=job_create.project_id,
            name=job_create.name,
            keywords=job_create.keywords,
            max_images=job_create.max_images,
            search_engine=job_create.search_engine,
            config=job_create.config,
            user_id=current_user["user_id"]
        )

        # Start job execution in background
        background_tasks.add_task(execute_crawl_job, job.id)

        return CrawlJobResponse(
            id=job.id,
            project_id=job.project_id,
            name=job.name,
            keywords=job.keywords,
            max_images=job.max_images,
            status=job.status,
            progress=job.progress,
            total_images=job.total_images,
            downloaded_images=job.downloaded_images,
            valid_images=job.valid_images,
            created_at=job.created_at.isoformat(),
            updated_at=job.updated_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create crawl job: {str(e)}"
        )


@router.get("/{job_id}", response_model=CrawlJobResponse)
async def get_crawl_job(
    job_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CrawlJobResponse:
    """
    Get crawl job by ID.

    Retrieves detailed information about a specific crawl job,
    including current status and progress.

    Args:
        job_id: Crawl job ID
        current_user: Current authenticated user
        session: Database session

    Returns:
        Crawl job information

    Raises:
        HTTPException: If job not found
    """
    try:
        service = CrawlJobService(session)
        job = await service.get_job(job_id)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crawl job not found"
            )

        return CrawlJobResponse(
            id=job.id,
            project_id=job.project_id,
            name=job.name,
            keywords=job.keywords,
            max_images=job.max_images,
            status=job.status,
            progress=job.progress,
            total_images=job.total_images,
            downloaded_images=job.downloaded_images,
            valid_images=job.valid_images,
            created_at=job.created_at.isoformat(),
            updated_at=job.updated_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve crawl job: {str(e)}"
        )


@router.post("/{job_id}/cancel")
async def cancel_crawl_job(
    job_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Dict[str, str]:
    """
    Cancel a running crawl job.

    Attempts to cancel a crawl job that is currently running or pending.

    Args:
        job_id: Crawl job ID
        current_user: Current authenticated user
        session: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If job not found or cannot be cancelled
    """
    try:
        service = CrawlJobService(session)
        job = await service.get_job(job_id)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crawl job not found"
            )

        if job.status not in ["pending", "running"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel job with status: {job.status}"
            )

        await service.update_job(job_id, "cancelled")

        return {"message": "Crawl job cancelled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel crawl job: {str(e)}"
        )
