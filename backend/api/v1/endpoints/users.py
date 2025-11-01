"""User management endpoints."""

from fastapi import APIRouter, HTTPException, status
from fastapi_pagination import Page

from backend.api.types import UserID, UserServiceDep
from backend.api.v1.response_models import get_common_responses
from backend.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(
    tags=["Users"],
    responses=get_common_responses(401, 403, 404, 500),
)


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create User Account",
    description="Create a new user account with email and profile information.",
    response_description="Newly created user account details",
    operation_id="createUser",
    responses={
        201: {
            "description": "User created successfully",
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
        **get_common_responses(401, 422, 500)
    }
)
async def create_user(
    user_create: UserCreate,
    user_service: UserServiceDep,
) -> UserResponse:
    """
    Create a new user account.

    **Note:** In production, users are typically created via Supabase Auth.
    This endpoint is for administrative purposes or special use cases.

    **Authentication Required:** Admin privileges

    Args:
        user_create: User creation data
        user_service: User service dependency

    Returns:
        Created user information

    Raises:
        HTTPException: If user creation fails or email already exists
    """
    # TODO: Implement user creation logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="User creation not implemented yet"
    )


@router.get(
    "/",
    response_model=Page[UserResponse],
    summary="List Users",
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
    user_service: UserServiceDep,
) -> Page[UserResponse]:
    """
    List users with pagination.

    Retrieve a paginated list of all users. Supports filtering and sorting
    via query parameters.

    **Query Parameters:**
    - `page` (int): Page number (default: 1)
    - `size` (int): Items per page (default: 50, max: 100)

    **Authentication Required:** Admin privileges

    Args:
        user_service: User service dependency

    Returns:
        Paginated list of users
    """
    # TODO: Implement user listing logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="User listing not implemented yet"
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get User by ID",
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
    user_service: UserServiceDep,
) -> UserResponse:
    """
    Get user by ID.

    Retrieve detailed information about a specific user by their UUID.

    **Authentication Required:** Admin privileges or own user ID

    Args:
        user_id: User UUID (must be >= 1)
        user_service: User service dependency

    Returns:
        User information

    Raises:
        HTTPException: If user not found (404) or access denied (403)
    """
    # TODO: Implement user retrieval logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="User retrieval not implemented yet"
    )


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update User",
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
    user_service: UserServiceDep,
) -> UserResponse:
    """
    Update user information.

    Update user profile fields such as name, email, or status.
    Only provided fields will be updated (partial update).

    **Authentication Required:** Admin privileges or own user ID

    Args:
        user_id: User UUID
        user_update: User update data (only provided fields will be updated)
        user_service: User service dependency

    Returns:
        Updated user information

    Raises:
        HTTPException: If user not found (404), validation fails (422), or access denied (403)
    """
    # TODO: Implement user update logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="User update not implemented yet"
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete User",
    description="Permanently delete a user account and all associated data.",
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
    user_service: UserServiceDep,
) -> None:
    """
    Delete user account.

    **Warning:** This action is permanent and will delete all user data
    including projects, crawl jobs, and images.

    **Authentication Required:** Admin privileges

    Args:
        user_id: User UUID
        user_service: User service dependency

    Raises:
        HTTPException: If user not found (404), access denied (403), or deletion fails (500)
    """
    # TODO: Implement user deletion logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="User deletion not implemented yet"
    )
