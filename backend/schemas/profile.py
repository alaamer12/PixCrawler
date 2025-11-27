"""
Profile schemas for PixCrawler.

This module defines Pydantic schemas for user profile management,
including creation, updates, and responses.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator, HttpUrl

__all__ = [
    'UserRole',
    'ProfileBase',
    'ProfileCreate',
    'ProfileUpdate',
    'ProfileResponse',
    'ProfileListResponse',
    'ProfileSettings',
]


class UserRole(str, Enum):
    """User roles."""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


class ProfileBase(BaseModel):
    """Base schema for user profiles."""
    
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        use_enum_values=True,
    )
    
    email: EmailStr = Field(
        description="User email address",
        examples=["user@example.com"],
    )
    
    full_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="User's full name",
        examples=["John Doe"],
    )
    
    avatar_url: Optional[HttpUrl] = Field(
        default=None,
        description="URL to user's avatar image",
        examples=["https://example.com/avatar.jpg"],
    )
    
    # Professional information
    bio: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="User biography",
    )
    
    company: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Company name",
        examples=["Acme Corp"],
    )
    
    job_title: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Job title",
        examples=["ML Engineer", "Data Scientist"],
    )
    
    location: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Location",
        examples=["San Francisco, CA"],
    )
    
    website: Optional[HttpUrl] = Field(
        default=None,
        description="Personal or company website",
        examples=["https://example.com"],
    )
    
    # Social links
    linkedin_username: Optional[str] = Field(
        default=None,
        max_length=100,
        pattern=r'^[a-zA-Z0-9-]+$',
        description="LinkedIn username",
        examples=["johndoe"],
    )
    
    github_username: Optional[str] = Field(
        default=None,
        max_length=100,
        pattern=r'^[a-zA-Z0-9-]+$',
        description="GitHub username",
        examples=["johndoe"],
    )
    
    twitter_username: Optional[str] = Field(
        default=None,
        max_length=100,
        pattern=r'^[a-zA-Z0-9_]+$',
        description="Twitter username",
        examples=["johndoe"],
    )
    
    @field_validator('bio')
    @classmethod
    def validate_bio(cls, v: Optional[str]) -> Optional[str]:
        """Strip whitespace and validate bio."""
        if v:
            v = v.strip()
            if len(v) == 0:
                return None
        return v


class ProfileCreate(ProfileBase):
    """Schema for creating user profiles."""
    
    id: UUID = Field(description="User ID (from Supabase auth)")
    role: UserRole = Field(default=UserRole.USER, description="User role")


class ProfileUpdate(BaseModel):
    """Schema for updating user profiles."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True,
    )
    
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    avatar_url: Optional[HttpUrl] = Field(default=None)
    bio: Optional[str] = Field(default=None, max_length=1000)
    company: Optional[str] = Field(default=None, max_length=200)
    job_title: Optional[str] = Field(default=None, max_length=200)
    location: Optional[str] = Field(default=None, max_length=200)
    website: Optional[HttpUrl] = Field(default=None)
    linkedin_username: Optional[str] = Field(default=None, max_length=100, pattern=r'^[a-zA-Z0-9-]+$')
    github_username: Optional[str] = Field(default=None, max_length=100, pattern=r'^[a-zA-Z0-9-]+$')
    twitter_username: Optional[str] = Field(default=None, max_length=100, pattern=r'^[a-zA-Z0-9_]+$')


class ProfileResponse(ProfileBase):
    """Schema for profile responses."""
    
    id: UUID = Field(description="User ID")
    role: UserRole = Field(description="User role")
    created_at: datetime = Field(description="Profile creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class ProfileListResponse(BaseModel):
    """Schema for profile list response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    data: list[ProfileResponse] = Field(
        description="List of user profiles",
        examples=[[{
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "email": "user@example.com",
            "full_name": "John Doe",
            "avatar_url": "https://example.com/avatar.jpg",
            "role": "user",
            "bio": "ML Engineer",
            "company": "Acme Corp",
            "job_title": "Senior ML Engineer",
            "location": "San Francisco, CA",
            "website": "https://johndoe.com",
            "linkedin_username": "johndoe",
            "github_username": "johndoe",
            "twitter_username": "johndoe",
            "created_at": "2024-01-20T10:00:00Z",
            "updated_at": "2024-01-27T10:00:00Z"
        }]]
    )
    
    meta: dict = Field(
        default_factory=lambda: {"total": 0, "skip": 0, "limit": 50},
        description="Pagination metadata",
        examples=[{"total": 100, "skip": 0, "limit": 50}]
    )


class ProfileSettings(BaseModel):
    """Schema for user settings."""
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
    )
    
    # Preferences
    timezone: str = Field(
        default="UTC",
        max_length=100,
        description="User timezone",
        examples=["UTC", "America/New_York", "Europe/London"],
    )
    
    language: str = Field(
        default="en",
        max_length=10,
        pattern=r'^[a-z]{2}(-[A-Z]{2})?$',
        description="Language code",
        examples=["en", "en-US", "es"],
    )
    
    public_profile: bool = Field(
        default=False,
        description="Make profile publicly visible",
    )
    
    email_notifications: bool = Field(
        default=True,
        description="Enable email notifications",
    )
    
    marketing_emails: bool = Field(
        default=False,
        description="Receive marketing emails",
    )
    
    # Appearance
    theme: str = Field(
        default="system",
        pattern=r'^(light|dark|system)$',
        description="UI theme preference",
        examples=["light", "dark", "system"],
    )
    
    compact_mode: bool = Field(
        default=False,
        description="Use compact UI mode",
    )
    
    # Workspace
    default_view: str = Field(
        default="grid",
        pattern=r'^(grid|list)$',
        description="Default view mode",
        examples=["grid", "list"],
    )
    
    items_per_page: int = Field(
        default=20,
        ge=10,
        le=100,
        description="Items per page",
        examples=[20, 50, 100],
    )
    
    show_thumbnails: bool = Field(
        default=True,
        description="Show image thumbnails",
    )
    
    auto_expand_folders: bool = Field(
        default=False,
        description="Auto-expand folder trees",
    )
    
    confirm_delete: bool = Field(
        default=True,
        description="Confirm before deleting",
    )
    
    # Privacy
    show_activity: bool = Field(
        default=True,
        description="Show activity in profile",
    )
    
    allow_analytics: bool = Field(
        default=True,
        description="Allow usage analytics",
    )
