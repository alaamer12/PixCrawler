"""
Dashboard service for aggregating statistics.

This module provides the DashboardService for aggregating statistics
from multiple tables to provide dashboard overview metrics.
"""

from typing import Dict, Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Project, CrawlJob, Image
from backend.repositories import (
    ProjectRepository,
    CrawlJobRepository,
    ImageRepository,
)

__all__ = ['DashboardService']


# noinspection PyTypeChecker
class DashboardService:
    """
    Service for dashboard statistics aggregation.

    Provides methods for aggregating data from multiple tables
    to generate dashboard overview metrics.
    """

    def __init__(
        self,
        project_repo: ProjectRepository,
        crawl_job_repo: CrawlJobRepository,
        image_repo: ImageRepository,
    ):
        """
        Initialize DashboardService with required repositories.

        Args:
            project_repo: Project repository instance
            crawl_job_repo: CrawlJob repository instance
            image_repo: Image repository instance
        """
        self.project_repo = project_repo
        self.crawl_job_repo = crawl_job_repo
        self.image_repo = image_repo

    async def get_dashboard_stats(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get dashboard statistics for a user.

        Aggregates data from multiple tables to provide overview metrics
        including project count, active jobs, total images, and storage usage.

        Args:
            user_id: User UUID to get statistics for

        Returns:
            Dictionary containing dashboard statistics
        """
        # Get session from repository
        session = self.project_repo.session

        # Count total projects
        total_projects_query = select(func.count(Project.id)).where(
            Project.user_id == user_id
        )
        total_projects = await session.scalar(total_projects_query) or 0

        # Count active jobs (pending or running)
        active_jobs_query = select(func.count(CrawlJob.id)).where(
            CrawlJob.project_id.in_(
                select(Project.id).where(Project.user_id == user_id)
            ),
            CrawlJob.status.in_(['pending', 'running'])
        )
        active_jobs = await session.scalar(active_jobs_query) or 0

        # Count total images
        total_images_query = select(func.count(Image.id)).where(
            Image.crawl_job_id.in_(
                select(CrawlJob.id).where(
                    CrawlJob.project_id.in_(
                        select(Project.id).where(Project.user_id == user_id)
                    )
                )
            )
        )
        total_images = await session.scalar(total_images_query) or 0

        # Calculate storage (sum of image file sizes)
        storage_query = select(func.sum(Image.file_size)).where(
            Image.crawl_job_id.in_(
                select(CrawlJob.id).where(
                    CrawlJob.project_id.in_(
                        select(Project.id).where(Project.user_id == user_id)
                    )
                )
            )
        )
        storage_bytes = await session.scalar(storage_query) or 0
        storage_gb = storage_bytes / (1024 ** 3)
        storage_used = f"{storage_gb:.2f} GB"

        # Calculate processing speed (simplified)
        # Note: Can be enhanced by calculating from recent job metrics
        processing_speed = "0/min"

        # Get credits remaining
        # Note: Requires credit_accounts table implementation
        credits_remaining = 0

        return {
            "total_projects": total_projects,
            "active_jobs": active_jobs,
            "total_datasets": 0,  # Note: Requires datasets table implementation
            "total_images": total_images,
            "storage_used": storage_used,
            "processing_speed": processing_speed,
            "credits_remaining": credits_remaining,
        }
