"""
Response helper functions for consistent API responses.

This module provides utility functions for building consistent API responses
across all endpoints, following professional FastAPI patterns.

Functions:
    success_response: Build successful response with data
    error_response: Build error response with details
    paginated_response: Build paginated response
    created_response: Build 201 Created response
    no_content_response: Build 204 No Content response

Best Practices:
    - Use these helpers instead of manually constructing responses
    - Ensures consistent response format across all endpoints
    - Simplifies error handling and status code management
    - Improves API documentation and client integration
"""

from typing import Any, Dict, List, Optional

from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

__all__ = [
    'success_response',
    'error_response',
    'created_response',
    'no_content_response',
    'paginated_response',
]


def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = status.HTTP_200_OK,
    **kwargs
) -> JSONResponse:
    """
    Build successful response with optional data.

    Args:
        data: Response data (dict, list, model, etc.)
        message: Success message
        status_code: HTTP status code (default: 200)
        **kwargs: Additional fields to include in response

    Returns:
        JSONResponse with success format

    Example:
        >>> success_response(
        ...     data={"user_id": 123, "name": "John"},
        ...     message="User retrieved successfully"
        ... )
        JSONResponse({"message": "User retrieved successfully", "data": {...}})
    """
    content = {
        "message": message,
        "data": data,
        **kwargs
    }
    return JSONResponse(
        content=jsonable_encoder(content),
        status_code=status_code
    )


def created_response(
    data: Any,
    message: str = "Resource created successfully",
    location: Optional[str] = None,
    **kwargs
) -> JSONResponse:
    """
    Build 201 Created response for resource creation.

    Args:
        data: Created resource data
        message: Success message
        location: Optional Location header value (resource URL)
        **kwargs: Additional fields to include in response

    Returns:
        JSONResponse with 201 status code

    Example:
        >>> created_response(
        ...     data={"id": 123, "name": "New Project"},
        ...     message="Project created successfully",
        ...     location="/api/v1/projects/123"
        ... )
    """
    response = success_response(
        data=data,
        message=message,
        status_code=status.HTTP_201_CREATED,
        **kwargs
    )
    
    if location:
        response.headers["Location"] = location
    
    return response


def no_content_response() -> JSONResponse:
    """
    Build 204 No Content response for successful operations with no data.

    Returns:
        JSONResponse with 204 status code and no content

    Example:
        >>> no_content_response()
        JSONResponse(status_code=204)
    """
    return JSONResponse(
        content=None,
        status_code=status.HTTP_204_NO_CONTENT
    )


def error_response(
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    details: Optional[List[Dict[str, Any]]] = None,
    error_code: Optional[str] = None,
    **kwargs
) -> JSONResponse:
    """
    Build error response with details.

    Args:
        message: Error message
        status_code: HTTP status code (default: 400)
        details: Optional list of error details
        error_code: Optional error code for client handling
        **kwargs: Additional fields to include in response

    Returns:
        JSONResponse with error format

    Example:
        >>> error_response(
        ...     message="Validation failed",
        ...     status_code=422,
        ...     details=[
        ...         {"field": "email", "message": "Invalid email format"}
        ...     ],
        ...     error_code="VALIDATION_ERROR"
        ... )
    """
    content = {
        "message": message,
        "details": details or [],
        **kwargs
    }
    
    if error_code:
        content["error_code"] = error_code
    
    return JSONResponse(
        content=jsonable_encoder(content),
        status_code=status_code
    )


def paginated_response(
    items: List[Any],
    total: int,
    page: int,
    size: int,
    message: str = "Success",
    **kwargs
) -> JSONResponse:
    """
    Build paginated response.

    Note: This is for manual pagination. For automatic pagination,
    use fastapi-pagination's Page[T] response model instead.

    Args:
        items: List of items for current page
        total: Total number of items
        page: Current page number
        size: Items per page
        message: Success message
        **kwargs: Additional fields to include in response

    Returns:
        JSONResponse with pagination metadata

    Example:
        >>> paginated_response(
        ...     items=[{"id": 1}, {"id": 2}],
        ...     total=100,
        ...     page=1,
        ...     size=20
        ... )
        JSONResponse({
            "message": "Success",
            "data": {"items": [...], "total": 100, "page": 1, "size": 20, "pages": 5}
        })
    """
    pages = (total + size - 1) // size  # Ceiling division
    
    content = {
        "message": message,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
            "pages": pages
        },
        **kwargs
    }
    
    return JSONResponse(
        content=jsonable_encoder(content),
        status_code=status.HTTP_200_OK
    )
