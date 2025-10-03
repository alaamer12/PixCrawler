"""
Authentication endpoints for Supabase Auth integration.

This module provides authentication endpoints that work with Supabase Auth,
including user profile management and token verification endpoints.

Note: Primary authentication (login/signup) is handled by Supabase Auth
directly from the frontend. These endpoints provide backend integration
and user profile management.
"""

from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_current_user
from backend.models.user import UserResponse
from backend.services.supabase_auth import SupabaseAuthService

__all__ = ['router']

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: SupabaseAuthService = Depends(),
) -> UserResponse:
    """
    Get current authenticated user profile.

    Returns the profile information for the currently authenticated user
    based on the Supabase JWT token.

    Args:
        current_user: Current authenticated user from dependency
        auth_service: Supabase authentication service

    Returns:
        Current user profile information

    Raises:
        HTTPException: If user profile is not found
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


@router.post("/verify-token")
async def verify_token(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Verify Supabase JWT token and return user information.

    This endpoint can be used by the frontend to verify that a token
    is still valid and get updated user information.

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


@router.post("/sync-profile")
async def sync_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: SupabaseAuthService = Depends(),
) -> Dict[str, str]:
    """
    Sync user profile from Supabase Auth to profiles table.

    This endpoint ensures that the user profile in the profiles table
    is synchronized with the Supabase Auth user data.

    Args:
        current_user: Current authenticated user from dependency
        auth_service: Supabase authentication service

    Returns:
        Success message
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
