"""
API key management endpoints.

This module provides API endpoints for API key management,
including creation, listing, revocation, and usage tracking.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status

from api.dependencies import get_api_key_service
from backend.api.types import CurrentUser
from backend.api.v1.response_models import get_common_responses
from backend.core.exceptions import NotFoundError, ValidationError
from backend.schemas.api_keys import (
    APIKeyResponse,
    APIKeyCreateResponse,
    APIKeyListResponse,
    APIKeyStatus,
    APIKeyPermission,
)
from backend.services.api_keys import APIKeyService

__all__ = ['router']

router = APIRouter(
    tags=["API Keys"],
    responses=get_common_responses(401, 404, 500),
)


@router.get(
    "/",
    response_model=APIKeyListResponse,
    summary="List API Keys",
    description="Retrieve all API keys for the authenticated user with pagination and filtering.",
    response_description="Paginated list of API keys",
    operation_id="listAPIKeys",
    responses={
        200: {
            "description": "Successfully retrieved API keys",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {
                                "id": "123e4567-e89b-12d3-a456-426614174000",
                                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                                "name": "Production API Key",
                                "key_prefix": "pk_live_",
                                "permissions": ["read", "write"],
                                "rate_limit": 1000,
                                "status": "active",
                                "usage_count": 150,
                                "last_used_at": "2024-01-27T10:00:00Z",
                                "last_used_ip": "192.168.1.1",
                                "expires_at": None,
                                "created_at": "2024-01-20T10:00:00Z",
                                "updated_at": "2024-01-27T10:00:00Z",
                                "is_active": True,
                                "is_expired": False
                            }
                        ],
                        "meta": {
                            "total": 3,
                            "skip": 0,
                            "limit": 50
                        }
                    }
                }
            }
        },
        **get_common_responses(401, 500)
    }
)
async def list_api_keys(
    current_user: CurrentUser,
    service: APIKeyService = Depends(get_api_key_service),
    skip: int = Query(0, ge=0, description="Number of items to skip for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Maximum items to return (max: 100)"),
    status: Optional[APIKeyStatus] = Query(None, description="Filter by status"),
) -> APIKeyListResponse:
    """
    List all API keys for the current user.

    Returns a paginated list of API keys with their metadata,
    permissions, and usage statistics. The actual key values
    are never returned for security.

    **Query Parameters:**
    - `skip` (int): Pagination offset (default: 0)
    - `limit` (int): Items per page (default: 50, max: 100)
    - `status` (str): Filter by status (active, revoked, expired)

    **Authentication Required:** Bearer token

    Args:
        current_user: Current authenticated user (injected)
        service: API key service instance (injected)
        skip: Number of items to skip
        limit: Maximum items to return
        status: Status filter

    Returns:
        Paginated list of API keys

    Raises:
        HTTPException: 401 if authentication fails
        HTTPException: 500 if query fails
    """
    try:
        user_id = UUID(current_user["user_id"])
        keys, total = await service.list_keys(
            user_id=user_id,
            skip=skip,
            limit=limit,
            status=status,
        )

        # Transform to response model
        data = [APIKeyResponse.model_validate(k) for k in keys]

        return APIKeyListResponse(
            data=data,
            meta={"total": total, "skip": skip, "limit": limit}
        )

    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve API keys: {str(e)}"
        )


@router.post(
    "/",
    response_model=APIKeyCreateResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Create API Key",
    description="Create a new API key for programmatic access with specified permissions and rate limits.",
    response_description="Created API key with full key value (shown only once)",
    operation_id="createAPIKey",
    responses={
        201: {
            "description": "API key created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "user_id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Production API Key",
                        "key": "pk_live_1234567890abcdef",
                        "key_prefix": "pk_live_",
                        "permissions": ["read", "write"],
                        "rate_limit": 1000,
                        "status": "active",
                        "usage_count": 0,
                        "last_used_at": None,
                        "last_used_ip": None,
                        "expires_at": None,
                        "created_at": "2024-01-27T10:00:00Z",
                        "updated_at": "2024-01-27T10:00:00Z"
                    }
                }
            }
        },
        **get_common_responses(401, 422, 500)
    }
)
async def create_api_key(
    current_user: CurrentUser,
    service: APIKeyService = Depends(get_api_key_service),
    name: str = Query(..., min_length=1, max_length=200, description="Key name"),
    permissions: list[APIKeyPermission] = Query(..., description="List of permissions"),
    rate_limit: int = Query(1000, gt=0, le=100000, description="Requests per hour limit"),
) -> APIKeyCreateResponse:
    """
    Create a new API key for the current user.

    Generates a secure API key with specified permissions and rate limits.
    The full key value is returned only once during creation and should
    be stored securely by the client.

    **Important:** Save the key immediately. It cannot be retrieved later.

    **Query Parameters:**
    - `name` (str): User-friendly key name (1-200 chars)
    - `permissions` (list): List of permissions (e.g., ["read", "write"])
    - `rate_limit` (int): Requests per hour (default: 1000, max: 100000)

    **Authentication Required:** Bearer token

    Args:
        current_user: Current authenticated user (injected)
        service: API key service instance (injected)
        name: Key name
        permissions: List of permissions
        rate_limit: Requests per hour limit

    Returns:
        Created API key with full key value

    Raises:
        HTTPException: 401 if authentication fails
        HTTPException: 422 if validation fails
        HTTPException: 500 if creation fails
    """
    try:
        user_id = UUID(current_user["user_id"])

        # Create key
        api_key, full_key = await service.create_key(
            user_id=user_id,
            name=name,
            permissions=permissions,
            rate_limit=rate_limit,
        )

        # Build response with full key
        response_data = APIKeyResponse.model_validate(api_key)

        return APIKeyCreateResponse(
            **response_data.model_dump(),
            key=full_key,
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}"
        )


@router.delete(
    "/{key_id}",
    status_code=http_status.HTTP_200_OK,
    summary="Revoke API Key",
    description="Revoke an API key to permanently disable it. This action cannot be undone.",
    response_description="Revocation confirmation",
    operation_id="revokeAPIKey",
    responses={
        200: {
            "description": "API key revoked successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "API key revoked successfully",
                        "key_id": "123e4567-e89b-12d3-a456-426614174000"
                    }
                }
            }
        },
        **get_common_responses(401, 404, 500)
    }
)
async def revoke_api_key(
    key_id: UUID,
    current_user: CurrentUser,
    service: APIKeyService = Depends(get_api_key_service),
) -> dict:
    """
    Revoke an API key.

    Permanently disables the API key. Revoked keys cannot be reactivated.
    Any requests using the revoked key will be rejected.

    **Warning:** This action cannot be undone.

    **Authentication Required:** Bearer token

    Args:
        key_id: API key ID to revoke
        current_user: Current authenticated user (injected)
        service: API key service instance (injected)

    Returns:
        Revocation confirmation message

    Raises:
        HTTPException: 401 if authentication fails
        HTTPException: 404 if key not found or access denied
        HTTPException: 500 if revocation fails
    """
    try:
        user_id = UUID(current_user["user_id"])

        # Revoke key
        await service.revoke_key(key_id, user_id)

        return {
            "message": "API key revoked successfully",
            "key_id": str(key_id),
        }

    except NotFoundError:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke API key: {str(e)}"
        )


@router.get(
    "/{key_id}/usage",
    response_model=dict,
    summary="Get API Key Usage",
    description="Retrieve usage statistics for a specific API key.",
    response_description="Usage statistics and metrics",
    operation_id="getAPIKeyUsage",
    responses={
        200: {
            "description": "Successfully retrieved usage statistics",
            "content": {
                "application/json": {
                    "example": {
                        "key_id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Production API Key",
                        "total_usage": 1500,
                        "rate_limit": 1000,
                        "last_used_at": "2024-01-27T10:00:00Z",
                        "last_used_ip": "192.168.1.1",
                        "average_daily_usage": 50.0,
                        "status": "active",
                        "created_at": "2024-01-20T10:00:00Z"
                    }
                }
            }
        },
        **get_common_responses(401, 404, 500)
    }
)
async def get_api_key_usage(
    key_id: UUID,
    current_user: CurrentUser,
    service: APIKeyService = Depends(get_api_key_service),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze (1-365)"),
) -> dict:
    """
    Get usage statistics for an API key.

    Returns detailed usage metrics including:
    - Total usage count
    - Rate limit
    - Last usage timestamp and IP
    - Average daily usage
    - Current status

    **Query Parameters:**
    - `days` (int): Analysis period in days (default: 30, max: 365)

    **Authentication Required:** Bearer token

    Args:
        key_id: API key ID
        current_user: Current authenticated user (injected)
        service: API key service instance (injected)
        days: Number of days to analyze

    Returns:
        Usage statistics dictionary

    Raises:
        HTTPException: 401 if authentication fails
        HTTPException: 404 if key not found or access denied
        HTTPException: 500 if query fails
    """
    try:
        user_id = UUID(current_user["user_id"])
        usage = await service.get_key_usage(key_id, user_id, days)
        return usage

    except NotFoundError:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve usage statistics: {str(e)}"
        )
