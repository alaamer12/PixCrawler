"""
User management endpoints.

⚠️ IMPORTANT: Uses Supabase Auth (NO custom JWT) ⚠️

PixCrawler uses Supabase Auth exclusively (ADR-001). The backend does NOT
implement custom JWT generation.

Authentication Flow:
    1. User registers via POST /api/v1/users/ (public)
    2. User logs in via POST /api/v1/auth/login (public)
    3. Supabase returns JWT tokens
    4. User sends Bearer token in requests
    5. Backend verifies token using SupabaseAuthService

User Endpoints (This Module):
    - Register User: POST /api/v1/users/ (PUBLIC - no auth required)
    - List Users: GET /api/v1/users (admin only)
    - Get User: GET /api/v1/users/{user_id} (admin only)
    - Update User: PATCH /api/v1/users/{user_id} (admin only)
    - Delete User: DELETE /api/v1/users/{user_id} (admin only)

Authentication Endpoints (see auth.py):
    - Login: POST /api/v1/auth/login (PUBLIC)
    - Signup: POST /api/v1/auth/signup (PUBLIC)
    - Get Profile: GET /api/v1/auth/me (requires auth)
    - Verify Token: POST /api/v1/auth/verify-token (requires auth)

References:
    - ADR-001: Use Shared Supabase Database
    - backend/services/supabase_auth.py: Token verification
    - backend/api/v1/endpoints/auth.py: Auth endpoints
"""

from fastapi import APIRouter, HTTPException, status as http_status
from fastapi_pagination import Page

from backend.api.types import (
    UserID,
    UserServiceDep,
    CurrentUser,
    SupabaseAuthServiceDep,
)
from backend.api.v1.response_models import get_common_responses
from backend.schemas.user import UserCreate, UserResponse, UserUpdate

__all__ = ['router']

router = APIRouter(
    tags=["Users"],
    responses=get_common_responses(401, 403, 404, 500),
)


@router.post(
    "/",
    response_model=UserResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Register New User",
    description="Register a new user account via Supabase Auth. Public endpoint - no authentication required.",
    response_description="Newly created user account details",
    operation_id="registerUser",
    responses={
        201: {
            "description": "User registered successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "email": "newuser@example.com",
                        "full_name": "Jane Smith",
                        "is_active": True,
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z"
                    }
                }
            }
        },
        409: {
            "description": "Email already registered",
            "content": {
                "application/json": {
                    "example": {"detail": "Email already registered"}
                }
            }
        },
        **get_common_responses(422, 500)
    }
)
async def create_user(
    user_create: UserCreate,
    auth_service: SupabaseAuthServiceDep,
) -> UserResponse:
    """
    Register a new user account.

    **PUBLIC ENDPOINT**: No authentication required.

    Creates a new user via Supabase Auth and automatically creates
    a profile in the profiles table.

    **Usage:**
    ```bash
    curl -X POST http://localhost:8000/api/v1/users/ \\
      -H "Content-Type: application/json" \\
      -d '{
        "email": "user@example.com",
        "password": "SecurePass123!",
        "full_name": "John Doe"
      }'
    ```

    Args:
        user_create: User registration data (email, password, full_name)
        auth_service: Supabase authentication service

    Returns:
        Created user information (without password)

    Raises:
        HTTPException: 409 if email already registered
        HTTPException: 422 if validation fails
        HTTPException: 500 if registration fails
    """
    try:
        # Sign up using Supabase Auth (public signup)
        response = auth_service.supabase.auth.sign_up({
            "email": user_create.email,
            "password": user_create.password.get_secret_value(),
            "options": {
                "data": {
                    "full_name": user_create.full_name
                }
            }
        })

        if not response.user:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user account"
            )

        # Create profile in profiles table
        try:
            await auth_service.create_user_profile({
                "id": response.user.id,
                "email": user_create.email,
                "full_name": user_create.full_name,
            })
        except Exception as e:
            # Profile creation failed, but user was created in auth
            auth_service.logger.warning(f"Profile creation failed: {e}")

        # Log successful registration
        auth_service.log_operation(
            "user_registration",
            user_id=response.user.id
        )

        return UserResponse(
            id=response.user.id,
            email=user_create.email,
            full_name=user_create.full_name,
            is_active=True,  # New users are always active
            created_at=response.user.created_at,
            updated_at=response.user.updated_at or response.user.created_at
        )

    except HTTPException:
        raise
    except AttributeError as e:
        # Handle case where Supabase client is not properly initialized
        auth_service.logger.error(f"Supabase client error: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service not properly configured"
        )
    except Exception as e:
        auth_service.logger.error(f"Failed to register user: {str(e)}")
        # Check for duplicate email error
        error_msg = str(e).lower()
        if "already" in error_msg or "duplicate" in error_msg or "exists" in error_msg:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register user: {str(e)}"
        )


