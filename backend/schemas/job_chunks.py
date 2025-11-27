"""
Pydantic schemas for job chunk operations.

This module provides request and response schemas for job chunk management,
including creation, updates, and status tracking.

Classes:
    JobChunkStatus: Enum for chunk statuses
    ImageRange: Schema for image range tracking
    JobChunkCreate: Schema for creating chunks
    JobChunkUpdate: Schema for updating chunks
    JobChunkResponse: Schema for chunk responses
    JobChunkStatistics: Schema for chunk statistics
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

__all__ = [
    'JobChunkStatus',
    'ImageRange',
    'JobChunkCreate',
    'JobChunkUpdate',
    'JobChunkResponse',
    'JobChunkStatistics',
]


class JobChunkStatus(str, Enum):
    """Job chunk processing statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ImageRange(BaseModel):
    """
    Image range tracking for chunks.
    
    Attributes:
        start: Starting image index (0-based)
        end: Ending image index (inclusive)
    """
    start: int = Field(ge=0, description="Starting image index")
    end: int = Field(ge=0, description="Ending image index")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {"start": 0, "end": 499}
    })


class JobChunkCreate(BaseModel):
    """Schema for creating a new job chunk."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid',
    )
    
    job_id: int = Field(
        gt=0,
        description="Parent job ID",
        examples=[1, 42, 123],
    )
    
    chunk_index: int = Field(
        ge=0,
        description="Sequential chunk number within the job",
        examples=[0, 1, 2],
    )
    
    status: JobChunkStatus = Field(
        default=JobChunkStatus.PENDING,
        description="Initial chunk status",
    )
    
    priority: int = Field(
        default=5,
        ge=0,
        le=10,
        description="Processing priority (0-10, higher is more urgent)",
        examples=[5, 8, 10],
    )
    
    image_range: ImageRange = Field(
        description="Image range for this chunk",
    )
    
    task_id: Optional[str] = Field(
        default=None,
        description="Celery task ID (optional)",
    )


class JobChunkUpdate(BaseModel):
    """Schema for updating a job chunk."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )
    
    status: Optional[JobChunkStatus] = Field(
        default=None,
        description="New chunk status",
    )
    
    priority: Optional[int] = Field(
        default=None,
        ge=0,
        le=10,
        description="Updated priority",
    )
    
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if chunk failed",
    )
    
    task_id: Optional[str] = Field(
        default=None,
        description="Celery task ID",
    )


class JobChunkResponse(BaseModel):
    """Schema for job chunk response."""
    
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
    )
    
    id: int = Field(description="Chunk ID")
    job_id: int = Field(description="Parent job ID")
    chunk_index: int = Field(description="Sequential chunk number")
    status: str = Field(description="Chunk status")
    priority: int = Field(description="Processing priority (0-10)")
    image_range: dict = Field(description="Image range (start, end)")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    retry_count: int = Field(description="Number of retry attempts")
    task_id: Optional[str] = Field(default=None, description="Celery task ID")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class JobChunkStatistics(BaseModel):
    """Schema for job chunk statistics."""
    
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
    )
    
    job_id: int = Field(description="Job ID")
    total: int = Field(ge=0, description="Total number of chunks")
    pending: int = Field(ge=0, description="Number of pending chunks")
    processing: int = Field(ge=0, description="Number of processing chunks")
    completed: int = Field(ge=0, description="Number of completed chunks")
    failed: int = Field(ge=0, description="Number of failed chunks")
    
    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total == 0:
            return 0.0
        return (self.completed / self.total) * 100
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total == 0:
            return 0.0
        return (self.completed / self.total) * 100
