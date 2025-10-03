"""
User-related Pydantic models and schemas for the PixCrawler backend.

This module provides all user-related data models including user creation,
authentication, and response schemas with comprehensive validation and
type safety.

Classes:
    UserBase: Base user schema with common fields
    UserCreate: Schema for creating a new user account
    UserUpdate: Schema for updating user information
    UserResponse: Schema for user response data
    UserLogin: Schema for user authentication
    TokenResponse: Schema for authentication token response
    TokenRefresh: Schema for token refresh request

Features:
    - Email validation with Pydantic EmailStr
    - Password strength requirements
    - Comprehensive user data validation
    - JWT token response structures
"""

from typing import Optional
from uuid import UUID

from pydantic import EmailStr, Field

from .base import BaseSchema, TimestampMixin

__all__ = [
    'UserBase',
    'UserCreate',
    'UserUpdate',
    'UserResponse',
    'UserLogin',
    'TokenResponse',
    'TokenRefresh'
]


class UserBase(BaseSchema):
    """
    Base user schema with common fields.

    Contains the core user attributes that are shared across
    different user-related schemas.

    Attributes:
        email: User email address with validation
        full_name: User's full name
        is_active: Whether the user account is active
    """

    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., min_length=1, max_length=100,
                           description="User full name")
    is_active: bool = Field(default=True, description="Whether user is active")


class UserCreate(UserBase):
    """
    Schema for creating a new user account.

    Extends UserBase with password field for user registration.

    Attributes:
        password: User password with minimum length requirement
    """

    password: str = Field(..., min_length=8, max_length=100,
                          description="User password")


class UserUpdate(BaseSchema):
    """
    Schema for updating user information.

    All fields are optional to support partial updates.

    Attributes:
        full_name: Updated user full name
        is_active: Updated user active status
    """

    full_name: Optional[str] = Field(None, min_length=1, max_length=100,
                                     description="User full name")
    is_active: Optional[bool] = Field(None, description="Whether user is active")


class UserResponse(UserBase, TimestampMixin):
    """
    Schema for user response data.

    Includes all user information returned by the API,
    with timestamps for audit trails.

    Attributes:
        id: Unique user identifier
    """

    id: UUID = Field(..., description="User ID (UUID from Supabase auth)")


class UserLogin(BaseSchema):
    """
    Schema for user authentication.

    Contains credentials required for user login.

    Attributes:
        email: User email address
        password: User password
    """

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenResponse(BaseSchema):
    """
    Schema for authentication token response.

    Contains JWT tokens and metadata returned after successful authentication.

    Attributes:
        access_token: JWT access token for API authentication
        refresh_token: JWT refresh token for token renewal
        token_type: Token type (always "bearer")
        expires_in: Token expiration time in seconds
    """

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TokenRefresh(BaseSchema):
    """
    Schema for token refresh request.

    Contains the refresh token needed to obtain new access tokens.

    Attributes:
        refresh_token: Valid refresh token
    """

    refresh_token: str = Field(..., description="Refresh token")
