## Executive Summary
This document identifies critical architectural violations and type safety issues in the PixCrawler backend codebase. All issues violate the established three-layer architecture pattern (API → Service → Repository) and professional FastAPI best practices.

## Critical Architecture Violations

### 1. STATUS CODE IMPORT ERRORS (HIGH PRIORITY)

**Files Affected:**
- `backend/api/v1/endpoints/api_keys.py` (Lines 107, 157)
- `backend/api/v1/endpoints/crawl_jobs.py` (Line 52, 281)

**Issue:**
```python
# WRONG - Importing from wrong module
from backend.schemas.api_keys import APIKeyStatus
# Then using: status.HTTP_500_INTERNAL_SERVER_ERROR
# Error: Cannot find reference 'HTTP_500_INTERNAL_SERVER_ERROR' in 'APIKeyStatus | None'
```

**Root Cause:**
Variable name collision. `status` parameter shadows the `fastapi.status` module import.

**Fix Required:**
```python
# CORRECT PATTERN
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status  # Alias to avoid collision
from backend.schemas.api_keys import APIKeyStatus

# Then use:
raise HTTPException(
    status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail=f"Failed to retrieve API keys: {str(e)}"
)
```

**Action Items:**
1. Rename `status` import to `http_status` in all endpoint files
2. Update all `status.HTTP_*` references to `http_status.HTTP_*`
3. Keep schema enum imports as-is (e.g., `APIKeyStatus`, `DatasetStatus`)

---

### 2. SERVICE LAYER VIOLATIONS - MISSING PARAMETERS (CRITICAL)

**File:** `backend/services/crawl_job.py`

**Issue 1: Missing `user_id` parameter**
```python
# Line 456 - WRONG
await service.get_job_with_ownership_check(
    job_id=job_id,
    # Missing user_id parameter!
)
```

**Fix:**
```python
# CORRECT
await service.get_job_with_ownership_check(
    job_id=job_id,
    user_id=current_user["user_id"]  # Required parameter
)
```

**Issue 2: Useless service file**
The file `backend/services/crawl_job.py` contains 1971 lines of code that SHOULD use the `builder` package but instead reimplements crawling logic. This violates DRY principle and architecture.

**Action Required:**
1. Review `backend/services/crawl_job.py` completely
2. Replace custom crawling logic with `builder` package imports
3. Service should ONLY orchestrate, not implement crawling
4. Use `builder.tasks` for actual image downloading
5. Keep service focused on business logic and coordination

---

### 3. DATASET MODEL - TYPE MISMATCH (HIGH PRIORITY)

**File:** `backend/models/dataset.py` (Line 89)

**Issue:**
```python
# WRONG - Type mismatch
user_id: Mapped[UUID] = mapped_column(
    SQLAlchemyUUID(as_uuid=True),
    ForeignKey("profiles.id", ondelete="CASCADE"),
    nullable=False,
    index=True,
)

# But then used as:
__table_args__ = (
    Index("ix_datasets_user_id", "user_id"),  # String, not UUID list
    # Expected: list[UUID], got: str
)
```

**Fix:**
```python
# CORRECT - Use string for index name
__table_args__ = (
    Index("ix_datasets_user_id", user_id),  # Column object, not string
    Index("ix_datasets_status", status),
    Index("ix_datasets_user_status", user_id, status),
    Index("ix_datasets_created_at", created_at),
    # ... rest of constraints
)
```

---

### 4. MISSING ACTIVITY_LOG.CREATED_AT METHOD (MEDIUM PRIORITY)

**File:** `backend/models/activity_log.py` (MISSING FILE)

**Issue:**
ActivityLog model is imported from `backend.database.models` but doesn't have a `.created_at()` method. It should have a `created_at` column from `TimestampMixin`.

**Fix Required:**
1. Verify `ActivityLog` model extends `TimestampMixin`
2. Ensure `created_at` is a column, not a method
3. Update all references from `.created_at()` to `.created_at`

**Search Pattern:**
```bash
# Find all incorrect method calls
grep -r "\.created_at()" backend/
```

---

### 5. POLICY REPOSITORY - MISSING DOCSTRINGS (LOW PRIORITY)

**File:** `backend/repositories/policy_repository.py`

