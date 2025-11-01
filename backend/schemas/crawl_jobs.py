"""
Crawl job schemas for PixCrawler.

This module defines Pydantic schemas for crawl job management,
including creation, updates, and responses.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, computed_field

__all__ = [
    'CrawlJobStatus',
    'CrawlJobCreate',
    'CrawlJobUpdate',
    'CrawlJobResponse',
    'CrawlJobProgress',
    'JobLogEntry',
]


class CrawlJobStatus(str, Enum):
    """Crawl job statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CrawlJobCreate(BaseModel):
    """Schema for creating a new crawl job."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid',
    )
    
    project_id: int = Field(
        gt=0,
        description="Project ID",
        examples=[1, 42, 123],
    )
    
    name: str = Field(
        min_length=1,
        max_length=100,
        pattern=r'^[a-zA-Z0-9_\-\s]+$',
        description="Job name (alphanumeric, spaces, hyphens, underscores only)",
        examples=["Animal Photos Job", "car_images_crawl", "dataset-2024"],
    )
    
    keywords: list[str] = Field(
        min_length=1,
        max_length=50,
        description="List of search keywords",
        examples=[["cat", "dog", "bird"], ["car", "vehicle"]],
    )
    
    max_images: int = Field(
        default=1000,
        gt=0,
        le=100000,
        description="Maximum number of images to collect",
        examples=[100, 1000, 5000],
    )
    
    sources: list[str] = Field(
        default_factory=lambda: ["google", "bing"],
        description="Image sources to use",
        examples=[["google", "bing"], ["unsplash", "pixabay"]],
    )
    
    @field_validator('keywords')
    @classmethod
    def validate_keywords(cls, v: list[str]) -> list[str]:
        """Validate and clean keywords."""
        # Remove empty strings and strip whitespace
        cleaned = [k.strip() for k in v if k.strip()]
        
        if not cleaned:
            raise ValueError('At least one non-empty keyword is required')
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in cleaned:
            keyword_lower = keyword.lower()
            if keyword_lower not in seen:
                seen.add(keyword_lower)
                unique_keywords.append(keyword)
        
        return unique_keywords
    
    @field_validator('sources')
    @classmethod
    def validate_sources(cls, v: list[str]) -> list[str]:
        """Validate image sources."""
        valid_sources = {"google", "bing", "duckduckgo", "unsplash", "pixabay"}
        invalid = set(v) - valid_sources
        
        if invalid:
            raise ValueError(f"Invalid sources: {', '.join(invalid)}")
        
        return list(set(v))  # Remove duplicates


class CrawlJobUpdate(BaseModel):
    """Schema for updating crawl job."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )
    
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        pattern=r'^[a-zA-Z0-9_\-\s]+$',
    )
    
    status: Optional[CrawlJobStatus] = Field(
        default=None,
        description="Job status",
    )


class CrawlJobResponse(BaseModel):
    """Schema for crawl job response."""
    
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
    )
    
    id: int = Field(description="Job ID")
    project_id: int = Field(description="Project ID")
    name: str = Field(description="Job name")
    keywords: dict = Field(description="Search keywords (JSON)")
    max_images: int = Field(description="Maximum images to collect")
    status: str = Field(description="Job status")
    progress: int = Field(description="Progress percentage (0-100)")
    total_images: int = Field(description="Total images found")
    downloaded_images: int = Field(description="Images downloaded")
    valid_images: int = Field(description="Valid images")
    started_at: Optional[datetime] = Field(default=None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    
    @computed_field
    @property
    def success_rate(self) -> Optional[float]:
        """Calculate success rate."""
        if self.downloaded_images == 0:
            return None
        return round((self.valid_images / self.downloaded_images) * 100, 2)
    
    @computed_field
    @property
    def is_running(self) -> bool:
        """Check if job is running."""
        return self.status == "running"
    
    @computed_field
    @property
    def is_completed(self) -> bool:
        """Check if job is completed."""
        return self.status in ("completed", "failed", "cancelled")


class JobLogEntry(BaseModel):
    """Schema for a single job log entry."""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    action: str = Field(description="Action performed")
    timestamp: datetime = Field(description="Timestamp")
    metadata: Optional[dict[str, Any]] = Field(default=None, description="Additional data")


class CrawlJobProgress(BaseModel):
    """Schema for crawl job progress response."""
    
    model_config = ConfigDict(use_enum_values=True)
    
    status: str = Field(description="Current status")
    progress: int = Field(ge=0, le=100, description="Progress percentage")
    total_images: int = Field(ge=0, description="Total images found")
    downloaded_images: int = Field(ge=0, description="Images downloaded")
    valid_images: int = Field(ge=0, description="Valid images")
    current_keyword: Optional[str] = Field(default=None, description="Currently processing keyword")
    logs: list[JobLogEntry] = Field(default_factory=list, description="Recent log entries")
    
    @computed_field
    @property
    def remaining_images(self) -> int:
        """Calculate remaining images to download."""
        return max(0, self.total_images - self.downloaded_images)
