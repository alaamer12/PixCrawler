"""
Crawl job management endpoints.

This module provides API endpoints for managing image crawling jobs,
including creation, status monitoring, and execution control.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.base import PaginatedResponse, PaginationParams
from backend.database.connection import get_session
from backend.services.crawl_job import CrawlJobService, execute_crawl_job
from backend.api.dependencies import get_current_user
from pydantic import BaseModel, Field

__all__ = ['router']

router = APIRouter()


class CrawlJobCreate(BaseModel):
    """Schema for creating a new crawl job."""

    project_id: int = Field(..., description="Project ID")
    name: str = Field(..., min_length=1, max_length=100, description="Job name")
    keywords: List[str] = Field(..., min_items=1, description="Search keywords")
    max_images: int = Field(default=100, ge=1, le=10000, description="Maximum images")
    search_engine: str = Field(default="duckduckgo", description="Search engine")
    config: Dict[str, Any] = Field(default_factory=dict, description="Additional config")


class CrawlJobResponse(BaseModel):
    """Schema for crawl job response."""

    id: int
    project_id: int
    name: str
    keywords: List[str]
    max_images: int
    search_engine: str
    status: str
    progress: int
    total_images: int
    downloaded_images: int
    valid_images: int
    config: Dict[str, Any]
    created_at: str
    updated_at: str
    started_at: str | None = None
    completed_at: str | None = None


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
            search_engine=job.search_engine,
            status=job.status,
            progress=job.progress,
            total_images=job.total_images,
            downloaded_images=job.downloaded_images,
            valid_images=job.valid_images,
            config=job.config,
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
            search_engine=job.search_engine,
            status=job.status,
            progress=job.progress,
            total_images=job.total_images,
            downloaded_images=job.downloaded_images,
            valid_images=job.valid_images,
            config=job.config,
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