**Issue:**
Missing module-level docstring and inconsistent method documentation.

**Fix Required:**
```python
"""
Repository layer for dataset lifecycle policies.

This module provides data access for archival and cleanup policies,
following the repository pattern for clean architecture.

Classes:
    ArchivalPolicyRepository: Data access for archival policies
    CleanupPolicyRepository: Data access for cleanup policies
    PolicyExecutionLogRepository: Data access for policy execution logs

Architecture:
    - Extends BaseRepository for CRUD operations
    - Provides policy-specific query methods
    - Handles active policy filtering
"""

from typing import List, Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.policy import ArchivalPolicy, CleanupPolicy, PolicyExecutionLog
from .base import BaseRepository

__all__ = [
    'ArchivalPolicyRepository',
    'CleanupPolicyRepository',
    'PolicyExecutionLogRepository'
]


class ArchivalPolicyRepository(BaseRepository[ArchivalPolicy]):
    """
    Repository for archival policy data access.
    
    Provides methods for retrieving and managing archival policies
    that control dataset lifecycle transitions to archive storage.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize archival policy repository.
        
        Args:
            session: SQLAlchemy async session for database operations
        """
        super().__init__(session, ArchivalPolicy)

    async def get_active_policies(self) -> Sequence[ArchivalPolicy]:
        """
        Retrieve all active archival policies.
        
        Returns:
            Sequence of active ArchivalPolicy instances
            
        Note:
            Only returns policies where is_active=True
        """
        query = select(ArchivalPolicy).where(ArchivalPolicy.is_active == True)
        result = await self.session.execute(query)
        return result.scalars().all()
```

---

### 6. POLICY ENDPOINT - ARCHITECTURE VIOLATIONS (HIGH PRIORITY)

**File:** `backend/api/v1/endpoints/policies.py`

**Issues:**
1. Inconsistent dependency injection pattern
2. Missing proper response models
3. No operation_id in decorators
4. Mixing `Dict[str, Any]` with proper CurrentUser type
5. Missing service dependency type annotation

**Fix Required:**
```python
"""
Dataset lifecycle policy management endpoints.

This module provides REST API endpoints for managing archival and cleanup
policies that control dataset lifecycle transitions.

Endpoints:
    POST   /archival - Create archival policy (Admin only)
    GET    /archival - List archival policies (Admin only)
    GET    /archival/{policy_id} - Get archival policy (Admin only)
    PATCH  /archival/{policy_id} - Update archival policy (Admin only)
    DELETE /archival/{policy_id} - Delete archival policy (Admin only)
    POST   /cleanup - Create cleanup policy (Admin only)
    GET    /cleanup - List cleanup policies (Admin only)
    GET    /cleanup/{policy_id} - Get cleanup policy (Admin only)
    PATCH  /cleanup/{policy_id} - Update cleanup policy (Admin only)
    DELETE /cleanup/{policy_id} - Delete cleanup policy (Admin only)
    POST   /execute/archival - Trigger archival execution (Admin only)
    POST   /execute/cleanup - Trigger cleanup execution (Admin only)

Authentication:
    All endpoints require admin role authentication.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi import status as http_status

from backend.api.types import CurrentUser, PolicyServiceDep
from backend.api.v1.response_models import get_common_responses
from backend.schemas.policy import (
    ArchivalPolicyCreate,
    ArchivalPolicyResponse,
    ArchivalPolicyUpdate,
    CleanupPolicyCreate,
    CleanupPolicyResponse,
    CleanupPolicyUpdate,
)
from backend.tasks.policy import execute_archival_policies, execute_cleanup_policies

__all__ = ['router']

router = APIRouter(
    tags=["Policies"],
    responses=get_common_responses(401, 403, 404, 500),
)


def require_admin(current_user: CurrentUser) -> None:
    """
    Verify user has admin role.
    
    Args:
        current_user: Current authenticated user
        
    Raises:
        HTTPException: 403 if user is not admin
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )


@router.post(
    "/archival",
    response_model=ArchivalPolicyResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Create Archival Policy",
    description="Create a new archival policy for dataset lifecycle management (Admin only).",
    response_description="Created archival policy",
    operation_id="createArchivalPolicy",
    responses={
        201: {
            "description": "Archival policy created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Archive old datasets",
                        "is_active": True,
                        "age_days": 90
                    }
                }
            }
        },
        **get_common_responses(401, 403, 422, 500)
    }
)
async def create_archival_policy(
    policy_in: ArchivalPolicyCreate,
    current_user: CurrentUser,
    service: PolicyServiceDep,  # Use typed dependency
) -> ArchivalPolicyResponse:
    """
    Create a new archival policy.
    
    Creates a policy that automatically archives datasets based on age
    and access patterns. Requires admin role.
    
    **Authentication Required:** Bearer token with admin role
    
    Args:
        policy_in: Archival policy creation data
        current_user: Current authenticated user (injected)
        service: Policy service (injected)
        
    Returns:
        Created archival policy
        
    Raises:
        HTTPException: 403 if not admin
        HTTPException: 422 if validation fails
        HTTPException: 500 if creation fails
    """
    require_admin(current_user)
    return await service.create_archival_policy(policy_in)
```

