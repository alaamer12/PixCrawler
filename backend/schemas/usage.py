"""
Usage and analytics schemas for PixCrawler.

This module defines Pydantic schemas for usage tracking,
metrics, and analytics.
"""

from datetime import date as Date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

__all__ = [
    'UsageMetricBase',
    'UsageMetricCreate',
    'UsageMetricUpdate',
    'UsageMetricResponse',
    'UsageSummary',
    'UsageTrend',
]


class UsageMetricBase(BaseModel):
    """Base schema for usage metrics."""
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
    )
    
    images_processed: int = Field(
        default=0,
        ge=0,
        description="Images processed count",
        examples=[500, 1000],
    )
    
    images_limit: int = Field(
        default=10000,
        gt=0,
        description="Images processing limit",
        examples=[10000, 50000],
    )
    
    storage_used_gb: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        description="Storage used in GB",
        examples=[Decimal("5.50"), Decimal("25.75")],
    )
    
    storage_limit_gb: Decimal = Field(
        default=Decimal("100.00"),
        gt=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        description="Storage limit in GB",
        examples=[Decimal("100.00"), Decimal("500.00")],
    )
    
    api_calls: int = Field(
        default=0,
        ge=0,
        description="API calls count",
        examples=[1000, 5000],
    )
    
    api_calls_limit: int = Field(
        default=50000,
        gt=0,
        description="API calls limit",
        examples=[50000, 100000],
    )
    
    bandwidth_used_gb: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        description="Bandwidth used in GB",
        examples=[Decimal("10.50"), Decimal("50.25")],
    )
    
    bandwidth_limit_gb: Decimal = Field(
        default=Decimal("500.00"),
        gt=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        description="Bandwidth limit in GB",
        examples=[Decimal("500.00"), Decimal("1000.00")],
    )


class UsageMetricCreate(UsageMetricBase):
    """Schema for creating usage metrics."""
    
    user_id: UUID = Field(description="User ID")
    metric_date: Date = Field(description="Date for metrics")


class UsageMetricUpdate(BaseModel):
    """Schema for updating usage metrics."""
    
    model_config = ConfigDict(validate_assignment=True)
    
    images_processed: Optional[int] = Field(default=None, ge=0)
    storage_used_gb: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))
    api_calls: Optional[int] = Field(default=None, ge=0)
    bandwidth_used_gb: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))


class UsageMetricResponse(UsageMetricBase):
    """Schema for usage metric responses."""
    
    id: UUID = Field(description="Metric ID")
    user_id: UUID = Field(description="User ID")
    metric_date: Date = Field(description="Date for metrics")
    created_at: datetime = Field(description="Creation timestamp")
    
    @computed_field
    @property
    def images_usage_percent(self) -> float:
        """Calculate images usage percentage."""
        if self.images_limit == 0:
            return 0.0
        return round((self.images_processed / self.images_limit) * 100, 2)
    
    @computed_field
    @property
    def storage_usage_percent(self) -> float:
        """Calculate storage usage percentage."""
        if self.storage_limit_gb == 0:
            return 0.0
        return round(float(self.storage_used_gb / self.storage_limit_gb) * 100, 2)
    
    @computed_field
    @property
    def api_calls_usage_percent(self) -> float:
        """Calculate API calls usage percentage."""
        if self.api_calls_limit == 0:
            return 0.0
        return round((self.api_calls / self.api_calls_limit) * 100, 2)
    
    @computed_field
    @property
    def bandwidth_usage_percent(self) -> float:
        """Calculate bandwidth usage percentage."""
        if self.bandwidth_limit_gb == 0:
            return 0.0
        return round(float(self.bandwidth_used_gb / self.bandwidth_limit_gb) * 100, 2)
    
    @computed_field
    @property
    def is_over_limit(self) -> bool:
        """Check if any metric is over limit."""
        return (
            self.images_processed > self.images_limit
            or self.storage_used_gb > self.storage_limit_gb
            or self.api_calls > self.api_calls_limit
            or self.bandwidth_used_gb > self.bandwidth_limit_gb
        )
    
    @computed_field
    @property
    def is_near_limit(self) -> bool:
        """Check if any metric is near limit (>80%)."""
        return (
            self.images_usage_percent > 80
            or self.storage_usage_percent > 80
            or self.api_calls_usage_percent > 80
            or self.bandwidth_usage_percent > 80
        )


class UsageSummary(BaseModel):
    """Schema for usage summary across multiple days."""
    
    model_config = ConfigDict(validate_assignment=True)
    
    total_images_processed: int = Field(ge=0, description="Total images processed")
    total_storage_used_gb: Decimal = Field(ge=Decimal("0.00"), description="Total storage used")
    total_api_calls: int = Field(ge=0, description="Total API calls")
    total_bandwidth_used_gb: Decimal = Field(ge=Decimal("0.00"), description="Total bandwidth used")
    
    average_daily_images: float = Field(ge=0.0, description="Average daily images")
    average_daily_storage_gb: Decimal = Field(ge=Decimal("0.00"), description="Average daily storage")
    average_daily_api_calls: float = Field(ge=0.0, description="Average daily API calls")
    average_daily_bandwidth_gb: Decimal = Field(ge=Decimal("0.00"), description="Average daily bandwidth")
    
    period_start: Date = Field(description="Period start date")
    period_end: Date = Field(description="Period end date")
    days_count: int = Field(gt=0, description="Number of days in period")


class UsageTrend(BaseModel):
    """Schema for usage trend data."""
    
    model_config = ConfigDict(validate_assignment=True)
    
    trend_date: Date = Field(description="Date")
    images_processed: int = Field(ge=0, description="Images processed")
    storage_used_gb: Decimal = Field(ge=Decimal("0.00"), description="Storage used")
    api_calls: int = Field(ge=0, description="API calls")
    bandwidth_used_gb: Decimal = Field(ge=Decimal("0.00"), description="Bandwidth used")
