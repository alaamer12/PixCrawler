"""Authentication and authorization endpoints.

This module provides authentication functionality for the PixCrawler API.
It handles user registration, login, and role-based access control.

Roles:
    - admin: Full access to all resources
    - user: Limited access to own resources

Note:
    This is a demo implementation with hardcoded credentials and fake tokens.
    In production, use proper password hashing (bcrypt) and JWT tokens.

Test Accounts:
    - Admin: username="admin", password="adminpass"
    - User1: username="user1", password="userpass"
    - User2: username="user2", password="userpass"
"""

import secrets
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

# Router with prefix
router = APIRouter(prefix="/auth", tags=["Authentication"])


# Pydantic models
class AuthUser(BaseModel):
    """Authentication user model.
    
    Used for both registration and login requests.
    
    Attributes:
        username: Unique username (3-50 characters)
        password: User password (minimum 6 characters)
    
    Note:
        In production, password should be validated with stronger requirements
        (uppercase, lowercase, numbers, special characters).
    """

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Unique username for the user",
        example="admin",
    )
    password: str = Field(
        ...,
        min_length=6,
        description="User password (minimum 6 characters)",
        example="secret123",
    )

    class Config:
        json_schema_extra = {
            "example": {"username": "admin", "password": "adminpass"}
        }


class UserResponse(BaseModel):
    """User response model after successful authentication.
    
    Returned after successful login with authentication token.
    
    Attributes:
        id: User's unique identifier
        username: User's username
        role: User's role (admin or user)
        token: Authentication token for subsequent requests
    
    Note:
        In production, use JWT tokens with expiration times.
    """

    id: int = Field(..., description="User's unique identifier", example=1)
    username: str = Field(..., description="User's username", example="admin")
    role: str = Field(
        ...,
        description="User's role (admin or user)",
        example="admin",
    )
    token: str = Field(
        ...,
        description="Authentication token for API requests",
        example="fake_token_abc123",
    )


class RegisterResponse(BaseModel):
    """Response model for successful user registration.
    
    Attributes:
        id: New user's unique identifier
        username: Registered username
        role: Assigned role (defaults to 'user')
        message: Confirmation message
    """

    id: int = Field(
        ...,
        description="New user's unique identifier",
        example=1,
    )
    username: str = Field(
        ...,
        description="Registered username",
        example="john_doe",
    )
    role: str = Field(
        ...,
        description="Assigned role (new users get 'user' role by default)",
        example="user",
    )
    message: str = Field(
        ...,
        description="Confirmation message",
        example="User registered successfully",
    )


# Fake user database with roles
fake_auth_users_db = [
    {"id": 1, "username": "admin", "password": "adminpass", "role": "admin"},
    {"id": 2, "username": "user1", "password": "userpass", "role": "user"},
    {"id": 3, "username": "user2", "password": "userpass", "role": "user"},
]


def generate_fake_token() -> str:
    """Generate a fake authentication token.
    
    Returns:
        A URL-safe fake token string.
    
    Note:
        In production, use JWT (JSON Web Tokens) with proper
        expiration times and signature verification.
    """
    return f"fake_token_{secrets.token_urlsafe(16)}"


def get_user_by_username(username: str) -> Optional[dict]:
    """Find user by username in fake database.
    
    Args:
        username: The username to search for.
    
    Returns:
        User dictionary if found, None otherwise.
    """
    for user in fake_auth_users_db:
        if user["username"] == username:
            return user
    return None


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with the provided credentials. New users are assigned the 'user' role by default.",
    responses={
        201: {
            "description": "User successfully registered",
            "content": {
                "application/json": {
                    "example": {
                        "id": 4,
                        "username": "newuser",
                        "role": "user",
                        "message": "User registered successfully",
                    }
                }
            },
        },
        409: {
            "description": "Username already exists",
            "content": {
                "application/json": {
                    "example": {"detail": "Username 'newuser' already exists"}
                }
            },
        },
    },
)
async def register(user: AuthUser):
    """
    Register a new user account.

    Creates a new user with the provided credentials. All new users are
    automatically assigned the 'user' role. Usernames must be unique.

    Args:
        user: User credentials containing username and password.

    Returns:
        Registration confirmation with user details and assigned role.

    Raises:
        HTTPException: 409 Conflict if username already exists.

    Example:
        Request:
            POST /auth/register
            {
                "username": "johndoe",
                "password": "secure123"
            }

        Response (201):
            {
                "id": 4,
                "username": "johndoe",
                "role": "user",
                "message": "User registered successfully"
            }
    """
    # Check if username already exists
    if get_user_by_username(user.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{user.username}' already exists",
        )

    # Generate new ID
    new_id = (
        max(u["id"] for u in fake_auth_users_db) + 1 if fake_auth_users_db else 1
    )

    # Create new user with default 'user' role
    new_user = {
        "id": new_id,
        "username": user.username,
        "password": user.password,  # In production, hash this!
        "role": "user",  # Default role for new users
    }

    # Add to fake database
    fake_auth_users_db.append(new_user)

    return RegisterResponse(
        id=new_id,
        username=user.username,
        role="user",
        message="User registered successfully",
    )


@router.post(
    "/login",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Login user",
    description="Authenticate user and return access token with user details and role.",
    responses={
        200: {
            "description": "Login successful",
            "content": {
                "application/json": {
                    "examples": {
                        "admin_login": {
                            "summary": "Admin login",
                            "value": {
                                "id": 1,
                                "username": "admin",
                                "role": "admin",
                                "token": "fake_token_abc123xyz",
                            },
                        },
                        "user_login": {
                            "summary": "Regular user login",
                            "value": {
                                "id": 2,
                                "username": "user1",
                                "role": "user",
                                "token": "fake_token_def456uvw",
                            },
                        },
                    }
                }
            },
        },
        401: {
            "description": "Invalid credentials",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid username or password"}
                }
            },
        },
    },
)
async def login(user: AuthUser):
    """
    Authenticate user and return access token.

    Validates user credentials and returns an authentication token along with
    user details and role. The token should be included in subsequent API
    requests for authentication.

    Args:
        user: User credentials containing username and password.

    Returns:
        User details with authentication token and role information.

    Raises:
        HTTPException: 401 Unauthorized if credentials are invalid.

    Example:
        Request:
            POST /auth/login
            {
                "username": "admin",
                "password": "adminpass"
            }

        Response (200):
            {
                "id": 1,
                "username": "admin",
                "role": "admin",
                "token": "fake_token_abc123xyz"
            }

    Test Accounts:
        - Admin: username="admin", password="adminpass"
        - User1: username="user1", password="userpass"
        - User2: username="user2", password="userpass"
    """
    # Find user by username
    db_user = get_user_by_username(user.username)

    # Check if user exists and password matches
    if not db_user or db_user["password"] != user.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate fake token
    token = generate_fake_token()

    return UserResponse(
        id=db_user["id"],
        username=db_user["username"],
        role=db_user["role"],
        token=token,
    )
