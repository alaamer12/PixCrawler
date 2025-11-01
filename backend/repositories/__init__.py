"""
Repository layer for data access operations.

This module provides the repository pattern implementation for all models,
ensuring clean separation between business logic and data access.

Exports:
    - BaseRepository: Abstract base repository
    - CrawlJobRepository: CrawlJob data access
    - ProjectRepository: Project data access
    - ImageRepository: Image data access
    - UserRepository: User/Profile data access
    - ActivityLogRepository: ActivityLog data access
"""

from .base import BaseRepository
from .crawl_job_repository import CrawlJobRepository
from .project_repository import ProjectRepository
from .image_repository import ImageRepository
from .user_repository import UserRepository
from .activity_log_repository import ActivityLogRepository

__all__ = [
    "BaseRepository",
    "CrawlJobRepository",
    "ProjectRepository",
    "ImageRepository",
    "UserRepository",
    "ActivityLogRepository",
]
