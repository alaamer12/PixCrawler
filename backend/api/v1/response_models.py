"""
Common response models and helpers for OpenAPI documentation.

This module provides reusable response schemas and helper functions for
consistent API documentation across all endpoints.

Functions:
    get_common_responses: Get common response schemas for specified status codes

Features:
    - Standardized error response schemas
    - Consistent OpenAPI documentation
    - Reusable response patterns
"""
from typing import Any, Dict

__all__ = ['get_common_responses']

# Common response schemas mapped by status code
_RESPONSE_MAP: Dict[int, Dict[str, Any]] = {
    400: {
        "description": "Bad Request - Invalid input data",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Invalid request parameters"
                }
            }
        }
    },
    401: {
        "description": "Unauthorized - Invalid or missing authentication token",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Not authenticated"
                }
            }
        }
    },
    403: {
        "description": "Forbidden - Insufficient permissions",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Not enough permissions"
                }
            }
        }
    },
    404: {
        "description": "Not Found - Resource does not exist",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Resource not found"
                }
            }
        }
    },
    409: {
        "description": "Conflict - Resource already exists or state conflict",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Resource already exists"
                }
            }
        }
    },
    422: {
        "description": "Unprocessable Entity - Validation error",
        "content": {
            "application/json": {
                "example": {
                    "detail": [
                        {
                            "loc": ["body", "field_name"],
                            "msg": "field required",
                            "type": "value_error.missing"
                        }
                    ]
                }
            }
        }
    },
    429: {
        "description": "Too Many Requests - Rate limit exceeded",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Rate limit exceeded"
                }
            }
        }
    },
    500: {
        "description": "Internal Server Error - Unexpected server error",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Internal server error"
                }
            }
        }
    },
    503: {
        "description": "Service Unavailable - Service temporarily unavailable",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Service temporarily unavailable"
                }
            }
        }
    }
}


def get_common_responses(*status_codes: int) -> Dict[int, Dict[str, Any]]:
    """
    Get common response schemas for specified status codes.

    This function is lightweight and doesn't need @lru_cache because:
    1. It only does dictionary lookups (O(1) operations)
    2. The response_map is a module-level constant
    3. The result is a small dict that's immediately used in decorator
    4. Caching would add overhead without meaningful performance gain

    Args:
        *status_codes: HTTP status codes to include (e.g., 401, 404, 500)

    Returns:
        Dictionary mapping status codes to response schemas

    Example:
        ```python
        @router.get(
            "/resource",
            responses={
                200: {"description": "Success"},
                **get_common_responses(401, 404, 500)
            }
        )
        async def get_resource():
            pass
        ```
    """
    return {
        code: _RESPONSE_MAP[code]
        for code in status_codes
        if code in _RESPONSE_MAP
    }
