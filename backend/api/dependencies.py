"""
FastAPI dependencies for authentication and authorization.

This module provides FastAPI dependencies for handling authentication,
authorization, and user context throughout the PixCrawler backend API.

Functions:
    get_current_user: Get current authenticated user from Supabase token
    get_current_user_optional: Get current user or None if not authenticated
    get_supabase_auth_service: Get Supabase authentication service instance

Features:
    - Supabase JWT token extraction and verification
    - User context injection into API endpoints
    - Optional authentication support
    - Comprehensive error handling
"""

from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.core.exceptions import AuthenticationError
from backend.services.supabase_auth import SupabaseAuthService

__all__ = [
    'get_current_user',
    'get_current_user_optional',
    'get_supabase_auth_service'
]

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


def get_supabase_auth_service() -> SupabaseAuthService:
    """
    Get Supabase authentication service instance.

    FastAPI dependency that provides a Supabase authentication
    service instance for use in API endpoints.

    Returns:
        SupabaseAuthService instance
    """
    return SupabaseAuthService()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: SupabaseAuthService = Depends(get_supabase_auth_service)
) -> Dict[str, Any]:
    """
    Get current authenticated user from Supabase token.

    FastAPI dependency that extracts and verifies the Supabase JWT token
    from the Authorization header and returns the authenticated user information.

    Args:
        credentials: HTTP Bearer token credentials
        auth_service: Supabase authentication service

    Returns:
        Authenticated user information

    Raises:
        HTTPException: If authentication fails or token is missing
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_info = await auth_service.verify_token(credentials.credentials)

        # Get user profile from database
        profile = await auth_service.get_user_profile(user_info["user_id"])

        return {
            **user_info,
            "profile": profile
        }

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: SupabaseAuthService = Depends(get_supabase_auth_service)
) -> Optional[Dict[str, Any]]:
    """
    Get current user or None if not authenticated.

    FastAPI dependency that optionally extracts and verifies the Supabase JWT token.
    Returns None if no token is provided or if authentication fails.

    Args:
        credentials: HTTP Bearer token credentials (optional)
        auth_service: Supabase authentication service

    Returns:
        Authenticated user information or None
    """
    if not credentials:
        return None

    try:
        user_info = await auth_service.verify_token(credentials.credentials)

        # Get user profile from database
        profile = await auth_service.get_user_profile(user_info["user_id"])

        return {
            **user_info,
            "profile": profile
        }

    except Exception:
        # Return None for any authentication errors in optional auth
        return None
