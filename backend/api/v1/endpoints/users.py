"""
User management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_pagination import Page

from backend.api.types import UserID, UserServiceDep
from backend.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_create: UserCreate,
    user_service: UserServiceDep,
) -> UserResponse:
    """
    Create a new user account.

    Args:
        user_create: User creation data
        user_service: User service dependency

    Returns:
        Created user information

    Raises:
        HTTPException: If user creation fails
    """
    # TODO: Implement user creation logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="User creation not implemented yet"
    )


@router.get("/", response_model=Page[UserResponse])
async def list_users(
    user_service: UserServiceDep,
) -> Page[UserResponse]:
    """
    List users with pagination.

    Pagination is handled automatically by fastapi-pagination.
    Query parameters: page (default=1), size (default=50)

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


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UserID,
    user_service: UserServiceDep,
) -> UserResponse:
    """
    Get user by ID.

    Args:
        user_id: User ID
        user_service: User service dependency

    Returns:
        User information

    Raises:
        HTTPException: If user not found
    """
    # TODO: Implement user retrieval logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="User retrieval not implemented yet"
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UserID,
    user_update: UserUpdate,
    user_service: UserServiceDep,
) -> UserResponse:
    """
    Update user information.

    Args:
        user_id: User ID
        user_update: User update data
        user_service: User service dependency

    Returns:
        Updated user information

    Raises:
        HTTPException: If user not found or update fails
    """
    # TODO: Implement user update logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="User update not implemented yet"
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UserID,
    user_service: UserServiceDep,
) -> None:
    """
    Delete user account.

    Args:
        user_id: User ID
        user_service: User service dependency

    Raises:
        HTTPException: If user not found or deletion fails
    """
    # TODO: Implement user deletion logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="User deletion not implemented yet"
    )
