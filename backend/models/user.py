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

from pydantic import EmailStr, Field, field_validator, SecretStr

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

    email: EmailStr = Field(
        ..., 
        description="User email address",
        examples=["user@example.com", "john.doe@company.org"]
    )
    full_name: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        pattern=r'^[a-zA-Z\s\-\.\']+$',
        description="User full name (letters, spaces, hyphens, dots, apostrophes only)",
        examples=["John Doe", "Mary Jane Smith", "José María García"]
    )
    is_active: bool = Field(
        default=True, 
        description="Whether user account is active",
        examples=[True, False]
    )

    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        """Validate and clean full name."""
        cleaned = ' '.join(v.split())  # Remove extra whitespace
        if len(cleaned.split()) < 2:
            raise ValueError("Full name must contain at least first and last name")
        return cleaned


class UserCreate(UserBase):
    """
    Schema for creating a new user account.

    Extends UserBase with password field for user registration.

    Attributes:
        password: User password with strength requirements
    """

    password: SecretStr = Field(
        ..., 
        min_length=8, 
        max_length=128,
        description="User password (minimum 8 characters, must contain uppercase, lowercase, digit, and special character)"
    )

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: SecretStr) -> SecretStr:
        """Validate password strength requirements."""
        password = v.get_secret_value()
        
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
            
        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain at least one uppercase letter")
            
        if not any(c.islower() for c in password):
            raise ValueError("Password must contain at least one lowercase letter")
            
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one digit")
            
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            raise ValueError("Password must contain at least one special character")
            
        return v


class UserUpdate(BaseSchema):
    """
    Schema for updating user information.

    All fields are optional to support partial updates.

    Attributes:
        full_name: Updated user full name
        is_active: Updated user active status
    """

    full_name: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=100,
        pattern=r'^[a-zA-Z\s\-\.\']+$',
        description="Updated user full name",
        examples=["John Smith", None]
    )
    is_active: Optional[bool] = Field(
        None, 
        description="Updated user active status",
        examples=[True, False, None]
    )

    @field_validator('full_name')
    @classmethod
    def validate_full_name_update(cls, v: Optional[str]) -> Optional[str]:
        """Validate full name if provided."""
        if v is not None:
            cleaned = ' '.join(v.split())
            if len(cleaned.split()) < 2:
                raise ValueError("Full name must contain at least first and last name")
            return cleaned
        return v


class UserResponse(UserBase, TimestampMixin):
    """
    Schema for user response data.

    Includes all user information returned by the API,
    with timestamps for audit trails.

    Attributes:
        id: Unique user identifier
    """

    id: UUID = Field(
        ..., 
        description="User ID (UUID from Supabase auth)",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )


class UserLogin(BaseSchema):
    """
    Schema for user authentication.

    Contains credentials required for user login.

    Attributes:
        email: User email address
        password: User password
    """

    email: EmailStr = Field(
        ..., 
        description="User email address",
        examples=["user@example.com"]
    )
    password: SecretStr = Field(
        ..., 
        min_length=1,
        description="User password"
    )


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

    access_token: str = Field(
        ..., 
        min_length=10,
        description="JWT access token",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
    refresh_token: str = Field(
        ..., 
        min_length=10,
        description="JWT refresh token",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
    token_type: str = Field(
        default="bearer", 
        pattern=r'^bearer$',
        description="Token type (always 'bearer')",
        examples=["bearer"]
    )
    expires_in: int = Field(
        ..., 
        gt=0,
        le=86400,  # Max 24 hours
        description="Token expiration time in seconds",
        examples=[3600, 7200, 86400]
    )


class TokenRefresh(BaseSchema):
    """
    Schema for token refresh request.

    Contains the refresh token needed to obtain new access tokens.

    Attributes:
        refresh_token: Valid refresh token
    """

    refresh_token: str = Field(
        ..., 
        min_length=10,
        description="Valid refresh token",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