**Action Items:**
1. Add proper module docstring
2. Create `PolicyServiceDep` type in `backend/api/types.py`
3. Add `operation_id` to all endpoints
4. Use `http_status` alias instead of `status`
5. Add comprehensive OpenAPI documentation
6. Create `require_admin` helper function
7. Add proper response examples

---

### 7. MISSING REPOSITORIES, SERVICES, AND MODELS (CRITICAL)

**Missing Files:**
1. `backend/services/policy.py` - PolicyService implementation
2. `backend/models/activity_log.py` - ActivityLog model (imported but missing)

**Action Required:**

**Create `backend/services/policy.py`:**
```python
"""
Policy service for dataset lifecycle management.

This module provides business logic for archival and cleanup policies
that control dataset lifecycle transitions.
"""

from typing import List, Optional
from backend.core.exceptions import NotFoundError, ValidationError
from backend.repositories.policy_repository import (
    ArchivalPolicyRepository,
    CleanupPolicyRepository,
    PolicyExecutionLogRepository
)
from backend.schemas.policy import (
    ArchivalPolicyCreate,
    ArchivalPolicyUpdate,
    CleanupPolicyCreate,
    CleanupPolicyUpdate
)
from backend.models.policy import ArchivalPolicy, CleanupPolicy
from .base import BaseService

__all__ = ['PolicyService']


class PolicyService(BaseService):
    """
    Service for policy business logic.
    
    Handles policy creation, updates, retrieval, and execution
    for dataset lifecycle management.
    """

    def __init__(
        self,
        archival_repo: ArchivalPolicyRepository,
        cleanup_repo: CleanupPolicyRepository,
        execution_log_repo: PolicyExecutionLogRepository
    ) -> None:
        """
        Initialize policy service with repositories.
        
        Args:
            archival_repo: Archival policy repository
            cleanup_repo: Cleanup policy repository
            execution_log_repo: Execution log repository
        """
        super().__init__()
        self.archival_repo = archival_repo
        self.cleanup_repo = cleanup_repo
        self.execution_log_repo = execution_log_repo

    async def create_archival_policy(
        self,
        policy_in: ArchivalPolicyCreate
    ) -> ArchivalPolicy:
        """
        Create a new archival policy.
        
        Args:
            policy_in: Policy creation data
            
        Returns:
            Created archival policy
            
        Raises:
            ValidationError: If policy data is invalid
        """
        self.log_operation("create_archival_policy", name=policy_in.name)
        
        # Check for duplicate name
        existing = await self.archival_repo.get_by_name(policy_in.name)
        if existing:
            raise ValidationError(f"Policy with name '{policy_in.name}' already exists")
        
        # Create policy
        policy_data = policy_in.model_dump()
        return await self.archival_repo.create(policy_data)

    # Add remaining methods following the same pattern...
```

**Create dependency in `backend/api/dependencies.py`:**
```python
async def get_policy_service(
    session: AsyncSession = Depends(get_session)
) -> PolicyService:
    """Create policy service with dependencies."""
    archival_repo = ArchivalPolicyRepository(session)
    cleanup_repo = CleanupPolicyRepository(session)
    execution_log_repo = PolicyExecutionLogRepository(session)
    
    return PolicyService(
        archival_repo=archival_repo,
        cleanup_repo=cleanup_repo,
        execution_log_repo=execution_log_repo
    )
```

**Add type in `backend/api/types.py`:**
```python
PolicyServiceDep = Annotated[
    PolicyService,
    Depends(get_policy_service)
]
```

---

### 8. DATASET SERVICE - UNEXPECTED ARGUMENTS (HIGH PRIORITY)

**File:** `backend/services/dataset.py`

**Issues:**

**Issue 1: Wrong repository method call (Line 85)**
```python
# WRONG
crawl_job = await self.crawl_job_repo.create(crawl_job_data)

# CORRECT - BaseRepository.create() expects **kwargs, not dict
crawl_job = await self.crawl_job_repo.create(**crawl_job_data)
```

**Issue 2: Missing parameters in validator call (Line 456)**
```python
# WRONG
result = await asyncio.to_thread(
    validator.check_integrity,
    directory=str(Path(image.storage_url).parent),
    expected_count=1,
    keyword=str(image_id)
    # Missing category_name parameter!
)

# CORRECT
result = await asyncio.to_thread(
    validator.check_integrity,
    directory=str(Path(image.storage_url).parent),
    expected_count=1,
    category_name=image.category or "default",  # Required parameter
    keyword=str(image_id)
)
```

**Issue 3: Type mismatch in metrics service (Line 234)**
```python
# WRONG - Passing UUID where int expected
await self.metrics_service.record_processing(
    user_id=user_id,  # UUID type
    # But method expects: user_id: int
)

# CORRECT
await self.metrics_service.record_processing(
    user_id=int(user_id) if isinstance(user_id, UUID) else user_id,
)
```

---

### 9. NOTIFICATION SERVICE - REPOSITORY METHOD ISSUES (MEDIUM PRIORITY)

**File:** `backend/services/notification.py`

**Issue 1: Wrong create method call (Line 78)**
```python
# WRONG
return await self.repository.create(notification_in.model_dump())

# CORRECT - BaseRepository.create() expects **kwargs
return await self.repository.create(**notification_in.model_dump())
```

**Issue 2: Non-existent repository method (Line 45)**
```python
# WRONG - NotificationRepository doesn't have .get() method
notification = await self.repository.get(notification_id)

# CORRECT - Use get_by_id() from BaseRepository
notification = await self.repository.get_by_id(notification_id)
```

---

### 10. PROJECT SERVICE - TYPE AND METHOD ISSUES (MEDIUM PRIORITY)

**File:** `backend/services/project.py`

**Issue 1: Wrong repository method (Line 56)**
```python
# WRONG
project = await self.repository.get(project_id)

# CORRECT
project = await self.repository.get_by_id(project_id)
```

**Issue 2: Wrong update method signature (Line 95)**
```python
# WRONG
return await self.repository.update(project_id, update_data)

# CORRECT - BaseRepository.update() expects (instance, **updates)
project = await self.repository.get_by_id(project_id)
return await self.repository.update(project, **update_data)
```

**Issue 3: Type mismatch (Line 78)**
```python
# WRONG - Returning int instead of Project
return await self.repository.create(project_data)
# Expected type 'Project', got 'int' instead

# CORRECT - create() returns the model instance
project = await self.repository.create(**project_data)
return project  # Returns Project instance
```

---

### 11. USER SERVICE - UPDATE METHOD SIGNATURE (HIGH PRIORITY)

**File:** `backend/services/user.py`

**Issue: Missing `instance` parameter (Line 145)**
```python
# WRONG
updated_user = await self.repository.update(
    user_id=user_id,
    email=email,
    full_name=full_name,
    role=role
)

# CORRECT - BaseRepository.update(instance, **updates)
user = await self.repository.get_by_uuid(user_id)
if not user:
    raise NotFoundError(f"User not found: {user_id}")

updated_user = await self.repository.update(
    user,  # Instance parameter required
    email=email,
    full_name=full_name,
    role=role
)
```

---

### 12. VALIDATION SERVICE - MISSING PARAMETERS (MEDIUM PRIORITY)

**File:** `backend/services/validation.py`