@router.get(
    "/",
    response_model=Page[UserResponse],
    summary="List Users (Admin)",
    description="Retrieve a paginated list of all users in the system.",
    response_description="Paginated user list",
    operation_id="listUsers",
    responses={
        200: {
            "description": "Successfully retrieved user list",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": "123e4567-e89b-12d3-a456-426614174000",
                                "email": "user1@example.com",
                                "full_name": "John Doe",
                                "is_active": True
                            }
                        ],
                        "total": 100,
                        "page": 1,
                        "size": 50,
                        "pages": 2
                    }
                }
            }
        },
        **get_common_responses(401, 403, 500)
    }
)
async def list_users(
    current_user: CurrentUser,
    user_service: UserServiceDep,
) -> Page[UserResponse]:
    """
    List all users with pagination.

    **ADMIN ONLY**: This endpoint requires admin privileges.

    Retrieve a paginated list of all users in the system.
    Supports filtering and sorting via query parameters.

    **Query Parameters:**
    - `page` (int): Page number (default: 1)
    - `size` (int): Items per page (default: 50, max: 100)

    **Authentication Required:** Admin privileges

    Args:
        current_user: Current authenticated user (must be admin)
        user_service: User service dependency

    Returns:
        Paginated list of users

    Raises:
        HTTPException: If not admin or query fails
    """
    # Check if current user is admin
    user_profile = current_user.get("profile", {})
    user_role = user_profile.get("role", "user")

    if user_role != "admin":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to list users"
        )

    try:
        # Delegate to service layer
        return await user_service.list_users()

    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}"
        )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get User by ID (Admin)",
    description="Retrieve detailed information about a specific user.",
    response_description="User account details",
    operation_id="getUserById",
    responses={
        200: {
            "description": "Successfully retrieved user",
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
        **get_common_responses(401, 403, 404, 500)
    }
)
async def get_user(
    user_id: UserID,
    current_user: CurrentUser,
    auth_service: SupabaseAuthServiceDep,
) -> UserResponse:
    """
    Get user by ID.

    **ADMIN ONLY**: This endpoint requires admin privileges.

    Retrieve detailed information about a specific user by their UUID.

    **Authentication Required:** Admin privileges

    Args:
        user_id: User UUID
        current_user: Current authenticated user (must be admin)
        auth_service: Supabase authentication service

    Returns:
        User information

    Raises:
        HTTPException: If user not found (404) or access denied (403)
    """
    # Check if current user is admin
    user_profile = current_user.get("profile", {})
    user_role = user_profile.get("role", "user")

    if user_role != "admin":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to view user details"
        )

    try:
        # Get user profile from database
        profile = await auth_service.get_user_profile(str(user_id))

        if not profile:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return UserResponse(
            id=profile["id"],
            email=profile["email"],
            full_name=profile.get("full_name", ""),
            is_active=True,
            created_at=profile["created_at"],
            updated_at=profile["updated_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        auth_service.logger.error(f"Failed to retrieve user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user: {str(e)}"
        )


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update User (Admin)",
    description="Update user profile information and settings.",
    response_description="Updated user account details",
    operation_id="updateUser",
    responses={
        200: {
            "description": "User updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "email": "user@example.com",
                        "full_name": "John Doe Updated",
                        "is_active": True,
                        "updated_at": "2024-01-02T00:00:00Z"
                    }
                }
            }
        },
        **get_common_responses(401, 403, 404, 422, 500)
    }
)
async def update_user(
    user_id: UserID,
    user_update: UserUpdate,
    current_user: CurrentUser,
    auth_service: SupabaseAuthServiceDep,
) -> UserResponse:
    """
    Update user information.

    **ADMIN ONLY**: This endpoint requires admin privileges.

    Update user profile fields such as name or status.
    Only provided fields will be updated (partial update).

    **Authentication Required:** Admin privileges

    Args:
        user_id: User UUID
        user_update: User update data (only provided fields will be updated)
        current_user: Current authenticated user (must be admin)
        auth_service: Supabase authentication service

    Returns:
        Updated user information

    Raises:
        HTTPException: If user not found (404), validation fails (422), or access denied (403)
    """
    # Check if current user is admin
    user_profile = current_user.get("profile", {})
    user_role = user_profile.get("role", "user")

    if user_role != "admin":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to update users"
        )

    try:
        # Build update data (only include provided fields)
        update_data = {}
        if user_update.full_name is not None:
            update_data["full_name"] = user_update.full_name
        if user_update.is_active is not None:
            update_data["is_active"] = user_update.is_active

        if not update_data:
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No fields to update"
            )

        # Update user profile
        updated_profile = await auth_service.update_user_profile(
            str(user_id),
            update_data
        )

        auth_service.log_operation(
            "update_user",
            user_id=current_user["user_id"],
            target_user_id=str(user_id)
        )

        return UserResponse(
            id=updated_profile["id"],
            email=updated_profile["email"],
            full_name=updated_profile.get("full_name", ""),
            is_active=updated_profile.get("is_active", True),
            created_at=updated_profile["created_at"],
            updated_at=updated_profile["updated_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        auth_service.logger.error(f"Failed to update user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete(
    "/{user_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    summary="Delete User (Admin)",
    description="Permanently delete a user account and all associated data using Supabase Admin API.",
    response_description="User deleted successfully (no content)",
    operation_id="deleteUser",
    responses={
        204: {
            "description": "User deleted successfully"
        },
        **get_common_responses(401, 403, 404, 500)
    }
)
async def delete_user(
    user_id: UserID,
    current_user: CurrentUser,
    auth_service: SupabaseAuthServiceDep,
) -> None:
    """
    Delete a user by UUID using Supabase Admin API.

    **ADMIN ONLY**: This endpoint requires admin privileges.

    Cascade Deletion (handled by database RLS policies):
    - User profile (profiles table)
    - Projects (projects table)
    - Crawl jobs (crawl_jobs table)
    - Images (images table)
    - Activity logs (activity_logs table)
    - API keys (api_keys table)
    - Notifications (notifications table)

    **Authentication Required:** Admin privileges

    Args:
        user_id: User UUID to delete
        current_user: Current authenticated user (must be admin)
        auth_service: Supabase authentication service

    Raises:
        HTTPException:
            - 401: Not authenticated
            - 403: Access denied (non-admin user)
            - 404: User not found
            - 500: Deletion failed
    """
    # Check if current user is admin
    user_profile = current_user.get("profile", {})
    user_role = user_profile.get("role", "user")
    
    if user_role != "admin":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to delete users"
        )
    
    # Prevent self-deletion
    if str(current_user["user_id"]) == str(user_id):
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    try:
        # Delete user using Supabase Admin API
        # This will cascade delete all related data via database policies
        await auth_service.supabase.auth.admin.delete_user(str(user_id))
        
        auth_service.log_operation(
            "delete_user",
            user_id=current_user["user_id"],
            target_user_id=str(user_id)
        )
        
    except Exception as e:
        auth_service.logger.error(f"Failed to delete user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )
