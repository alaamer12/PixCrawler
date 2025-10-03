"""
User-related Pydantic models and schemas.
"""

from datetime import datetime
from typing import Optional

from pydantic import EmailStr, Field

from .base import BaseSchema, TimestampMixin


class UserBase(BaseSchema):
    """Base user schema with common fields."""
    
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., min_length=1, max_length=100, description="User full name")
    is_active: bool = Field(default=True, description="Whether user is active")


class UserCreate(UserBase):
    """Schema for creating a new user."""
    
    password: str = Field(..., min_length=8, max_length=100, description="User password")


class UserUpdate(BaseSchema):
    """Schema for updating user information."""
    
    full_name: Optional[str] = Field(None, min_length=1, max_length=100, description="User full name")
    is_active: Optional[bool] = Field(None, description="Whether user is active")


class UserResponse(UserBase, TimestampMixin):
    """Schema for user response data."""
    
    id: int = Field(..., description="User ID")
    
    class Config:
        from_attributes = True


class UserLogin(BaseSchema):
    """Schema for user login."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenResponse(BaseSchema):
    """Schema for authentication token response."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TokenRefresh(BaseSchema):
    """Schema for token refresh request."""
    
    refresh_token: str = Field(..., description="Refresh token")