**Issue: Missing `category_name` parameter (Line 234)**
```python
# WRONG
result = await asyncio.to_thread(
    validator.check_integrity,
    directory=str(Path(image.storage_url).parent),
    expected_count=1,
    keyword=str(image_id)
    # Missing category_name!
)

# CORRECT
result = await asyncio.to_thread(
    validator.check_integrity,
    directory=str(Path(image.storage_url).parent),
    expected_count=1,
    category_name="validation",  # Required parameter
    keyword=str(image_id)
)
```

---

### 13. AZURE BLOB STORAGE - TYPE ISSUES (LOW PRIORITY)

**File:** `backend/storage/azure_blob_archive.py`

**Issue 1: Type mismatch in rehydrate_blob (Lines 456, 478)**
```python
# WRONG
def rehydrate_blob(
    self,
    blob_name: str,
    target_tier: AccessTier = AccessTier.HOT,
    priority: RehydratePriority = RehydratePriority.STANDARD
) -> Dict[str, Any]:
    # ...
    blob_client.set_standard_blob_tier(
        standard_tier,
        rehydrate_priority=priority.value  # Expects RehydratePriority, got str
    )

# CORRECT
blob_client.set_standard_blob_tier(
    standard_tier,
    rehydrate_priority=priority  # Pass enum, not .value
)
```

**Issue 2: Wrong metadata attribute (Line 589)**
```python
# WRONG
"metadata": properties.metadata_  # Wrong attribute name

# CORRECT
"metadata": properties.metadata  # Correct attribute name
```

---

## IMPLEMENTATION CHECKLIST

### Phase 1: Critical Fixes (Do First)
- [ ] Fix status code import collisions (all endpoint files)
- [ ] Fix missing user_id parameters in service calls
- [ ] Fix Dataset model index definitions
- [ ] Create missing PolicyService
- [ ] Fix repository method calls (create, update, get)

### Phase 2: Service Layer Cleanup
- [ ] Refactor crawl_job.py to use builder package
- [ ] Fix all BaseRepository.create() calls to use **kwargs
- [ ] Fix all BaseRepository.update() calls to pass instance
- [ ] Fix all BaseRepository.get() calls to use get_by_id()

### Phase 3: Type Safety
- [ ] Fix UUID to int conversions
- [ ] Fix RehydratePriority type issues
- [ ] Add missing type annotations
- [ ] Run mypy and fix all type errors

### Phase 4: Documentation
- [ ] Add module docstrings to all files
- [ ] Add operation_id to all endpoints
- [ ] Add comprehensive OpenAPI examples
- [ ] Update ARCHITECTURE.md with fixes
---

## ARCHITECTURE PRINCIPLES TO FOLLOW

### 1. Three-Layer Architecture
```
API Layer (Endpoints)
    ↓ depends on
Service Layer (Business Logic)
    ↓ depends on
Repository Layer (Data Access)
```

### 2. Dependency Injection Pattern
```python
# ALWAYS use factory pattern
async def get_service(
    session: AsyncSession = Depends(get_session)
) -> Service:
    repo = Repository(session)
    return Service(repo)

# ALWAYS use typed dependencies
ServiceDep = Annotated[Service, Depends(get_service)]
```

### 3. Repository Pattern
```python
# ALWAYS extend BaseRepository
class MyRepository(BaseRepository[MyModel]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MyModel)

# ALWAYS use correct method signatures
await repo.create(**data)  # Not create(data)
await repo.update(instance, **updates)  # Not update(id, updates)
await repo.get_by_id(id)  # Not get(id)
```

### 4. Service Pattern
```python
# ALWAYS depend on repositories, not session
class MyService(BaseService):
    def __init__(self, repository: MyRepository) -> None:
        super().__init__()
        self.repository = repository
    
    # NEVER access session directly
    # NEVER write SQL queries
    # ALWAYS delegate to repository
```

### 5. Endpoint Pattern
```python
# ALWAYS use typed dependencies
@router.post(
    "/resource",
    response_model=ResponseModel,
    status_code=http_status.HTTP_201_CREATED,
    summary="Create Resource",
    description="Detailed description",
    operation_id="createResource",
    responses={...}
)
async def create_resource(
    data: CreateRequest,
    current_user: CurrentUser,
    service: ServiceDep,
) -> ResponseModel:
    # NEVER access database directly
    # NEVER create service instances
    # ALWAYS delegate to service layer
    result = await service.create(data)
    return ResponseModel.model_validate(result)
```