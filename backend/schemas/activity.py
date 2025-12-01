"""
Activity log schemas for PixCrawler.

This module defines Pydantic schemas for activity log management,
including listing and filtering activity logs.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    'ActivityLogBase',
    'ActivityLogResponse',
    'ActivityLogListResponse',
]


class ActivityLogBase(BaseModel):
    """Base schema for activity logs."""
    
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
    )
    
    action: str = Field(
        description="Action description",
        examples=["Created project", "Started crawl job", "Deleted dataset"],
    )
    
    resource_type: Optional[str] = Field(
        default=None,
        description="Type of resource affected",
        examples=["project", "crawl_job", "dataset", "api_key"],
    )
    
    resource_id: Optional[str] = Field(
        default=None,
        description="ID of resource affected",
        examples=["1", "123e4567-e89b-12d3-a456-426614174000"],
    )
    
    metadata: Optional[dict] = Field(
        default=None,
        description="Additional event metadata",
        examples=[{"project_name": "Animals Dataset", "status": "completed"}],
    )


class ActivityLogResponse(ActivityLogBase):
    """Schema for activity log responses."""
    
    id: int = Field(description="Log ID")
    user_id: Optional[UUID] = Field(default=None, description="User ID (None for system events)")
    timestamp: datetime = Field(description="Event timestamp")


class ActivityLogListResponse(BaseModel):
    """Schema for activity log list response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    data: list[ActivityLogResponse] = Field(
        description="List of activity logs",
        examples=[[{
            "id": 1,
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "action": "Created project 'Animals Dataset'",
            "resource_type": "project",
            "resource_id": "1",
            "metadata": {"project_name": "Animals Dataset"},
            "timestamp": "2024-01-27T10:00:00Z"
        }]]
    )
    
    meta: dict = Field(
        default_factory=lambda: {"total": 0, "skip": 0, "limit": 50},
        description="Pagination metadata",
        examples=[{"total": 100, "skip": 0, "limit": 50}]
    )
