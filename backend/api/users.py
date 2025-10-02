"""User management endpoints."""

from typing import List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

# Router with prefix
router = APIRouter(prefix="/users", tags=["Users"])


# Pydantic models
class User(BaseModel):
    """User model."""

    id: int = Field(..., example=1)
    username: str = Field(..., min_length=3, max_length=50, example="john_doe")
    email: str = Field(..., example="john@example.com")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "john_doe",
                "email": "john@example.com",
            }
        }


class UserCreate(BaseModel):
    """User creation model."""

    username: str = Field(..., min_length=3, max_length=50, example="john_doe")
    email: str = Field(..., example="john@example.com")


# Fake database
fake_users_db = [
    User(id=1, username="alice", email="alice@example.com"),
    User(id=2, username="bob", email="bob@example.com"),
    User(id=3, username="charlie", email="charlie@example.com"),
]


@router.get("", response_model=List[User], status_code=status.HTTP_200_OK)
async def get_users():
    """
    Retrieve all users.

    Returns a list of all users in the system.
    """
    return fake_users_db


@router.get("/{user_id}", response_model=User, status_code=status.HTTP_200_OK)
async def get_user(user_id: int):
    """
    Retrieve a specific user by ID.

    Args:
        user_id: The ID of the user to retrieve

    Returns:
        User details

    Raises:
        HTTPException: 404 if user not found
    """
    for user in fake_users_db:
        if user.id == user_id:
            return user

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"User with id {user_id} not found",
    )


@router.post("", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    """
    Create a new user.

    Args:
        user: User data for creation

    Returns:
        Created user with generated ID
    """
    # Generate new ID
    new_id = max(u.id for u in fake_users_db) + 1 if fake_users_db else 1

    # Create new user
    new_user = User(id=new_id, username=user.username, email=user.email)

    # Add to fake database
    fake_users_db.append(new_user)

    return new_user
