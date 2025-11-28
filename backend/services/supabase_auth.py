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

from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

import jwt
from supabase import create_client, Client

from backend.core.config import get_settings
from backend.core.exceptions import AuthenticationError, NotFoundError, RateLimitExceeded
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
        
    def _get_tier_limits(self, tier: str) -> Dict[str, Any]:
        """
        Get the limits for a specific user tier.

        Args:
            tier: User tier (FREE, PRO, ENTERPRISE)

        Returns:
            Dictionary containing the limits for the tier
        """
        tier = tier.upper()
        
        # Define limits for each tier
        limits = {
            'FREE': {
                'max_concurrent_jobs': 1,
                'max_images_per_job': 100,
                'max_jobs_per_day': 3,
                'max_projects': 3,
                'max_team_members': 1
            },
            'PRO': {
                'max_concurrent_jobs': 3,
                'max_images_per_job': 1000,
                'max_jobs_per_day': 20,
                'max_projects': 10,
                'max_team_members': 5
            },
            'ENTERPRISE': {
                'max_concurrent_jobs': 10,
                'max_images_per_job': 10000,
                'max_jobs_per_day': 1000,
                'max_projects': 100,
                'max_team_members': 50
            }
        }
        
        # Default to FREE tier if tier is not found
        return limits.get(tier, limits['FREE'])

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

    async def get_user_tier(self, user_id: str) -> str:
        """
        Get user's subscription tier from the profiles table.

        Args:
            user_id: User ID to get tier for

        Returns:
            User's tier (FREE, PRO, ENTERPRISE)

        Raises:
            NotFoundError: If user profile is not found
        """
        try:
            response = self.supabase.table("profiles").select("user_tier").eq("id", user_id).execute()
            
            if not response.data:
                raise NotFoundError(f"User profile not found for ID: {user_id}")
                
            return response.data[0].get("user_tier", "FREE").upper()
            
        except Exception as e:
            self.logger.error(f"Failed to get user tier: {str(e)}")
            raise

    async def get_user_usage_metrics(self, user_id: str) -> Dict[str, int]:
        """
        Get current usage metrics for the user.

        Args:
            user_id: Supabase user ID

        Returns:
            Dictionary containing current usage metrics
        """
        try:
            # Get current date in UTC
            today = datetime.utcnow().date()
            
            # Get concurrent jobs
            concurrent_jobs = (
                self.supabase.table("crawl_jobs")
                .select("id", count="exact")
                .eq("user_id", user_id)
                .in_("status", ["pending", "in_progress"])
                .execute()
            ).count or 0
            
            # Get today's jobs
            today_jobs = (
                self.supabase.table("crawl_jobs")
                .select("id", count="exact")
                .eq("user_id", user_id)
                .gte("created_at", f"{today.isoformat()}T00:00:00")
                .execute()
            ).count or 0
            
            # Get total projects
            total_projects = (
                self.supabase.table("projects")
                .select("id", count="exact")
                .eq("owner_id", user_id)
                .execute()
            ).count or 0
            
            # Get team members (if applicable)
            total_team_members = 0
            team_response = (
                self.supabase.table("teams")
                .select("id")
                .eq("owner_id", user_id)
                .execute()
            )
            
            if team_response.data:
                team_id = team_response.data[0].get("id")
                if team_id:
                    total_team_members = (
                        self.supabase.table("team_members")
                        .select("id", count="exact")
                        .eq("team_id", team_id)
                        .execute()
                    ).count or 0
            
            return {
                "concurrent_jobs": concurrent_jobs,
                "jobs_today": today_jobs,
                "total_projects": total_projects,
                "team_members": total_team_members
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get user metrics: {str(e)}")
            return {}

    async def is_new_user(self, user_id: str) -> bool:
        """
        Check if user is new by verifying they have no job history.

        Args:
            user_id: Supabase user ID

        Returns:
            True if user has no completed jobs, False otherwise
        """
        try:
            response = (
                self.supabase.table("crawl_jobs")
                .select("id", count="exact")
                .eq("user_id", user_id)
                .eq("status", "completed")
                .execute()
            )
            return response.count == 0
            
        except Exception as e:
            self.logger.error(f"Failed to check if user is new: {str(e)}")
            return True

    async def get_user_tier_info(self, user_id: str) -> Tuple[str, Dict[str, Any], Dict[str, int]]:
        """
        Get user's tier information including limits and current usage.

        Args:
            user_id: Supabase user ID

        Returns:
            Tuple of (tier_name, tier_limits, current_usage)
        """
        tier = await self.get_user_tier(user_id)
        limits = self._get_tier_limits(tier)
        usage = await self.get_user_usage_metrics(user_id)
        return tier, limits, usage

    async def detect_user_tier(self, user_id: str) -> str:
        """
        Detect and return user's tier based on their profile and job history.

        Args:
            user_id: Supabase user ID

        Returns:
            str: User's tier (FREE, PRO, ENTERPRISE)
        """
        try:
            # Get user profile to check for existing tier
            profile = await self.get_user_profile(user_id)
            
            # If user has a tier set, return it
            if profile and profile.get('user_tier'):
                return profile['user_tier'].upper()
                
            # Check if this is a new user (no completed jobs)
            is_new_user = await self.is_new_user(user_id)
            
            # Default to FREE tier for new users
            if is_new_user:
                # Update profile with default tier
                await self.update_user_profile(user_id, {"user_tier": "FREE"})
                return "FREE"
                
            # For existing users without a tier, default to FREE
            await self.update_user_profile(user_id, {"user_tier": "FREE"})
            return "FREE"
            
        except Exception as e:
            self.logger.error(f"Failed to detect user tier: {str(e)}")
            return "FREE"
            
    async def get_user_limits(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's tier limits based on their current tier.

        Args:
            user_id: Supabase user ID

        Returns:
            Dict containing the user's tier limits
        """
        tier = await self.detect_user_tier(user_id)
        return self._get_tier_limits(tier)
        
    async def check_limit(self, user_id: str, limit_type: str, value: int = 1) -> bool:
        """
        Check if a specific limit would be exceeded for the user.

        Args:
            user_id: Supabase user ID
            limit_type: One of ['concurrent_jobs', 'jobs_today', 'total_projects', 'team_members']
            value: Value to check against the limit (default: 1)

        Returns:
            bool: True if within limit, False otherwise
        """
        try:
            # Get current usage and tier limits
            usage = await self.get_user_usage_metrics(user_id)
            limits = await self.get_user_limits(user_id)

            # Map usage keys to their corresponding limit keys in the limits dict
            limit_key_map = {
                "concurrent_jobs": "max_concurrent_jobs",
                "jobs_today": "max_jobs_per_day",
                "total_projects": "max_projects",
                "team_members": "max_team_members"
            }

            if limit_type not in limit_key_map:
                self.logger.warning(f"Invalid limit type: {limit_type}")
                return False

            limit_key = limit_key_map[limit_type]

            # Current usage value (fall back to 0)
            current_usage = usage.get(limit_type, 0)

            # Compare (current + value) to the limit
            limit_value = limits.get(limit_key)
            if limit_value is None:
                self.logger.warning(f"Limit key {limit_key} not found for user {user_id}")
                return False

            return (current_usage + value) <= limit_value

        except Exception as e:
            self.logger.error(f"Failed to check limit: {str(e)}")
            return False


    async def validate_request(self, user_id: str, request_type: str, **kwargs) -> bool:
        """
        Validate if user's request is allowed based on their tier.

        Args:
            user_id: Supabase user ID
            request_type: Type of request to validate ('crawl_job', 'create_project', 'add_team_member')
            **kwargs: Additional parameters for specific validations

        Returns:
            bool: True if request is allowed, False otherwise

        Raises:
            RateLimitExceeded: If user has exceeded their tier limits
        """
        try:
            # Get user tier, limits, and current usage
            tier = await self.detect_user_tier(user_id)
            limits = await self.get_user_limits(user_id)
            usage = await self.get_user_usage_metrics(user_id)
            
            if request_type == 'crawl_job':
                # Check concurrent jobs limit
                if not await self.check_limit(user_id, 'concurrent_jobs'):
                    raise RateLimitExceeded(
                        tier=tier,
                        current_usage=usage['concurrent_jobs'],
                        limit=limits['max_concurrent_jobs'],
                        message=f"Maximum concurrent jobs limit ({limits['max_concurrent_jobs']}) reached for {tier} tier"
                    )
                
                # Check daily job limit
                if not await self.check_limit(user_id, 'jobs_today'):
                    raise RateLimitExceeded(
                        tier=tier,
                        current_usage=usage['jobs_today'],
                        limit=limits['max_jobs_per_day'],
                        message=f"Daily job limit ({limits['max_jobs_per_day']}) reached for {tier} tier"
                    )
                
                # Check images per job limit if provided
                if 'image_count' in kwargs and kwargs['image_count'] > limits['max_images_per_job']:
                    raise RateLimitExceeded(
                        tier=tier,
                        current_usage=kwargs['image_count'],
                        limit=limits['max_images_per_job'],
                        message=f"Maximum images per job ({limits['max_images_per_job']}) exceeded for {tier} tier"
                    )
            
            elif request_type == 'create_project':
                if usage['total_projects'] >= limits['max_projects']:
                    raise RateLimitExceeded(
                        tier=tier,
                        current_usage=usage['total_projects'],
                        limit=limits['max_projects'],
                        message=f"Maximum projects limit ({limits['max_projects']}) reached for {tier} tier"
                    )
            
            elif request_type == 'add_team_member':
                if usage['team_members'] >= limits['max_team_members']:
                    raise RateLimitExceeded(
                        tier=tier,
                        current_usage=usage['team_members'],
                        limit=limits['max_team_members'],
                        message=f"Maximum team members limit ({limits['max_team_members']}) reached for {tier} tier"
                    )
            
            return True
            
        except RateLimitExceeded:
            raise
        except Exception as e:
            self.logger.error(f"Request validation failed: {str(e)}")
            # Default to allowing the request on error (fail-open for availability)
            return True


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