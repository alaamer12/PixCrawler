# Design Document: Celery Tasks Integration with Repository Pattern

## Overview

This design document outlines the integration of Celery tasks from the builder and validator packages into the FastAPI backend API endpoints. The integration follows the established Repository Pattern and ensures proper database session management for distributed workers.

### Goals

1. Enable asynchronous image crawling and validation through RESTful API endpoints
2. Maintain proper separation between API layer, service layer, and data access layer
3. Ensure database session isolation between API processes and Celery worker processes
4. Provide real-time progress tracking for long-running crawl jobs
5. Implement comprehensive error handling and recovery mechanisms
6. Support idempotent operations to handle duplicate requests gracefully

### Non-Goals

1. Implementing new Celery tasks (we use existing tasks from builder and validator packages)
2. Modifying the frontend application
3. Changing the database schema (we work with existing tables)
4. Implementing custom authentication (we use existing Supabase Auth)

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     API Layer (FastAPI)                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Endpoints: /jobs, /validation, /keywords, /labels     │ │
│  │  - Authentication (Supabase JWT)                       │ │
│  │  - Request validation (Pydantic schemas)               │ │
│  │  - Response formatting                                 │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  CrawlJobService, ValidationService                    │ │
│  │  - Business logic orchestration                        │ │
│  │  - Task dispatch coordination                          │ │
│  │  - Result handling                                     │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Repository Layer                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  CrawlJobRepository, ImageRepository                   │ │
│  │  - Database operations (CRUD)                          │ │
│  │  - Query abstraction                                   │ │
│  │  - Transaction management                              │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              Database (Supabase PostgreSQL)                  │
│  Tables: crawl_jobs, images, notifications, etc.            │
└─────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │ Celery Tasks │
                    │ (Distributed)│
                    └──────────────┘
                            ↑
                    Task Dispatch (Redis)
                            ↑
                    Service Layer
