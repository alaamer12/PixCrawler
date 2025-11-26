"""
Project schemas for PixCrawler.

This module defines Pydantic schemas for Project validation and serialization.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    'ProjectBase',
    'ProjectCreate',
    'ProjectUpdate',
    'ProjectResponse',
    'ProjectListResponse',
]


class ProjectBase(BaseModel):
    """Base schema for Project."""
    
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
    )
    
    name: str = Field(
        min_length=1,
        max_length=100,
        description="Project name",
        examples=["Animal Classification", "Vehicle Detection"],
    )
    
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Project description",
        examples=["Dataset for classifying different animal species"],
    )


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""
    pass


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Project name",
    )
    
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Project description",
    )


class ProjectResponse(ProjectBase):
    """Schema for project response."""
    
    id: int = Field(description="Project ID")
    user_id: UUID = Field(description="User ID")
    status: str = Field(description="Project status")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    dataset_count: Optional[int] = Field(default=0, description="Number of datasets")
    image_count: Optional[int] = Field(default=0, description="Total images in project")


class ProjectListResponse(BaseModel):
    """Schema for list of projects response."""
    
    data: list[ProjectResponse]
    meta: dict = Field(default_factory=dict, description="Pagination metadata")
