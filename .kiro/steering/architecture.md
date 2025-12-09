# Backend Architecture Documentation

**Version:** 1.0  
**Last Updated:** January 2025

## Table of Contents

- [Overview](#overview)
- [Architecture Principles](#architecture-principles)
- [Layer Responsibilities](#layer-responsibilities)
- [Correct Patterns](#correct-patterns)
- [Anti-Patterns to Avoid](#anti-patterns-to-avoid)
- [Dependency Injection](#dependency-injection)
- [Testing Strategy](#testing-strategy)
- [Best Practices](#best-practices)

---

## Overview

The PixCrawler backend follows a **three-layer architecture pattern** with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│         API Layer (Endpoints)           │
│  HTTP Request/Response Handling         │
│  Authentication & Authorization         │
│  Input Validation & Serialization       │
└──────────────┬──────────────────────────┘
               │ Depends on
               ▼
┌─────────────────────────────────────────┐
│       Service Layer (Business Logic)    │
│  Business Rules & Validation            │
│  Workflow Orchestration                 │
│  Cross-Repository Coordination          │
└──────────────┬──────────────────────────┘
               │ Depends on
               ▼
┌─────────────────────────────────────────┐
│     Repository Layer (Data Access)      │
│  CRUD Operations                        │
│  Query Construction                     │
│  Transaction Management                 │
└──────────────┬──────────────────────────┘
               │ Uses
               ▼
┌─────────────────────────────────────────┐
│      Database Layer (SQLAlchemy)        │
│  ORM Models                             │
│  Database Schema                        │
└─────────────────────────────────────────┘
```

### Key Benefits

- **Testability**: Each layer can be tested independently with mocks
- **Maintainability**: Clear boundaries make code easier to understand and modify
- **Reusability**: Business logic in services can be reused across endpoints
- **Flexibility**: Easy to swap implementations (e.g., different databases)
- **Scalability**: Layers can be optimized independently

---

## Architecture Principles

### 1. Separation of Concerns

Each layer has a single, well-defined responsibility:

- **API Layer**: HTTP protocol concerns only
- **Service Layer**: Business logic only
- **Repository Layer**: Data access only

### 2. Dependency Direction

Dependencies flow downward only:

```
API → Service → Repository → Database
```

**Never:**
- Repository depends on Service
- Service depends on API
- Database depends on Repository

### 3. Dependency Injection

All dependencies are injected through constructors:

```python
# ✅ CORRECT
class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

# ❌ WRONG
class UserService:
    def __init__(self):
        self.repository = UserRepository(session)  # Creating dependency
```

### 4. Interface Segregation

Services depend on repository interfaces, not concrete implementations:

```python
# ✅ CORRECT
class UserService:
    def __init__(self, repository: UserRepository):  # Interface/base class
        self.repository = repository

# ❌ WRONG
class UserService:
    def __init__(self, session: AsyncSession):  # Concrete implementation
        self.session = session
```

### 5. Single Responsibility

Each class has one reason to change:

- **Endpoint**: Changes when HTTP API contract changes
- **Service**: Changes when business rules change
- **Repository**: Changes when data access patterns change

---

## Layer Responsibilities

### API Layer (Endpoints)

**Location:** `backend/api/v1/endpoints/`

#### Allowed Responsibilities

✅ HTTP request/response handling  
✅ Input validation using Pydantic schemas  
✅ Authentication and authorization checks  
✅ Response serialization  
✅ OpenAPI documentation  
✅ Error handling (converting exceptions to HTTP responses)

#### Not Allowed

❌ Business logic  
❌ Database queries  
❌ Data transformation (beyond serialization)  
❌ Direct session access  
❌ Creating service instances (use dependency injection)

#### Example

```python
@router.get(
    "/notifications",
    response_model=NotificationListResponse,
    summary="List Notifications",
    operation_id="listNotifications",
)
async def list_notifications(
    current_user: CurrentUser,  # ✅ Authentication
    service: NotificationServiceDep,  # ✅ Injected service
) -> NotificationListResponse:  # ✅ Typed response
    """List all notifications for the current user."""
    # ✅ Delegate to service layer
    notifications = await service.get_notifications(
        user_id=current_user["user_id"]
    )
    
    # ✅ Serialize response
    return NotificationListResponse(data=notifications)
```

---

### Service Layer (Business Logic)

**Location:** `backend/services/`

#### Allowed Responsibilities

✅ Business rules and validation  
✅ Workflow orchestration  
✅ Cross-repository coordination  
✅ Error handling and custom exceptions  
✅ Data transformation and aggregation  
✅ Complex calculations  
✅ External API calls

#### Not Allowed

❌ Direct database access via AsyncSession  
❌ HTTP concerns (request/response handling)  
❌ Raw SQL queries  
❌ Creating repository instances (use dependency injection)

#### Example

```python
class NotificationService:
    def __init__(self, repository: NotificationRepository):
        """Initialize service with repository dependency."""
        self.repository = repository  # ✅ Repository dependency
    
    async def get_notifications(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
        unread_only: bool = False
    ) -> List[Notification]:
        """Get notifications with business logic."""
        # ✅ Business rule: validate pagination
        if limit > 100:
            raise ValueError("Limit cannot exceed 100")
        
        # ✅ Delegate to repository
        notifications = await self.repository.get_by_user(
            user_id, skip, limit, unread_only
        )
        
        # ✅ Business logic: mark as delivered
        for notification in notifications:
            if not notification.delivered_at:
                notification.delivered_at = datetime.utcnow()
        
        await self.repository.bulk_update(notifications)
        
        return notifications
```

---

### Repository Layer (Data Access)

**Location:** `backend/repositories/`

#### Allowed Responsibilities

✅ CRUD operations  
✅ Query construction and execution  
✅ Database transaction management  
✅ Data access optimization  
✅ Simple filtering and sorting

#### Not Allowed

❌ Business logic  
❌ Complex calculations  
❌ Data transformation (beyond ORM mapping)  
❌ HTTP concerns  
❌ Workflow orchestration

#### Example

```python
class NotificationRepository(BaseRepository[Notification]):
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        super().__init__(session, Notification)
    
    async def get_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
        unread_only: bool = False
    ) -> List[Notification]:
        """Get notifications for a user (data access only)."""
        # ✅ Query construction
        query = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        # ✅ Simple filtering
        if unread_only:
            query = query.where(Notification.is_read == False)
        
        # ✅ Execute query
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def bulk_update(self, notifications: List[Notification]) -> None:
        """Update multiple notifications (data access only)."""
        # ✅ Simple persistence
        for notification in notifications:
            self.session.add(notification)
        await self.session.commit()
```

---

## Correct Patterns

### Pattern 1: Service with Repository Dependency

```python
# ✅ CORRECT
class CrawlJobService:
    def __init__(
        self,
        crawl_job_repo: CrawlJobRepository,
        project_repo: ProjectRepository,
        image_repo: ImageRepository
    ):
        """Service depends on repositories only."""
        self.crawl_job_repo = crawl_job_repo
        self.project_repo = project_repo
        self.image_repo = image_repo
    
    async def create_job(self, user_id: UUID, data: dict) -> CrawlJob:
        """Create crawl job with business logic."""
        # ✅ Business validation
        project = await self.project_repo.get_by_id(data["project_id"])
        if not project or project.user_id != user_id:
            raise ValueError("Invalid project")
        
        # ✅ Business rule: set defaults
        job_data = {
            **data,
            "status": "pending",
            "progress": 0,
            "created_at": datetime.utcnow()
        }
        
        # ✅ Delegate to repository
        job = await self.crawl_job_repo.create(job_data)
        
        # ✅ Business logic: log activity
        await self.activity_log_repo.create({
            "user_id": user_id,
            "action": "create_job",
            "resource_id": job.id
        })
        
        return job
```

### Pattern 2: Repository with Simple Data Access

```python
# ✅ CORRECT
class ProjectRepository(BaseRepository[Project]):
    def __init__(self, session: AsyncSession):
        """Repository depends on session only."""
        super().__init__(session, Project)
    
    async def get_by_user(self, user_id: UUID) -> List[Project]:
        """Get projects for user (data access only)."""
        result = await self.session.execute(
            select(Project)
            .where(Project.user_id == user_id)
            .order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_with_job_count(self, user_id: UUID) -> List[Dict]:
        """Get projects with job count (data access only)."""
        result = await self.session.execute(
            select(
                Project,
                func.count(CrawlJob.id).label("job_count")
            )
            .outerjoin(CrawlJob, CrawlJob.project_id == Project.id)
            .where(Project.user_id == user_id)
            .group_by(Project.id)
        )
        return [
            {"project": row[0], "job_count": row[1]}
            for row in result.all()
        ]
```

### Pattern 3: Endpoint with Service Dependency

```python
# ✅ CORRECT
@router.post(
    "/jobs",
    response_model=CrawlJobResponse,
    status_code=201,
    operation_id="createCrawlJob",
)
async def create_crawl_job(
    job_create: CrawlJobCreateRequest,  # ✅ Validated input
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,  # ✅ Authentication
    service: CrawlJobServiceDep,  # ✅ Injected service
) -> CrawlJobResponse:
    """Create a new crawl job."""
    try:
        # ✅ Delegate to service
        job = await service.create_job(
            user_id=current_user["user_id"],
            data=job_create.model_dump()
        )
        
        # ✅ HTTP concern: background task
        background_tasks.add_task(service.start_job, job.id)
        
        # ✅ Serialize response
        return CrawlJobResponse.model_validate(job)
    
    except ValueError as e:
        # ✅ Convert to HTTP error
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create job: {e}")
        raise HTTPException(status_code=500, detail="Failed to create job")
```

### Pattern 4: Dependency Injection Factory

```python
# ✅ CORRECT - In backend/api/dependencies.py
async def get_crawl_job_service(
    session: AsyncSession = Depends(get_session)
) -> CrawlJobService:
    """Create crawl job service with all dependencies."""
    # ✅ Create repositories
    crawl_job_repo = CrawlJobRepository(session)
    project_repo = ProjectRepository(session)
    image_repo = ImageRepository(session)
    activity_log_repo = ActivityLogRepository(session)
    
    # ✅ Inject repositories into service
    return CrawlJobService(
        crawl_job_repo=crawl_job_repo,
        project_repo=project_repo,
        image_repo=image_repo,
        activity_log_repo=activity_log_repo
    )

# ✅ CORRECT - In backend/api/types.py
CrawlJobServiceDep = Annotated[
    CrawlJobService,
    Depends(get_crawl_job_service)
]
```

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Service with Direct Session

```python
# ❌ WRONG
class CrawlJobService:
    def __init__(self, session: AsyncSession):
        """Service should NOT depend on session directly."""
        self.session = session  # ❌ Direct session dependency
    
    async def get_jobs(self, user_id: UUID) -> List[CrawlJob]:
        # ❌ Raw SQL query in service
        result = await self.session.execute(
            select(CrawlJob).where(CrawlJob.user_id == user_id)
        )
        return result.scalars().all()

# ✅ CORRECT
class CrawlJobService:
    def __init__(self, repository: CrawlJobRepository):
        """Service depends on repository only."""
        self.repository = repository
    
    async def get_jobs(self, user_id: UUID) -> List[CrawlJob]:
        # ✅ Delegate to repository
        return await self.repository.get_by_user(user_id)
```

### Anti-Pattern 2: Repository with Business Logic

```python
# ❌ WRONG
class CrawlJobRepository(BaseRepository[CrawlJob]):
    async def update_progress(self, job_id: int, progress: int) -> CrawlJob:
        job = await self.get_by_id(job_id)
        
        # ❌ Business logic in repository
        job.progress = progress
        if progress >= 100:
            job.status = "completed"  # ❌ Business rule
            job.completed_at = datetime.utcnow()
        
        await self.session.commit()
        return job

# ✅ CORRECT
class CrawlJobRepository(BaseRepository[CrawlJob]):
    async def update_fields(
        self,
        job_id: int,
        updates: Dict[str, Any]
    ) -> CrawlJob:
        """Update job fields (data access only)."""
        job = await self.get_by_id(job_id)
        for key, value in updates.items():
            setattr(job, key, value)
        await self.session.commit()
        return job

class CrawlJobService:
    async def update_progress(self, job_id: int, progress: int) -> CrawlJob:
        """Update progress with business logic."""
        # ✅ Business logic in service
        updates = {"progress": progress}
        if progress >= 100:
            updates["status"] = "completed"
            updates["completed_at"] = datetime.utcnow()
        
        # ✅ Delegate to repository
        return await self.repository.update_fields(job_id, updates)
```

### Anti-Pattern 3: Endpoint with Database Queries

```python
# ❌ WRONG
@router.get("/jobs")
async def list_jobs(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),  # ❌ Direct session
):
    # ❌ Database query in endpoint
    result = await session.execute(
        select(CrawlJob)
        .join(Project)
        .where(Project.user_id == current_user["user_id"])
    )
    jobs = result.scalars().all()
    
    # ❌ Business logic in endpoint
    return {
        "data": [
            {
                "id": job.id,
                "status": job.status,
                "progress": job.progress
            }
            for job in jobs
        ]
    }

# ✅ CORRECT
@router.get(
    "/jobs",
    response_model=CrawlJobListResponse,
    operation_id="listCrawlJobs",
)
async def list_jobs(
    current_user: CurrentUser,
    service: CrawlJobServiceDep,  # ✅ Injected service
) -> CrawlJobListResponse:
    """List crawl jobs."""
    # ✅ Delegate to service
    jobs = await service.get_jobs(user_id=current_user["user_id"])
    
    # ✅ Serialize response
    return CrawlJobListResponse(data=jobs)
```

### Anti-Pattern 4: Creating Dependencies in Endpoint

```python
# ❌ WRONG
@router.post("/jobs")
async def create_job(
    data: dict,
    session: AsyncSession = Depends(get_session),
):
    # ❌ Creating repository in endpoint
    repository = CrawlJobRepository(session)
    
    # ❌ Creating service in endpoint
    service = CrawlJobService(repository)
    
    job = await service.create_job(data)
    return {"data": job}

# ✅ CORRECT
@router.post(
    "/jobs",
    response_model=CrawlJobResponse,
    operation_id="createCrawlJob",
)
async def create_job(
    data: CrawlJobCreateRequest,
    service: CrawlJobServiceDep,  # ✅ Injected service
) -> CrawlJobResponse:
    """Create crawl job."""
    job = await service.create_job(data.model_dump())
    return CrawlJobResponse.model_validate(job)
```

### Anti-Pattern 5: Optional Session Parameter

```python
# ❌ WRONG
class UserService:
    def __init__(
        self,
        repository: UserRepository,
        session: Optional[AsyncSession] = None  # ❌ Optional session
    ):
        self.repository = repository
        self.session = session  # ❌ Storing session

# ✅ CORRECT
class UserService:
    def __init__(self, repository: UserRepository):
        """Service depends on repository only."""
        self.repository = repository
        # No session parameter or storage
```

---

## Dependency Injection

### Factory Pattern

All services use the factory pattern for dependency injection:

```python
# In backend/api/dependencies.py
async def get_notification_service(
    session: AsyncSession = Depends(get_session)
) -> NotificationService:
    """Create notification service with dependencies."""
    repository = NotificationRepository(session)
    return NotificationService(repository)

# In backend/api/types.py
NotificationServiceDep = Annotated[
    NotificationService,
    Depends(get_notification_service)
]

# In endpoint
@router.get("/notifications")
async def list_notifications(
    service: NotificationServiceDep,  # ✅ Type-safe injection
) -> NotificationListResponse:
    pass
```

### Benefits

- **Testability**: Easy to mock dependencies in tests
- **Flexibility**: Easy to swap implementations
- **Type Safety**: Full type checking with MyPy
- **Consistency**: Same pattern across all endpoints
- **Maintainability**: Dependencies defined in one place

---

## Testing Strategy

### Unit Tests

Test each layer independently with mocks:

```python
# Test service with mocked repository
async def test_create_job():
    # Arrange
    mock_repo = Mock(CrawlJobRepository)
    mock_repo.create.return_value = CrawlJob(id=1, status="pending")
    
    service = CrawlJobService(repository=mock_repo)
    
    # Act
    job = await service.create_job(user_id=UUID("..."), data={...})
    
    # Assert
    assert job.status == "pending"
    mock_repo.create.assert_called_once()
```

### Integration Tests

Test multiple layers together:

```python
# Test endpoint with real service and mocked repository
async def test_create_job_endpoint(client, auth_headers):
    response = await client.post(
        "/api/v1/jobs",
        json={"name": "Test Job", ...},
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
```

### Architecture Tests

Verify architectural constraints:

```python
def test_services_dont_import_async_session():
    """Ensure services don't import AsyncSession directly."""
    for service_file in Path("backend/services").glob("*.py"):
        content = service_file.read_text()
        if "AsyncSession" in content and "TYPE_CHECKING" not in content:
            pytest.fail(f"{service_file} imports AsyncSession")

def test_repositories_extend_base_repository():
    """Verify all repositories extend BaseRepository."""
    # Implementation checks inheritance

def test_endpoints_dont_have_queries():
    """Ensure endpoints don't execute database queries."""
    # Implementation checks for select() calls
```

---

## Best Practices

### 1. Keep Layers Thin

Each layer should be as simple as possible:

- **Endpoints**: Just HTTP handling
- **Services**: Just business logic
- **Repositories**: Just data access

### 2. Use Type Hints Everywhere

```python
# ✅ CORRECT
async def get_jobs(self, user_id: UUID) -> List[CrawlJob]:
    pass

# ❌ WRONG
async def get_jobs(self, user_id):
    pass
```

### 3. Document Public APIs

```python
async def create_job(self, user_id: UUID, data: dict) -> CrawlJob:
    """
    Create a new crawl job.
    
    Args:
        user_id: User ID creating the job
        data: Job configuration data
    
    Returns:
        Created crawl job instance
    
    Raises:
        ValueError: If project is invalid
    """
    pass
```

### 4. Handle Errors Appropriately

```python
# In service
async def get_job(self, job_id: int) -> CrawlJob:
    job = await self.repository.get_by_id(job_id)
    if not job:
        raise ValueError(f"Job {job_id} not found")
    return job

# In endpoint
try:
    job = await service.get_job(job_id)
    return CrawlJobResponse.model_validate(job)
except ValueError as e:
    raise HTTPException(status_code=404, detail=str(e))
```

### 5. Use Pydantic for Validation

```python
# Request schema
class CrawlJobCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    project_id: int = Field(..., gt=0)
    keywords: List[str] = Field(..., min_items=1)
    max_images: int = Field(100, ge=1, le=10000)

# Response schema
class CrawlJobResponse(BaseModel):
    id: int
    name: str
    status: str
    progress: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
```

### 6. Follow Naming Conventions

- **Services**: `{Resource}Service` (e.g., `CrawlJobService`)
- **Repositories**: `{Resource}Repository` (e.g., `CrawlJobRepository`)
- **Endpoints**: `{action}_{resource}` (e.g., `create_crawl_job`)
- **Schemas**: `{Resource}{Action}Request/Response` (e.g., `CrawlJobCreateRequest`)

### 7. Keep Methods Focused

Each method should do one thing:

```python
# ✅ CORRECT - Focused methods
async def create_job(self, data: dict) -> CrawlJob:
    """Create job only."""
    return await self.repository.create(data)

async def start_job(self, job_id: int) -> None:
    """Start job only."""
    await self.queue_job(job_id)

# ❌ WRONG - Doing too much
async def create_and_start_job(self, data: dict) -> CrawlJob:
    """Creates AND starts job - too much responsibility."""
    job = await self.repository.create(data)
    await self.queue_job(job.id)
    await self.send_notification(job.user_id)
    await self.log_activity(job.id)
    return job
```

---

## Summary

The PixCrawler backend architecture enforces clean separation of concerns through three distinct layers:

1. **API Layer**: HTTP concerns only
2. **Service Layer**: Business logic only
3. **Repository Layer**: Data access only

**Key Principles:**
- Services depend on repositories, not sessions
- Repositories extend BaseRepository
- Endpoints use service layer via dependency injection
- Each layer has a single responsibility
- Dependencies flow downward only

**Benefits:**
- Testable (each layer can be tested independently)
- Maintainable (clear boundaries and responsibilities)
- Flexible (easy to swap implementations)
- Type-safe (full type hints with MyPy)
- Scalable (layers can be optimized independently)

For implementation examples, see:
- [Endpoint Style Guide](./api/v1/ENDPOINT_STYLE_GUIDE.md)
- [Migration Guide](../docs/MIGRATION_GUIDE.md)
- [Repository Pattern Audit](../docs/REPOSITORY_PATTERN_AUDIT.md)

---

**Last Updated:** January 2025  
**Version:** 1.0.0