```

### Component Interactions

1. **API Endpoint** receives authenticated request
2. **Service Layer** validates business rules and dispatches tasks
3. **Repository Layer** persists task metadata and job state
4. **Celery Workers** execute tasks asynchronously
5. **Task Callbacks** update job progress through service layer
6. **Real-time Updates** propagate to frontend via Supabase subscriptions

## Components and Interfaces

### 1. API Endpoints

#### Crawl Jobs Endpoints (`backend/api/v1/endpoints/crawl_jobs.py`)

```python
@router.post("/jobs/{job_id}/start", response_model=JobStartResponse)
async def start_crawl_job(
    job_id: int,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> JobStartResponse:
    """
    Start a crawl job by dispatching Celery tasks.
    
    Args:
        job_id: ID of the job to start
        session: Database session
        current_user: Authenticated user
        
    Returns:
        JobStartResponse with task IDs and status
        
    Raises:
        HTTPException: 404 if job not found, 403 if unauthorized, 400 if invalid status
    """
```

```python
@router.post("/jobs/{job_id}/stop", response_model=JobStopResponse)
async def stop_crawl_job(
    job_id: int,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> JobStopResponse:
    """
    Stop a running crawl job by revoking Celery tasks.
    
    Args:
        job_id: ID of the job to stop
        session: Database session
        current_user: Authenticated user
        
    Returns:
        JobStopResponse with cancellation status
        
    Raises:
        HTTPException: 404 if job not found, 403 if unauthorized, 400 if not running
    """
```

```python
@router.get("/jobs/{job_id}/progress", response_model=JobProgressResponse)
async def get_job_progress(
    job_id: int,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> JobProgressResponse:
    """
    Get current progress of a crawl job.
    
    Args:
        job_id: ID of the job
        session: Database session
        current_user: Authenticated user
        
    Returns:
        JobProgressResponse with progress percentage and chunk statistics
        
    Raises:
        HTTPException: 404 if job not found, 403 if unauthorized
    """
```

#### Validation Endpoints (`backend/api/v1/endpoints/validation.py`)

```python
@router.post("/validation/job/{job_id}", response_model=ValidationResponse)
async def validate_job_images(
    job_id: int,
    request: ValidationRequest,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> ValidationResponse:
    """
    Validate all images in a job.
    
    Args:
        job_id: ID of the job
        request: Validation request with level (fast/medium/slow)
        session: Database session
        current_user: Authenticated user
        
    Returns:
        ValidationResponse with task IDs
        
    Raises:
        HTTPException: 404 if job not found or no images, 403 if unauthorized
    """
```

### 2. Service Layer

#### CrawlJobService (`backend/services/crawl_job.py`)

```python
class CrawlJobService:
    """Service for managing crawl jobs and task orchestration."""
    
    def __init__(
        self,
        job_repository: CrawlJobRepository,
        image_repository: ImageRepository,
        notification_service: NotificationService
    ):
        self.job_repository = job_repository
        self.image_repository = image_repository
        self.notification_service = notification_service
    
    async def start_job(self, job_id: int, user_id: str) -> Dict[str, Any]:
        """
        Start a crawl job by dispatching Celery tasks.
        
        Steps:
        1. Retrieve job from repository
        2. Validate job status (must be 'pending')
        3. Validate job ownership
        4. Calculate total chunks (keywords × engines)
        5. Dispatch download tasks for each keyword-engine combination
        6. Store task IDs in database
        7. Update job status to 'running'
        8. Create notification
        
        Args:
            job_id: ID of the job to start
            user_id: ID of the user starting the job
            
        Returns:
            Dict with task_ids, status, and message
            
        Raises:
            ValueError: If job not found, unauthorized, or invalid status
        """
    
    async def stop_job(self, job_id: int, user_id: str) -> Dict[str, Any]:
        """
        Stop a running job by revoking Celery tasks.
        
        Steps:
        1. Retrieve job from repository
        2. Validate job ownership
        3. Retrieve active task IDs
        4. Revoke each task using celery_core.app.control.revoke()
        5. Update job status to 'cancelled'
        6. Create notification
        
        Args:
            job_id: ID of the job to stop
            user_id: ID of the user stopping the job
            
        Returns:
            Dict with revoked task count and status
            
        Raises:
            ValueError: If job not found, unauthorized, or not running
        """
    
    async def handle_task_completion(
        self,
        job_id: int,
        task_id: str,
        result: Dict[str, Any]
    ) -> None:
        """
        Handle task completion callback.
        
        Steps:
        1. Retrieve job from repository
        2. Update chunk counters (completed_chunks++, active_chunks--)
        3. Calculate progress percentage
        4. If successful, create image records
        5. If failed, increment failed_chunks
        6. If all chunks complete, mark job as completed
        7. Create notification if job completed
        
        Args:
            job_id: ID of the job
            task_id: ID of the completed task
            result: Task result dictionary
        """
```

#### ValidationService (`backend/services/validation.py`)

```python
class ValidationService:
    """Service for managing image validation tasks."""
    
    def __init__(
        self,
        image_repository: ImageRepository,
        job_repository: CrawlJobRepository
    ):
        self.image_repository = image_repository
        self.job_repository = job_repository
    
    async def validate_job_images(
        self,
        job_id: int,
        validation_level: str = "medium"
    ) -> Dict[str, Any]:
        """
        Validate all images in a job.
        
        Steps:
        1. Retrieve all images for the job
        2. Select validation task based on level
        3. Dispatch validation task for each image
        4. Return task IDs for tracking
        
        Args:
            job_id: ID of the job
            validation_level: Validation level (fast/medium/slow)
            
        Returns:
            Dict with task_ids, images_count, and validation_level
            
        Raises:
            ValueError: If no images found for job
        """
    
    async def handle_validation_result(
        self,
        image_id: int,
        result: Dict[str, Any]
    ) -> None:
        """
        Handle validation task result.
        
        Steps:
        1. Retrieve image from repository
        2. Update validation status
        3. Update is_valid and is_duplicate flags
        4. Store validation metadata
        
        Args:
            image_id: ID of the image
            result: Validation result dictionary
        """
```

### 3. Repository Layer

#### CrawlJobRepository Extensions (`backend/repositories/crawl_job_repository.py`)

```python
class CrawlJobRepository(BaseRepository[CrawlJob]):
    """Repository for crawl job database operations."""
    
    async def add_task_id(self, job_id: int, task_id: str) -> CrawlJob:
        """
        Add a task ID to the job's task_ids array.
        
        Args:
            job_id: ID of the job
            task_id: Celery task ID to add
            
        Returns:
            Updated CrawlJob instance
        """
    
    async def update_progress(
        self,
        job_id: int,
        progress: int,
        completed_chunks: int,
        active_chunks: int
    ) -> CrawlJob:
        """
        Update job progress and chunk counters.
        
        Args:
            job_id: ID of the job
            progress: Progress percentage (0-100)
            completed_chunks: Number of completed chunks
            active_chunks: Number of active chunks
            
        Returns:
            Updated CrawlJob instance
        """
    
    async def mark_completed(self, job_id: int) -> CrawlJob:
        """
        Mark a job as completed.
        
        Args:
            job_id: ID of the job
            
        Returns:
            Updated CrawlJob instance with status='completed'
        """
    
    async def mark_failed(self, job_id: int, error: str) -> CrawlJob:
        """
        Mark a job as failed with error message.
        
        Args:
            job_id: ID of the job
            error: Error message
            
        Returns:
            Updated CrawlJob instance with status='failed'
        """
    
    async def get_active_tasks(self, job_id: int) -> List[str]:
        """
        Get list of active task IDs for a job.
        
        Args:
            job_id: ID of the job
            
        Returns:
            List of active Celery task IDs
        """
```

#### ImageRepository Extensions (`backend/repositories/image_repository.py`)

```python
class ImageRepository(BaseRepository[Image]):
    """Repository for image database operations."""
    
    async def create_from_download(
        self,
        job_id: int,
        image_data: Dict[str, Any]
    ) -> Image:
        """
        Create an image record from download task result.
        
        Args:
            job_id: ID of the crawl job
            image_data: Dictionary with image metadata
                - original_url: Source URL
                - filename: Local filename
                - storage_url: Storage URL
                - width: Image width
                - height: Image height
                - file_size: File size in bytes
                - format: Image format (jpg, png, webp)
                - hash: Perceptual hash
                
        Returns:
            Created Image instance
        """
    
    async def mark_validated(
        self,
        image_id: int,
        validation_result: Dict[str, Any]
    ) -> Image:
        """
        Update image with validation results.
        
        Args:
            image_id: ID of the image
            validation_result: Dictionary with validation data
                - is_valid: Boolean validation status
                - is_duplicate: Boolean duplicate status
                - metadata: Additional validation metadata
                
        Returns:
            Updated Image instance
        """
    
    async def get_by_job(self, job_id: int) -> List[Image]:
        """
        Get all images for a job.
        
        Args:
            job_id: ID of the crawl job
            
        Returns:
            List of Image instances
        """
    
    async def count_by_job(self, job_id: int) -> int:
        """
        Count images for a job.
        
        Args:
            job_id: ID of the crawl job
            
        Returns:
            Number of images
        """
```

## Data Models

### Request/Response Schemas

#### JobStartResponse (`backend/schemas/crawl_jobs.py`)

```python
class JobStartResponse(BaseModel):
    """Response schema for job start endpoint."""
    
    job_id: int
    status: str
    task_ids: List[str]
    total_chunks: int
    message: str
```

#### JobStopResponse (`backend/schemas/crawl_jobs.py`)

```python
class JobStopResponse(BaseModel):
    """Response schema for job stop endpoint."""
    
    job_id: int
    status: str
    revoked_tasks: int
    message: str
```

#### JobProgressResponse (`backend/schemas/crawl_jobs.py`)

```python
class JobProgressResponse(BaseModel):
    """Response schema for job progress endpoint."""
    
    job_id: int
    status: str
    progress: int
    total_chunks: int
    active_chunks: int
    completed_chunks: int
    failed_chunks: int
    downloaded_images: int
    estimated_completion: Optional[datetime]
```

#### ValidationRequest (`backend/schemas/validation.py`)

```python
class ValidationRequest(BaseModel):
    """Request schema for validation endpoint."""
    
    level: Literal["fast", "medium", "slow"] = "medium"
```

#### ValidationResponse (`backend/schemas/validation.py`)

```python
class ValidationResponse(BaseModel):
    """Response schema for validation endpoint."""
    
    job_id: int
    images_count: int
    validation_level: str
    task_ids: List[str]
    message: str
```

### Task Result Format

All Celery tasks return a standardized result dictionary:

```python
{
    "success": bool,           # Whether task succeeded
    "job_id": str,            # Job ID (for tracking)
    "user_id": str,           # User ID (for notifications)
    "downloaded": int,        # Number of images downloaded (download tasks)
    "images": List[Dict],     # Image metadata (download tasks)
    "error": Optional[str],   # Error message (if failed)
    "metadata": Dict          # Additional task-specific data
}
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Task Dispatch Serialization

*For any* task dispatch operation, all arguments passed to Celery tasks must be serializable primitive types (strings, integers, dictionaries, lists), with no AsyncSession instances, repository instances, or other non-serializable objects.

**Validates: Requirements 1.2, 2.1, 2.2**

### Property 2: Task ID Persistence

*For any* successful task dispatch, the task ID must be stored in the database and retrievable through the job's task_ids field.

**Validates: Requirements 1.3**

### Property 3: Job Start Correctness

*For any* job in pending status, starting the job must dispatch exactly (number of keywords × number of engines) tasks, update the job status to "running", and set total_chunks to the number of dispatched tasks.

**Validates: Requirements 1.1, 1.5**

### Property 4: Job Start Idempotency

*For any* job not in pending status, attempting to start the job must return a 400 error without dispatching new tasks, or if already running, return existing task IDs without dispatching new tasks.

**Validates: Requirements 1.4, 11.1**

### Property 5: Chunk Counter Invariant

*For any* task completion, the job's completed_chunks must increment by 1, active_chunks must decrement by 1, and the invariant (completed_chunks + active_chunks + failed_chunks ≤ total_chunks) must hold.

**Validates: Requirements 3.1, 3.2**

### Property 6: Progress Calculation

*For any* job with total_chunks > 0, the progress percentage must equal (completed_chunks / total_chunks) × 100, rounded to an integer.

**Validates: Requirements 3.3**

### Property 7: Job Completion Detection

*For any* job where completed_chunks + failed_chunks equals total_chunks, the job status must be updated to "completed" and a completion notification must be created.

**Validates: Requirements 3.4, 6.5**

### Property 8: Progress Endpoint Accuracy

*For any* job, the GET `/api/v1/jobs/{job_id}/progress` endpoint must return the current progress percentage and chunk statistics that match the database state.

**Validates: Requirements 3.5**

### Property 9: Job Stop Completeness

*For any* running job, stopping the job must revoke all active tasks, update the job status to "cancelled", and create a cancellation notification.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4**

### Property 10: Job Stop Idempotency

*For any* job not in running status, attempting to stop the job must return a 400 error without attempting to revoke tasks, or if already stopped, return success without side effects.

**Validates: Requirements 4.5, 11.2**

### Property 11: Validation Task Selection

*For any* validation request, the system must dispatch validation tasks using the task type corresponding to the requested level (fast → validate_image_fast_task, medium → validate_image_medium_task, slow → validate_image_slow_task).

**Validates: Requirements 5.2, 5.3, 5.4, 5.5**

### Property 12: Validation Result Persistence

*For any* completed validation task, the corresponding image record must be updated with the validation results (is_valid, is_duplicate, metadata).

**Validates: Requirements 5.6**

### Property 13: Image Creation from Download

*For any* successful download task result containing N images, exactly N image records must be created in the database with the correct job_id and metadata.

**Validates: Requirements 6.1**

### Property 14: Download Counter Update

*For any* successful download task result containing N images, the job's downloaded_images count must increase by N.

**Validates: Requirements 6.2**

### Property 15: Failure Counter Update

*For any* failed task, the job's failed_chunks count must increment by 1.

**Validates: Requirements 6.3**

### Property 16: Authentication Enforcement

*For any* protected endpoint request without a valid Authorization header or with an invalid JWT token, the system must return a 401 Unauthorized error.

**Validates: Requirements 8.1, 8.2**

### Property 17: Authorization Enforcement

*For any* request to access a job or resource, if the resource does not belong to the authenticated user, the system must return a 403 Forbidden error.

**Validates: Requirements 7.3, 8.4**

### Property 18: Resource Not Found Handling

*For any* request with a non-existent job_id or resource_id, the system must return a 404 Not Found error.

**Validates: Requirements 7.2**

### Property 19: Validation Error Handling

*For any* request with invalid input data, the system must return a 422 Unprocessable Entity error with field-level error details.

**Validates: Requirements 7.4**

### Property 20: Task Dispatch Error Handling

*For any* task dispatch operation that fails due to Celery or Redis errors, the system must return a 500 Internal Server Error with error details and log the error.

**Validates: Requirements 7.1**

### Property 21: User ID Extraction

*For any* valid JWT token, the system must successfully extract the user ID and make it available to the endpoint handler.

**Validates: Requirements 8.3**

### Property 22: Service Orchestration Order

*For any* job start operation, the system must validate job ownership and status before dispatching any tasks, ensuring no tasks are dispatched for unauthorized or invalid requests.

**Validates: Requirements 10.1**

### Property 23: Task Result Processing

*For any* task completion callback, the system must update all related database records (job progress, chunk counters, image records) within a single transaction.

**Validates: Requirements 10.3**

### Property 24: Atomic Job Stop

*For any* job stop operation, task revocation and job status update must occur atomically, ensuring consistent state even if the operation is interrupted.

**Validates: Requirements 10.5**

### Property 25: Result Deduplication

*For any* task result received multiple times (duplicate callbacks), only the first result must be processed, with subsequent duplicates being ignored.

**Validates: Requirements 11.3**

### Property 26: Retry Counter Reset

*For any* job retry operation, the chunk counters (active_chunks, completed_chunks, failed_chunks) must be reset to 0 before dispatching new tasks.

**Validates: Requirements 11.4**

## Error Handling

### Error Categories

1. **Client Errors (4xx)**
   - 400 Bad Request: Invalid job status for operation
   - 401 Unauthorized: Missing or invalid authentication
   - 403 Forbidden: Insufficient permissions
   - 404 Not Found: Resource not found
   - 422 Unprocessable Entity: Validation errors

2. **Server Errors (5xx)**
   - 500 Internal Server Error: Task dispatch failures, database errors
   - 503 Service Unavailable: Celery or Redis unavailable

### Error Response Format

All errors follow a consistent format:

```python
{
    "message": "Error category",
    "details": [
        {
            "detail": "Specific error message",
            "error_code": "ERROR_CODE",
            "field": "field_name"  # For validation errors
        }
    ],
    "request_id": "uuid"
}
```

### Error Handling Strategy

1. **Validation Errors**: Caught at Pydantic schema level, return 422
2. **Business Logic Errors**: Raised as custom exceptions in service layer, mapped to appropriate HTTP status
3. **Database Errors**: Caught in repository layer, logged and re-raised as service errors
4. **Task Dispatch Errors**: Caught in service layer, logged and returned as 500 errors
5. **Authentication Errors**: Handled by FastAPI dependency injection, return 401
6. **Authorization Errors**: Checked in service layer, return 403

### Logging Strategy

All errors are logged with structured context:

```python
logger.error(
    "Operation failed",
    operation="start_job",
    job_id=job_id,
    user_id=user_id,
    error=str(error),
    request_id=request_id
)
```

## Testing Strategy

### Unit Testing

Unit tests will verify individual components in isolation:

1. **Repository Tests**
   - Test each repository method with mock database
   - Verify correct SQL queries are generated
   - Test error handling for database failures

2. **Service Tests**
   - Test service methods with mock repositories
   - Verify business logic correctness
   - Test error handling and validation

3. **Endpoint Tests**
   - Test API endpoints with mock services
   - Verify request/response schemas
   - Test authentication and authorization

### Property-Based Testing

Property-based tests will verify universal properties across many inputs using **Hypothesis** (Python property-based testing library):

1. **Configuration**
   - Minimum 100 iterations per property test
   - Use Hypothesis strategies for generating test data
   - Shrink failing examples to minimal reproducible cases

2. **Test Tagging**
   - Each property test tagged with: `# Feature: celery-repository-integration, Property N: <property_text>`
   - Example: `# Feature: celery-repository-integration, Property 1: Task Dispatch Serialization`

3. **Property Test Coverage**
   - Property 1: Generate random task arguments, verify all are serializable
   - Property 3: Generate random jobs with various keyword/engine combinations, verify correct task count
   - Property 5: Generate random task completions, verify chunk counter invariant
   - Property 6: Generate random chunk counts, verify progress calculation
   - Property 11: Generate random validation levels, verify correct task selection
   - Property 16: Generate random requests with/without auth, verify 401 responses
   - Property 17: Generate random user/job combinations, verify 403 for unauthorized access

4. **Integration with Unit Tests**
   - Property tests complement unit tests by testing general behavior
   - Unit tests verify specific examples and edge cases
   - Together they provide comprehensive coverage

### Integration Testing

Integration tests will verify end-to-end workflows:

1. **Job Lifecycle Test**
   - Create job → Start job → Monitor progress → Complete job
   - Verify database state at each step
   - Verify notifications are created

2. **Job Cancellation Test**
   - Create job → Start job → Stop job
   - Verify tasks are revoked
   - Verify job status is updated

3. **Validation Workflow Test**
   - Create job → Download images → Validate images
   - Verify validation results are stored
   - Test all validation levels

4. **Error Scenario Tests**
   - Test authentication failures
   - Test authorization failures
   - Test invalid job states
   - Test task dispatch failures

### Test Database Setup

- Use test database with same schema as production
- Reset database between tests
- Use fixtures for common test data (users, jobs, images)
- Mock Celery task dispatch to avoid actual task execution

### Mocking Strategy

1. **Mock Celery Tasks**: Use `unittest.mock` to mock task.delay() calls
2. **Mock Database**: Use SQLAlchemy test fixtures with in-memory or test database
3. **Mock Supabase Auth**: Mock JWT token verification for authentication tests
4. **Mock Redis**: Use fakeredis for testing rate limiting

## Database Session Management

### Critical Rules

1. **Never Pass Sessions to Tasks**
   ```python
   # ❌ WRONG
   task.delay(session=session)
   
   # ✅ CORRECT
   task.delay(job_id=str(job.id))
   ```

2. **Tasks Create Own Sessions**
   ```python
   # In task implementation
   async def task_impl(job_id: str):
       async with get_session() as session:
           repository = CrawlJobRepository(session)
           await repository.update_progress(job_id, 50)
   ```

3. **API Endpoints Use Dependency Injection**
   ```python
   @router.post("/jobs/{job_id}/start")
   async def start_job(
       job_id: int,
       session: AsyncSession = Depends(get_session)
   ):
       # Session automatically managed by FastAPI
   ```

### Session Lifecycle

1. **API Request**: Session created by FastAPI dependency
2. **Service Layer**: Uses injected session for database operations
3. **Task Dispatch**: Only serializable data passed to tasks
4. **Task Execution**: Task creates its own session if needed
5. **Session Cleanup**: FastAPI automatically closes session after request

### Connection Pooling

- SQLAlchemy connection pool configured with:
  - pool_size: 10 (concurrent connections)
  - max_overflow: 20 (additional connections under load)
  - pool_timeout: 30 seconds
  - pool_recycle: 3600 seconds (1 hour)

## Security Considerations

### Authentication

- All endpoints require valid Supabase JWT token
- Token verified using Supabase service role key
- User ID extracted from token claims
- Invalid tokens return 401 Unauthorized

### Authorization

- Resource ownership verified before operations
- Users can only access their own jobs and images
- Admin users can access all resources (future enhancement)
- Unauthorized access returns 403 Forbidden

### Input Validation

- All request data validated using Pydantic schemas
- SQL injection prevented by SQLAlchemy parameterized queries
- Path parameters validated for type and format
- Query parameters validated for allowed values

### Rate Limiting

- API endpoints rate limited using FastAPI-Limiter + Redis
- Celery tasks have built-in rate limits
- Rate limit headers included in responses
- Rate limit exceeded returns 429 Too Many Requests

### Data Privacy

- Row Level Security (RLS) enforced at database level
- Backend uses service role key but implements application-level authorization
- Sensitive data (task results) only accessible to job owner
- Audit logging for all operations

## Performance Considerations

### Task Dispatch Optimization

- Batch task dispatch to reduce Redis round trips
- Use Celery's `group()` for parallel task execution
- Implement task result caching to avoid duplicate processing

### Database Query Optimization

- Use eager loading for related entities
- Implement pagination for large result sets
- Add database indexes on frequently queried columns:
  - crawl_jobs.user_id
  - crawl_jobs.status
  - images.crawl_job_id
  - images.is_valid

### Caching Strategy

- Cache job progress in Redis (TTL: 60 seconds)
- Cache validation results in Redis (TTL: 300 seconds)
- Invalidate cache on job status changes

### Monitoring

- Track task execution times
- Monitor database connection pool usage
- Alert on high error rates
- Track API endpoint response times

## Deployment Considerations

### Environment Variables

```bash
# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# Supabase Configuration
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=xxx

# Application Configuration
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### Celery Worker Configuration

```bash
# Start worker with concurrency
celery -A celery_core.app worker \
  --loglevel=info \
  --concurrency=4 \
  --max-tasks-per-child=1000

# Start beat scheduler
celery -A celery_core.app beat --loglevel=info
```

### Health Checks

- API health endpoint: `/health`
- Checks database connectivity
- Checks Redis connectivity
- Checks Celery worker availability
- Returns 200 if all healthy, 503 if any unhealthy

### Scaling Considerations

- Horizontal scaling: Add more Celery workers
- Vertical scaling: Increase worker concurrency
- Database scaling: Use read replicas for queries
- Redis scaling: Use Redis Cluster for high availability

## Future Enhancements

1. **Webhook Support**: Allow users to register webhooks for job events
2. **Real-time Progress**: Implement WebSocket endpoint for live progress updates
3. **Task Prioritization**: Allow users to set job priority
4. **Scheduled Jobs**: Support cron-like scheduling for recurring jobs
5. **Job Templates**: Allow users to save and reuse job configurations
6. **Advanced Validation**: Add custom validation rules and filters
7. **Batch Operations**: Support bulk job creation and management
8. **Export Formats**: Add more dataset export formats (COCO, YOLO, etc.)
