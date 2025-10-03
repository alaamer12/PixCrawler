"""
Supabase authentication service for user authentication and authorization.

This module provides integration with Supabase Auth for the PixCrawler backend,
handling user authentication, token verification, and user profile management
through Supabase's authentication system.

Classes:
    SupabaseAuthService: Service for handling Supabase authentication

Functions:
    get_user_from_token: Extract user information from Supabase JWT token
    verify_supabase_token: Verify Supabase JWT token

Features:
    - Supabase Auth integration
    - JWT token verification
    - User profile management
    - Row Level Security (RLS) support
"""

from typing import Optional, Dict, Any
import jwt
from supabase import create_client, Client

from backend.core.config import get_settings
from backend.core.exceptions import AuthenticationError, NotFoundError
from .base import BaseService

__all__ = [
    'SupabaseAuthService',
    'get_user_from_token',
    'verify_supabase_token'
]


class SupabaseAuthService(BaseService):
    """
    Service for handling Supabase authentication and authorization.

    Provides integration with Supabase Auth for user authentication,
    token verification, and user profile management.

    Attributes:
        settings: Application settings instance
        supabase: Supabase client instance
    """

    def __init__(self) -> None:
        """Initialize Supabase authentication service."""
        super().__init__()
        self.settings = get_settings()
        self.supabase: Client = create_client(
            self.settings.supabase_url,
            self.settings.supabase_service_role_key
        )

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify Supabase JWT token and return user information.

        Validates the Supabase JWT token and extracts user information
        from the token payload.

        Args:
            token: Supabase JWT token to verify

        Returns:
            User information from token payload

        Raises:
            AuthenticationError: If token is invalid or expired
        """
        try:
            # Verify token with Supabase
            response = self.supabase.auth.get_user(token)

            if response.user is None:
                raise AuthenticationError("Invalid or expired token")

            return {
                "user_id": response.user.id,
                "email": response.user.email,
                "user_metadata": response.user.user_metadata,
                "app_metadata": response.user.app_metadata,
            }

        except Exception as e:
            self.logger.error(f"Token verification failed: {str(e)}")
            raise AuthenticationError(f"Token verification failed: {str(e)}")

    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile from the profiles table.

        Retrieves user profile information from the database
        using the Supabase user ID.

        Args:
            user_id: Supabase user ID

        Returns:
            User profile data or None if not found

        Raises:
            NotFoundError: If user profile is not found
        """
        try:
            response = self.supabase.table("profiles").select("*").eq("id",
                                                                      user_id).execute()

            if not response.data:
                raise NotFoundError(f"User profile not found for ID: {user_id}")

            return response.data[0]

        except Exception as e:
            self.logger.error(f"Failed to get user profile: {str(e)}")
            raise NotFoundError(f"User profile not found: {str(e)}")

    async def create_user_profile(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create user profile in the profiles table.

        Creates a new user profile record in the database
        when a user signs up through Supabase Auth.

        Args:
            user_data: User profile data

        Returns:
            Created user profile data

        Raises:
            ValidationError: If user data is invalid
        """
        try:
            response = self.supabase.table("profiles").insert(user_data).execute()

            if not response.data:
                raise Exception("Failed to create user profile")

            self.log_operation("create_user_profile", user_id=user_data.get("id"))
            return response.data[0]

        except Exception as e:
            self.logger.error(f"Failed to create user profile: {str(e)}")
            raise

    async def update_user_profile(self, user_id: str, update_data: Dict[str, Any]) -> \
        Dict[str, Any]:
        """
        Update user profile in the profiles table.

        Updates an existing user profile record in the database.

        Args:
            user_id: Supabase user ID
            update_data: Profile data to update

        Returns:
            Updated user profile data

        Raises:
            NotFoundError: If user profile is not found
        """
        try:
            response = (
                self.supabase.table("profiles")
                .update(update_data)
                .eq("id", user_id)
                .execute()
            )

            if not response.data:
                raise NotFoundError(f"User profile not found for ID: {user_id}")

            self.log_operation("update_user_profile", user_id=user_id)
            return response.data[0]

        except Exception as e:
            self.logger.error(f"Failed to update user profile: {str(e)}")
            raise


def get_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Extract user information from Supabase JWT token without verification.

    Decodes the JWT token to extract user information without
    verifying the signature. Use only for non-critical operations.

    Args:
        token: Supabase JWT token

    Returns:
        User information from token or None if invalid
    """
    try:
        # Decode without verification (for extracting user info)
        payload = jwt.decode(token, options={"verify_signature": False})
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role"),
        }
    except Exception:
        return None


async def verify_supabase_token(token: str) -> Dict[str, Any]:
    """
    Verify Supabase JWT token using the auth service.

    Convenience function for token verification that creates
    a temporary auth service instance.

    Args:
        token: Supabase JWT token to verify

    Returns:
        User information from verified token

    Raises:
        AuthenticationError: If token is invalid or expired
    """
    auth_service = SupabaseAuthService()
    return await auth_service.verify_token(token)
