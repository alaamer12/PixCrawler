"""
API key schemas for PixCrawler.

This module defines Pydantic schemas for API key management,
including creation, updates, and responses.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, computed_field

__all__ = [
    'APIKeyStatus',
    'APIKeyPermission',
    'APIKeyBase',
    'APIKeyCreate',
    'APIKeyUpdate',
    'APIKeyResponse',
    'APIKeyRegenerateRequest',
]


class APIKeyStatus(str, Enum):
    """API key statuses."""
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class APIKeyPermission(str, Enum):
    """API key permissions."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    CRAWL_JOBS_CREATE = "crawl_jobs:create"
    CRAWL_JOBS_READ = "crawl_jobs:read"
    CRAWL_JOBS_CANCEL = "crawl_jobs:cancel"
    DATASETS_READ = "datasets:read"
    DATASETS_EXPORT = "datasets:export"


class APIKeyBase(BaseModel):
    """Base schema for API keys."""
    
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        use_enum_values=True,
    )
    
    name: str = Field(
        min_length=1,
        max_length=200,
        description="User-friendly key name",
        examples=["Production API Key", "Development Key"],
    )
    
    permissions: list[APIKeyPermission] = Field(
        default_factory=list,
        description="List of permissions",
        examples=[["read", "write"], ["crawl_jobs:create", "crawl_jobs:read"]],
    )
    
    rate_limit: int = Field(
        default=1000,
        gt=0,
        le=100000,
        description="Requests per hour limit",
        examples=[1000, 5000, 10000],
    )
    
    expires_at: Optional[datetime] = Field(
        default=None,
        description="Optional expiration timestamp",
    )
    
    @field_validator('permissions')
    @classmethod
    def validate_permissions(cls, v: list[str]) -> list[str]:
        """Ensure no duplicate permissions."""
        if len(v) != len(set(v)):
            raise ValueError('Duplicate permissions are not allowed')
        return v


class APIKeyCreate(APIKeyBase):
    """Schema for creating API keys."""
    
    user_id: UUID = Field(description="User ID")


class APIKeyUpdate(BaseModel):
    """Schema for updating API keys."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True,
    )
    
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="User-friendly key name",
    )
    
    permissions: Optional[list[APIKeyPermission]] = Field(
        default=None,
        description="List of permissions",
    )
    
    rate_limit: Optional[int] = Field(
        default=None,
        gt=0,
        le=100000,
        description="Requests per hour limit",
    )
    
    status: Optional[APIKeyStatus] = Field(
        default=None,
        description="Key status",
    )


class APIKeyResponse(APIKeyBase):
    """Schema for API key responses."""
    
    id: UUID = Field(description="Key ID")
    user_id: UUID = Field(description="User ID")
    key_prefix: str = Field(description="Key prefix for identification")
    status: APIKeyStatus = Field(description="Key status")
    usage_count: int = Field(description="Total number of uses")
    last_used_at: Optional[datetime] = Field(default=None, description="Last usage timestamp")
    last_used_ip: Optional[str] = Field(default=None, description="Last IP address")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    
    # Never expose the actual key hash
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        use_enum_values=True,
        exclude={'key_hash'},
    )
    
    @computed_field
    @property
    def is_active(self) -> bool:
        """Check if key is active and not expired."""
        if self.status != APIKeyStatus.ACTIVE:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True
    
    @computed_field
    @property
    def is_expired(self) -> bool:
        """Check if key is expired."""
        if self.expires_at and self.expires_at < datetime.utcnow():
            return True
        return False


class APIKeyRegenerateRequest(BaseModel):
    """Schema for regenerating API keys."""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    key_id: UUID = Field(description="Key ID to regenerate")


class APIKeyCreateResponse(APIKeyResponse):
    """Schema for API key creation response (includes full key once)."""
    
    key: str = Field(
        description="Full API key (only shown once)",
        examples=["pk_live_1234567890abcdef"],
    )
