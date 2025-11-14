"""
Project schemas for PixCrawler.

This module defines Pydantic schemas for project management,
including creation, updates, and responses with relationships.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

if TYPE_CHECKING:
    from .crawl_jobs import CrawlJobResponse

__all__ = [
    'ProjectStatus',
    'ProjectBase',
    'ProjectCreate',
    'ProjectUpdate',
    'ProjectResponse',
    'ProjectDetailResponse',
]


class ProjectStatus(str, Enum):
    """Project statuses."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ProjectBase(BaseModel):
    """Base schema for projects."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )
    
    name: str = Field(
        min_length=1,
        max_length=100,
        pattern=r'^[a-zA-Z0-9_\-\s]+$',
        description="Project name",
        examples=["Animal Photos", "car_images", "dataset-2024"],
    )
    
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Project description",
        examples=["A collection of animal photos for ML training", None],
    )
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Strip whitespace and validate description."""
        if v:
            v = v.strip()
            if len(v) == 0:
                return None
        return v


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""
    pass


class ProjectUpdate(BaseModel):
    """Schema for updating project information."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )
    
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        pattern=r'^[a-zA-Z0-9_\-\s]+$',
        description="Updated project name",
    )
    
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Updated project description",
    )
    
    status: Optional[ProjectStatus] = Field(
        default=None,
        description="Project status",
    )


class ProjectResponse(ProjectBase):
    """Schema for project response."""
    
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
    )
    
    id: int = Field(description="Project ID")
    user_id: UUID = Field(description="Project owner ID")
    status: str = Field(description="Project status")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class ProjectDetailResponse(ProjectResponse):
    """Schema for detailed project response with relationships."""
    
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
    )
    
    crawl_jobs: list["CrawlJobResponse"] = Field(
        default_factory=list,
        description="Associated crawl jobs",
    )
    
    @property
    def total_jobs(self) -> int:
        """Get total number of crawl jobs."""
        return len(self.crawl_jobs)
    
    @property
    def active_jobs(self) -> int:
        """Get number of active crawl jobs."""
        return sum(1 for job in self.crawl_jobs if job.status == "running")
    
    @property
    def completed_jobs(self) -> int:
        """Get number of completed crawl jobs."""
        return sum(1 for job in self.crawl_jobs if job.status == "completed")
    
    @property
    def total_images(self) -> int:
        """Get total images from all jobs."""
        return sum(job.total_images for job in self.crawl_jobs)
    
    @property
    def total_valid_images(self) -> int:
        """Get total valid images from all jobs."""
        return sum(job.valid_images for job in self.crawl_jobs)
