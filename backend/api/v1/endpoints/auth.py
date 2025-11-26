"""
Authentication utility endpoints for Supabase Auth integration.

This module provides utility endpoints for Supabase Auth integration.
Primary authentication (login/signup/logout) is handled directly by Supabase Auth
from the frontend using Supabase client libraries.

These endpoints provide:
- User profile retrieval
- Token verification
- Profile synchronization between Supabase Auth and profiles table

Note: Authentication flow:
1. Frontend uses Supabase Auth client for login/signup
2. Frontend receives JWT token from Supabase
3. Frontend sends token in Authorization header to backend
4. Backend verifies token using get_current_user dependency
"""
from typing import Union

from fastapi import APIRouter, HTTPException, status

from backend.api.types import CurrentUser, SupabaseAuthServiceDep
from backend.api.v1.response_models import get_common_responses
from backend.schemas.user import UserResponse

__all__ = ['router']

router = APIRouter(
    tags=["Authentication"],
    responses=get_common_responses(401, 500),
)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current User Profile",
    description="Retrieve the authenticated user's profile information from Supabase Auth.",
    response_description="User profile with email, name, and account details",
    operation_id="getCurrentUserProfile",
    responses={
        200: {
            "description": "Successfully retrieved user profile",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "email": "user@example.com",
                        "full_name": "John Doe",
                        "is_active": True,
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z"
                    }
                }
            }
        },
        **get_common_responses(401, 500)
    }
)
async def get_current_user_profile(
    current_user: CurrentUser,
    auth_service: SupabaseAuthServiceDep,
) -> UserResponse:
    """
    Get current authenticated user profile.

    Returns the profile information for the currently authenticated user
    based on the Supabase JWT token provided in the Authorization header.

    **Authentication Required:** Bearer token from Supabase Auth

    Args:
        current_user: Current authenticated user from dependency
        auth_service: Supabase authentication service

    Returns:
        Current user profile information

    Raises:
        HTTPException: If user profile is not found or token is invalid
    """
    try:
        profile = current_user["profile"]

        return UserResponse(
            id=profile["id"],
            email=profile["email"],
            full_name=profile.get("full_name", ""),
            is_active=True,  # Supabase users are active by default
            created_at=profile["created_at"],
            updated_at=profile["updated_at"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )


@router.post(
    "/verify-token",
    summary="Verify JWT Token",
    description="Validate a Supabase JWT token and return user information if valid.",
    response_description="Token validation result with user details",
    operation_id="verifyAuthToken",
    responses={
        200: {
            "description": "Token is valid",
            "content": {
                "application/json": {
                    "example": {
                        "valid": True,
                        "user": {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "email": "user@example.com",
                            "profile": {
                                "full_name": "John Doe",
                                "avatar_url": "https://example.com/avatar.jpg"
                            }
                        }
                    }
                }
            }
        },
        **get_common_responses(401, 500)
    }
)
async def verify_token(
    current_user: CurrentUser
) -> dict[str, Union[bool, dict[str, str]]]:
    """
    Verify Supabase JWT token and return user information.

    This endpoint validates the JWT token provided in the Authorization header
    and returns the associated user information if the token is valid.

    **Use Case:** Frontend can use this to check if a stored token is still valid
    before making authenticated requests.

    **Authentication Required:** Bearer token from Supabase Auth

    Args:
        current_user: Current authenticated user from dependency

    Returns:
        Token verification result with user information
    """
    return {
        "valid": True,
        "user": {
            "id": current_user["user_id"],
            "email": current_user["email"],
            "profile": current_user["profile"]
        }
    }


@router.post(
    "/sync-profile",
    summary="Sync User Profile",
    description="Synchronize user profile data from Supabase Auth to the profiles table.",
    response_description="Profile synchronization result",
    operation_id="syncUserProfile",
    responses={
        200: {
            "description": "Profile synchronized successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "created": {
                            "summary": "Profile created",
                            "value": {"message": "User profile created successfully"}
                        },
                        "updated": {
                            "summary": "Profile updated",
                            "value": {"message": "User profile updated successfully"}
                        }
                    }
                }
            }
        },
        **get_common_responses(401, 500)
    }
)
async def sync_user_profile(
    current_user: CurrentUser,
    auth_service: SupabaseAuthServiceDep,
) -> dict[str, str]:
    """
    Sync user profile from Supabase Auth to profiles table.

    This endpoint ensures that the user profile in the profiles table
    is synchronized with the Supabase Auth user data. It will create
    a new profile if one doesn't exist, or update the existing profile.

    **Use Case:** Call this after OAuth login to ensure profile data is up-to-date
    with the latest information from the authentication provider.

    **Authentication Required:** Bearer token from Supabase Auth

    Args:
        current_user: Current authenticated user from dependency
        auth_service: Supabase authentication service

    Returns:
        Success message indicating whether profile was created or updated
    """
    try:
        user_id = current_user["user_id"]
        email = current_user["email"]
        user_metadata = current_user.get("user_metadata", {})

        # Check if profile exists
        try:
            await auth_service.get_user_profile(user_id)
            # Profile exists, update it
            await auth_service.update_user_profile(user_id, {
                "email": email,
                "full_name": user_metadata.get("full_name"),
                "avatar_url": user_metadata.get("avatar_url"),
                "updated_at": "now()"
            })
            action = "updated"

        except Exception:
            # Profile doesn't exist, create it
            await auth_service.create_user_profile({
                "id": user_id,
                "email": email,
                "full_name": user_metadata.get("full_name"),
                "avatar_url": user_metadata.get("avatar_url"),
                "role": "user"
            })
            action = "created"

        return {"message": f"User profile {action} successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync user profile"
        )
