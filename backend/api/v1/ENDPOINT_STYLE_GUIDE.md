# Backend API Endpoint Style Guide

This guide defines the standards and conventions for all API endpoints in the PixCrawler backend. Following these patterns ensures consistency, maintainability, and excellent API documentation.

## Table of Contents

1. [Route Path Conventions](#route-path-conventions)
2. [Response Models](#response-models)
3. [OpenAPI Documentation](#openapi-documentation)
4. [Docstrings](#docstrings)
5. [Type Hints](#type-hints)
6. [Error Handling](#error-handling)
7. [Compliance Checklist](#compliance-checklist)

---

## Route Path Conventions

### Rules

1. **Use `"/"` or `"/resource-name"` for list endpoints** - Never use empty string `""`
2. **Use consistent path parameters** - `"/{id}"` not `"/{resource_id}"`
3. **Follow RESTful conventions**:
   - `GET /resources` - List resources
   - `POST /resources` - Create resource
   - `GET /resources/{id}` - Get single resource
   - `PUT /resources/{id}` or `PATCH /resources/{id}` - Update resource
   - `DELETE /resources/{id}` - Delete resource

### Examples

```python
# ✅ CORRECT
@router.get("/notifications")
@router.get("/")
@router.get("/{id}")

# ❌ WRONG
@router.get("")  # Empty string not allowed
@router.get("/{notification_id}")  # Use {id} instead
```

---

## Response Models

### Rules

1. **All endpoints MUST have `response_model` parameter**
2. **Use Pydantic schemas from `backend/schemas/`**
3. **Return typed responses, not generic dictionaries**
4. **List endpoints MUST return `{data: [], meta: {}}` structure**

### List Response Pattern

```python
from pydantic import BaseModel, Field

class ResourceListResponse(BaseModel):
    """List response for resources."""
    data: List[ResourceResponse]
    meta: Dict[str, Any] = Field(
        default_factory=lambda: {"total": 0, "skip": 0, "limit": 50}
    )

@router.get(
    "/resources",
    response_model=ResourceListResponse,  # ✅ Typed response
)
async def list_resources() -> ResourceListResponse:  # ✅ Typed return
    return ResourceListResponse(
        data=resources,
        meta={"total": len(resources), "skip": 0, "limit": 50}
    )
```

### Single Resource Response Pattern

```python
@router.get(
    "/resources/{id}",
    response_model=ResourceResponse,  # ✅ Typed response
)
async def get_resource(id: int) -> ResourceResponse:  # ✅ Typed return
    return ResourceResponse(**resource_data)
```

### Action Response Pattern

```python
@router.post(
    "/resources/{id}/action",
    response_model=Dict[str, str],  # ✅ Even simple responses are typed
)
async def perform_action(id: int) -> Dict[str, str]:
    return {"message": "Action completed successfully"}
```

---

## OpenAPI Documentation

### Required Fields

Every endpoint MUST include:

1. `response_model` - Pydantic schema for response
2. `summary` - Brief description (< 50 chars)
3. `description` - Detailed explanation (2-3 sentences)
4. `response_description` - Describes the response content
5. `operation_id` - camelCase identifier (e.g., `"listNotifications"`)
6. `responses` - Dict with 200 example and common error responses

### Template

```python
from backend.api.v1.response_models import get_common_responses

@router.get(
    "/resources",
    response_model=ResourceListResponse,
    summary="List Resources",  # ✅ Brief, clear
    description="Retrieve a paginated list of resources for the authenticated user.",  # ✅ Detailed
    response_description="Paginated list of resources with metadata",  # ✅ Describes response
    operation_id="listResources",  # ✅ camelCase
    responses={
        200: {
            "description": "Successfully retrieved resources",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {
                                "id": 1,
                                "name": "Example Resource",
                                "status": "active"
                            }
                        ],
                        "meta": {
                            "total": 10,
                            "skip": 0,
                            "limit": 50
                        }
                    }
                }
            }
        },
        **get_common_responses(401, 500)  # ✅ Include common errors
    }
)
async def list_resources():
    pass
```

### Operation ID Naming Convention

Use camelCase format following this pattern:

- `list{Resources}` - List endpoints
- `create{Resource}` - Create endpoints
- `get{Resource}` - Get single resource
- `update{Resource}` - Update endpoints
- `delete{Resource}` - Delete endpoints
- `{action}{Resource}` - Action endpoints (e.g., `cancelCrawlJob`, `retryDataset`)

Examples:
- `listNotifications`
- `createCrawlJob`
- `getDataset`
- `updateProject`
- `deleteUser`
- `markNotificationAsRead`
- `cancelCrawlJob`

---

## Docstrings

### Required Sections

Every endpoint function MUST have a docstring with:

1. **Summary paragraph** - Detailed description of what the endpoint does
2. **Authentication note** - `**Authentication Required:** Bearer token` (or specify if not required)
3. **Additional context** - Query parameters, rate limits, warnings, etc.
4. **Args section** - All parameters with types and descriptions
5. **Returns section** - Return type and description
6. **Raises section** - Possible HTTPException errors

### Template

```python
async def list_resources(
    skip: int = 0,
    limit: int = 50,
    current_user: CurrentUser = Depends(get_current_user),
    service: ResourceService = Depends(get_resource_service),
) -> ResourceListResponse:
    """
    List all resources for the current user with pagination.
    
    Retrieves resources filtered by user ownership with support for
    pagination and optional filtering. Results are ordered by creation
    date descending.
    
    **Authentication Required:** Bearer token
    
    **Query Parameters:**
    - `skip` (int): Number of items to skip (default: 0)
    - `limit` (int): Maximum items to return (default: 50, max: 100)
    
    Args:
        skip: Pagination offset
        limit: Maximum number of items to return
        current_user: Current authenticated user (injected)
        service: Resource service instance (injected)
    
    Returns:
        ResourceListResponse with list of resources and pagination metadata
    
    Raises:
        HTTPException: 401 if authentication fails
        HTTPException: 500 if database query fails
    """
    pass
```

### Examples for Different Endpoint Types

#### List Endpoint

```python
"""
List all notifications for the current user.

Retrieves notifications with optional filtering by read status.
Supports pagination for efficient data retrieval.

**Authentication Required:** Bearer token

**Query Parameters:**
- `skip` (int): Pagination offset (default: 0)
- `limit` (int): Items per page (default: 50, max: 100)
- `unread_only` (bool): Filter to unread notifications only (default: false)

Args:
    skip: Number of items to skip
    limit: Maximum items to return
    unread_only: Filter by unread status
    current_user: Current authenticated user (injected)
    service: Notification service (injected)

Returns:
    NotificationListResponse with notifications and metadata

Raises:
    HTTPException: 401 if authentication fails
    HTTPException: 500 if database query fails
"""
```

#### Create Endpoint

```python
"""
Create a new crawl job and start execution in background.

Creates a new image crawling job with the specified configuration
and immediately queues it for processing. The job will execute
asynchronously using Celery workers.

**Authentication Required:** Bearer token

**Rate Limit:** 10 requests per minute

Args:
    job_create: Crawl job creation data
    background_tasks: FastAPI background tasks
    current_user: Current authenticated user (injected)
    service: CrawlJob service (injected)

Returns:
    CrawlJobResponse with created job information

Raises:
    HTTPException: 401 if authentication fails
    HTTPException: 422 if validation fails
    HTTPException: 429 if rate limit exceeded
    HTTPException: 500 if job creation fails
"""
```

#### Action Endpoint

```python
"""
Cancel a running or pending crawl job.

Attempts to cancel a crawl job that is currently running or pending.
Completed or failed jobs cannot be cancelled. The cancellation is
graceful and will wait for current operations to complete.

**Authentication Required:** Bearer token

**Warning:** Cancellation may take a few seconds to complete.

Args:
    job_id: Crawl job ID
    current_user: Current authenticated user (injected)
    service: CrawlJob service (injected)

Returns:
    Success message with cancellation status

Raises:
    HTTPException: 400 if job cannot be cancelled (wrong status)
    HTTPException: 401 if authentication fails
    HTTPException: 404 if job not found or access denied
    HTTPException: 500 if cancellation fails
"""
```

---

## Type Hints

### Rules

1. **All parameters MUST have type hints**
2. **Return type MUST match `response_model`**
3. **Use type aliases from `backend/api/types.py`**
4. **Use proper generic types** (`List`, `Dict`, `Optional`, etc.)

### Common Type Aliases

```python
from backend.api.types import (
    CurrentUser,      # Current authenticated user dict
    DBSession,        # AsyncSession for database
    JobID,            # Annotated[int, Path(ge=1)]
    DatasetID,        # Annotated[int, Path(ge=1)]
    UserID,           # Annotated[str, Path(min_length=1)]
    # Service dependencies
    CrawlJobServiceDep,
    DatasetServiceDep,
    NotificationServiceDep,
    # etc.
)
```

### Examples

```python
# ✅ CORRECT - Full type hints
async def list_resources(
    skip: int = 0,
    limit: int = 50,
    current_user: CurrentUser = Depends(get_current_user),
    service: ResourceService = Depends(get_resource_service),
) -> ResourceListResponse:
    pass

# ✅ CORRECT - Using type aliases
async def get_crawl_job(
    job_id: JobID,  # Annotated[int, Path(ge=1)]
    current_user: CurrentUser,
    service: CrawlJobServiceDep,
) -> CrawlJobResponse:
    pass

# ❌ WRONG - Missing type hints
async def list_resources(skip=0, limit=50, current_user, service):
    pass

# ❌ WRONG - Generic dict return
async def list_resources() -> dict:
    pass
```

---

## Error Handling

### Rules

1. **Use `HTTPException` for all errors**
2. **Include appropriate status codes**
3. **Provide clear, actionable error messages**
4. **Use `get_common_responses()` in route decorator**
5. **Document all possible exceptions in docstring**

### Common Error Patterns

```python
from fastapi import HTTPException, status

# 400 Bad Request - Invalid input
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Cannot cancel job with status: completed"
)

# 401 Unauthorized - Authentication required
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials"
)

# 403 Forbidden - Insufficient permissions
raise HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="You don't have permission to access this resource"
)

# 404 Not Found - Resource doesn't exist
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Crawl job not found"
)

# 422 Unprocessable Entity - Validation error
raise HTTPException(
    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    detail="Invalid email format"
)

# 429 Too Many Requests - Rate limit exceeded
# (Handled automatically by FastAPI-Limiter)

# 500 Internal Server Error - Unexpected error
raise HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Failed to process request"
)
```

### Error Handling Template

```python
async def get_resource(
    resource_id: int,
    current_user: CurrentUser,
    service: ResourceService,
) -> ResourceResponse:
    """Get resource by ID."""
    try:
        resource = await service.get_resource(resource_id)
        
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )
        
        # Check ownership
        if resource.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,  # Don't reveal existence
                detail="Resource not found"
            )
        
        return ResourceResponse(**resource)
    
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Failed to get resource {resource_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve resource"
        )
```

---

## Compliance Checklist

Use this checklist to verify endpoint compliance:

### Route Definition

- [ ] Route path uses `"/"` or `"/resource-name"` (not empty string `""`)
- [ ] Path parameters use `/{id}` format (not `/{resource_id}`)
- [ ] Follows RESTful conventions

### Response Model

- [ ] Has `response_model` parameter in decorator
- [ ] Uses Pydantic schema from `backend/schemas/`
- [ ] Return type matches `response_model`
- [ ] List endpoints return `{data: [], meta: {}}` structure

### OpenAPI Documentation

- [ ] Has `summary` (< 50 chars)
- [ ] Has `description` (2-3 sentences)
- [ ] Has `response_description`
- [ ] Has `operation_id` in camelCase
- [ ] Has `responses` dict with 200 example
- [ ] Uses `get_common_responses()` for error codes

### Docstring

- [ ] Has detailed description paragraph
- [ ] Has authentication note (`**Authentication Required:**`)
- [ ] Documents query parameters (if any)
- [ ] Documents rate limits (if any)
- [ ] Has `Args:` section with all parameters
- [ ] Has `Returns:` section
- [ ] Has `Raises:` section with all HTTPExceptions

### Type Hints

- [ ] All parameters have type hints
- [ ] Return type is specified
- [ ] Uses type aliases from `backend/api/types.py`
- [ ] Uses proper generic types (`List`, `Dict`, `Optional`)

### Error Handling

- [ ] Uses `HTTPException` for errors
- [ ] Appropriate status codes
- [ ] Clear error messages
- [ ] Re-raises HTTPException in try/except
- [ ] Logs unexpected errors

---

## Complete Example

Here's a fully compliant endpoint:

```python
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from backend.api.types import CurrentUser, NotificationServiceDep
from backend.api.v1.response_models import get_common_responses
from backend.schemas.notifications import NotificationListResponse, NotificationResponse

router = APIRouter(
    tags=["Notifications"],
    responses=get_common_responses(401, 500),
)

@router.get(
    "/notifications",
    response_model=NotificationListResponse,
    summary="List Notifications",
    description="Retrieve a paginated list of notifications for the authenticated user with optional filtering.",
    response_description="Paginated list of notifications with metadata",
    operation_id="listNotifications",
    responses={
        200: {
            "description": "Successfully retrieved notifications",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {
                                "id": 1,
                                "title": "Job Completed",
                                "message": "Your crawl job has finished",
                                "is_read": False,
                                "created_at": "2024-01-01T00:00:00Z"
                            }
                        ],
                        "meta": {
                            "total": 10,
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
async def list_notifications(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum items to return"),
    unread_only: bool = Query(False, description="Filter to unread notifications only"),
    current_user: CurrentUser = Depends(get_current_user),
    service: NotificationServiceDep = Depends(get_notification_service),
) -> NotificationListResponse:
    """
    List all notifications for the current user with pagination.
    
    Retrieves notifications filtered by user ownership with optional
    filtering by read status. Results are ordered by creation date
    descending for most recent first.
    
    **Authentication Required:** Bearer token
    
    **Query Parameters:**
    - `skip` (int): Pagination offset (default: 0)
    - `limit` (int): Items per page (default: 50, max: 100)
    - `unread_only` (bool): Show only unread notifications (default: false)
    
    Args:
        skip: Number of items to skip for pagination
        limit: Maximum number of items to return
        unread_only: Filter by unread status
        current_user: Current authenticated user (injected)
        service: Notification service instance (injected)
    
    Returns:
        NotificationListResponse with list of notifications and pagination metadata
    
    Raises:
        HTTPException: 401 if authentication fails
        HTTPException: 500 if database query fails
    """
    try:
        notifications = await service.get_notifications(
            user_id=current_user["user_id"],
            skip=skip,
            limit=limit,
            unread_only=unread_only
        )
        
        total = await service.count_notifications(
            user_id=current_user["user_id"],
            unread_only=unread_only
        )
        
        return NotificationListResponse(
            data=[NotificationResponse.model_validate(n) for n in notifications],
            meta={"total": total, "skip": skip, "limit": limit}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notifications"
        )
```

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic V2 Documentation](https://docs.pydantic.dev/latest/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [REST API Best Practices](https://restfulapi.net/)

---

**Last Updated:** 2024-01-27
**Version:** 1.0.0
