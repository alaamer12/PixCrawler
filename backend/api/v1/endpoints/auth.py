"""
Authentication endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer

from backend.models.user import TokenRefresh, TokenResponse, UserLogin
from backend.services.auth import AuthService

router = APIRouter()
security = HTTPBearer()


@router.post("/login", response_model=TokenResponse)
async def login(
    user_login: UserLogin,
    auth_service: AuthService = Depends(),
) -> TokenResponse:
    """
    Authenticate user and return access tokens.

    Args:
        user_login: User login credentials
        auth_service: Authentication service dependency

    Returns:
        JWT tokens for authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    # TODO: Implement authentication logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication not implemented yet"
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_refresh: TokenRefresh,
    auth_service: AuthService = Depends(),
) -> TokenResponse:
    """
    Refresh access token using refresh token.

    Args:
        token_refresh: Refresh token request
        auth_service: Authentication service dependency

    Returns:
        New JWT tokens

    Raises:
        HTTPException: If refresh token is invalid
    """
    # TODO: Implement token refresh logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Token refresh not implemented yet"
    )


@router.post("/logout")
async def logout(
    token: str = Depends(security),
    auth_service: AuthService = Depends(),
) -> dict[str, str]:
    """
    Logout user and invalidate tokens.

    Args:
        token: Bearer token from Authorization header
        auth_service: Authentication service dependency

    Returns:
        Success message
    """
    # TODO: Implement logout logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Logout not implemented yet"
    )
