# Design Document: PixCrawler Project Completion Audit

## Overview

This design document outlines the approach for completing the PixCrawler project audit and ensuring production readiness. The audit focuses on code cleanup, completion of missing implementations, adherence to best practices, and ensuring all components work correctly together.

The project is a monorepo using UV workspace configuration with 5 Python packages (backend, builder, utility, celery_core, validator) and a Next.js frontend. The audit will ensure consistency across all packages while maintaining the existing architecture decisions (shared Supabase database, Supabase Auth only, distributed task processing with Celery).

## Architecture

### Current Architecture

The PixCrawler application follows a shared database architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                     PixCrawler Platform                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐              ┌──────────────────┐     │
│  │   Frontend       │              │   Backend        │     │
│  │   Next.js 15     │◄────────────►│   FastAPI        │     │
│  │   React 19       │   REST API   │   Python 3.11+   │     │
│  │   Drizzle ORM    │              │   SQLAlchemy     │     │
│  └────────┬─────────┘              └────────┬─────────┘     │
│           │                                 │                │
│           │         ┌──────────────────────┴────┐           │
│           └────────►│  Shared Supabase          │◄──────────┘
│                     │  PostgreSQL Database      │           │
│                     └───────────────────────────┘           │
│                                                               │
│  ┌──────────────────┐              ┌──────────────────┐     │
│  │   Celery Workers │              │   Redis Broker   │     │
│  │   (Distributed)  │◄────────────►│   (Task Queue)   │     │
│  └──────────────────┘              └──────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Audit Scope

The audit covers:

1. **Root Level**: manage.py CLI, environment configuration, workspace dependencies
2. **Backend Package**: API endpoints, services, repositories, middleware, configuration
3. **SDK Package**: Python SDK implementation for API access
4. **Celery Core**: Task definitions, workflows, configuration
5. **Test Organization**: Test structure across all packages

## Components and Interfaces

### 1. Management CLI (manage.py)

**Purpose**: Provide command-line interface for database management, server control, and development tasks.

**Current State**: Contains factory data generation functions copied from external sources that are not needed for production.

**Target State**: Clean CLI with only production-relevant commands.

**Interface**:
```python
# Commands to keep:
- createsuperuser: Create superuser account
- promote: Promote user to superuser
- create_tables: Create database tables
- drop_tables: Drop database tables
- reset_db: Reset database
- reset_password: Reset user password
- check_env: Validate environment
- seed_data: Create sample data
- clean_db: Clean orphaned types
- verify_setup: Verify setup
- stamp_alembic: Stamp Alembic version
- check_db: Check database connection
- tables: Display table information
- start: Start server
- stop: Stop server
- curl: Check server status
- clean: Clean up project

# Commands to remove:
- create_factory_mfg: Factory manufacturing data
- delete_factory_mfg: Delete factory manufacturing data
- create_factory_customers: Factory customer data
- delete_factory_customers: Delete factory customer data
```

### 2. API Endpoints (backend/api/v1/endpoints/)

**Purpose**: Provide RESTful API for frontend and SDK access.

**Current State**: Endpoints exist but may lack comprehensive documentation and consistent patterns.

**Target State**: All endpoints documented with authorization requirements, following professional FastAPI patterns.

**Endpoint Categories**:
- Authentication: `/api/v1/auth/*`
- Users: `/api/v1/users/*`
- Projects: `/api/v1/projects/*`
- Crawl Jobs: `/api/v1/jobs/*`
- Datasets: `/api/v1/datasets/*`
- Storage: `/api/v1/storage/*`
- Validation: `/api/v1/validation/*`
- Health: `/health`

**Documentation Requirements**:
- OpenAPI tags for grouping
- Comprehensive descriptions
- Authorization requirements in docstrings
- Request/response examples
- Error responses

### 3. Environment Configuration

**Purpose**: Manage configuration across development, testing, and production environments.

**Current State**: Multiple .env files with potential inconsistencies.

**Target State**: Consistent configuration with clear separation of concerns.

**Configuration Structure**:
```
Root Level (.env):
- PIXCRAWLER_DEVELOPMENT_MODE
- LEMONSQUEEZY_* (payment processing)

Backend (.env):
- ENVIRONMENT, DEBUG, HOST, PORT, LOG_LEVEL
- SUPABASE_* (auth and database)
- CORS settings
- DATABASE_* (connection pooling)
- REDIS_* (caching and rate limiting)
- CELERY_* (task queue)
- STORAGE_* (file storage configuration)
```

### 4. SDK (sdk/pixcrawler/)

**Purpose**: Provide simple Python SDK for loading datasets with minimal API surface.

**Current State**: Basic `load_dataset()` function exists with authentication and download logic.

**Target State**: Complete SDK with simple module-level API and additional dataset operations.

**SDK Design Philosophy**: 
- **Simple module-level API** (not class-based for the user faced apis but the implementation internally can used classes then wrapps to functions)
- **Minimal function calls** for common operations
- **Environment-based authentication** with optional override
- **In-memory dataset loading** for ML workflows

**Current Implementation**:
```python
# sdk/pixcrawler/__init__.py
from .core import Dataset, load_dataset

# sdk/pixcrawler/core.py
class Dataset:
    """In-memory dataset with iteration support."""
    def __init__(self, data: List[Any]):
        self.data = data
    
    def __iter__(self):
        for item in self.data:
            yield item

def load_dataset(dataset_id: str, config: Optional[Dict[str, Any]] = None) -> Dataset:
    """Load dataset from PixCrawler service.
    
    Authentication:
        - config["api_key"] (highest priority)
        - SERVICE_API_KEY environment variable
        - SERVICE_API_TOKEN environment variable
    
    Args:
        dataset_id: UUID of the dataset
        config: Optional config with 'api_key' and 'base_url'
    
    Returns:
        Dataset object with loaded data
    """
```

**Target API (Simple Module-Level Functions)**:
```python
import pixcrawler as pix

# Authentication (optional - uses env vars by default)
pix.auth(token="your_api_key")  # Sets global auth for session

# Load dataset into memory
wildlife_dataset = pix.load_dataset("dataset-id-123")

# Iterate over items
for item in wildlife_dataset:
    print(item)

# List available datasets
datasets = pix.list_datasets()  # Returns list of dataset metadata

# Get dataset metadata without downloading
metadata = wilde_life_dataset.metadata
print(f"Images: {metadata['image_count']}, Size: {metadata['size_mb']}MB")

# Download dataset to file (without loading into memory)
wild_life_dataset.download(output_path="./wildlife.zip")
```

**Functions to Implement**:

1. **`auth(token: str, base_url: str = None)`**
   - Set global authentication token for the session
   - Optional base_url override for testing
   - Stores in module-level variable

2. **`list_datasets(page: int = 1, size: int = 20) -> List[dict]`**
   - List user's datasets with pagination
   - Returns list of dataset metadata dicts
   - Uses stored auth token or env vars

3. **`get_dataset_info(dataset_id: str) -> dict`**
   - Get dataset metadata without downloading
   - Returns dict with image_count, size_mb, labels, etc.
   - Lightweight alternative to load_dataset

4. **`download_dataset(dataset_id: str, output_path: str) -> str`**
   - Download dataset archive to local file
   - Does NOT load into memory
   - Returns path to downloaded file
   - Useful for large datasets

5. **`load_dataset(dataset_id: str, config: dict = None) -> Dataset`**
   - Already implemented
   - Enhance to use global auth if available
   - Keep existing retry logic and memory guardrails

**Module-Level State**:
```python
# sdk/pixcrawler/core.py
_global_auth_token: Optional[str] = None
_global_base_url: str = "https://api.pixcrawler.com/v1"

def auth(token: str, base_url: str = None):
    """Set global authentication for the session."""
    global _global_auth_token, _global_base_url
    _global_auth_token = token
    if base_url:
        _global_base_url = base_url
```

**Error Handling**:
- `ValueError`: Authentication missing or invalid
- `ConnectionError`: Download failed after retries
- `TimeoutError`: Request timeout
- `RuntimeError`: API errors, memory limit exceeded

**Note**: The SDK intentionally does NOT include:
- Project management
- Crawl job creation/management
- User management
- Validation operations

This keeps the SDK focused on the primary use case: loading datasets for ML workflows.

### 5. Celery Tasks and Workflows

**Purpose**: Handle background processing for image crawling, validation, and dataset generation.

**Current State**: Tasks exist but may not be consistently integrated across endpoints and services.

**Target State**: All background operations use celery_core package with proper task definitions, and all endpoints/services correctly dispatch Celery tasks.

**Task Categories**:
- Image Crawling: `builder/tasks.py`
- Image Validation: `validator/tasks.py`
- Dataset Processing: `backend/services/dataset_processing_pipeline.py`
- Job Orchestration: `backend/services/job_orchestrator.py`

**Celery Integration Requirements**:

1. **All tasks must be defined in celery_core or package-specific tasks.py**
   - Import from `celery_core.app` for task decorator
   - Register tasks properly in Celery app
   - Use consistent task naming: `package.module.function_name`

2. **Endpoints must dispatch tasks, not execute directly**
   ```python
   # WRONG - Synchronous execution in endpoint
   @router.post("/jobs/{job_id}/start")
   async def start_job(job_id: str):
       result = process_crawl_job(job_id)  # Blocks request
       return result
   
   # CORRECT - Async task dispatch
   @router.post("/jobs/{job_id}/start")
   async def start_job(job_id: str):
       task = process_crawl_job.delay(job_id)  # Returns immediately
       return {"task_id": task.id, "status": "started"}
   ```

3. **Services must use task dispatch for long-running operations**
   ```python
   # In backend/services/crawl_job.py
   from builder.tasks import process_crawl_job_task
   
   async def start_crawl_job(job_id: str):
       # Update job status to "running"
       await job_repository.update(job_id, status="running")
       
       # Dispatch Celery task
       task = process_crawl_job_task.delay(job_id)
       
       # Store task ID for tracking
       await job_repository.update(job_id, task_ids=[task.id])
       
       return {"task_id": task.id}
   ```

4. **Task status tracking**
   - Store Celery task IDs in database (crawl_jobs.task_ids)
   - Provide endpoints to check task status
   - Update job status based on task completion

**Best Practices**:
- Task naming: `package.module.function_name`
- Retry logic: `@task(bind=True, max_retries=3, default_retry_delay=60)`
- Exponential backoff: `retry(countdown=2 ** self.request.retries)`
- Logging: Use utility/logging_config
- Result backend: Redis for task results
- Canvas workflows: Use chain, group, chord for complex workflows
- Task routing: Route tasks to appropriate queues based on priority/type

**Audit Checklist**:
- [ ] All crawl job operations dispatch Celery tasks
- [ ] All validation operations dispatch Celery tasks
- [ ] All dataset processing operations dispatch Celery tasks
- [ ] No long-running operations execute synchronously in endpoints
- [ ] All tasks are properly registered in celery_core
- [ ] Task IDs are stored and tracked in database
- [ ] Task status endpoints are implemented
- [ ] Error handling and retry logic is consistent

## Data Models

### Existing Models (No Changes Required)

The database schema is already defined and follows the shared Supabase database architecture:

**Core Tables**:
- profiles: User profiles (extends Supabase auth.users)
- projects: Project organization
- crawl_jobs: Image crawling tasks with chunk tracking
- images: Crawled image metadata

**User Management**:
- activity_logs: User activity tracking
- api_keys: Programmatic access keys
- notifications: User notifications

**Billing**:
- credit_accounts: User billing and credits
- credit_transactions: Transaction history
- notification_preferences: User notification settings
- usage_metrics: Daily usage tracking

All models are defined in:
- Frontend: `frontend/lib/db/schema.ts` (Drizzle ORM - source of truth)
- Backend: `backend/models/*.py` (SQLAlchemy - synchronized with Drizzle)

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: CLI Command Completeness
*For any* CLI command execution, if the command is not a factory command, then it should execute successfully without referencing removed factory functions
**Validates: Requirements 1.2**

### Property 2: API Endpoint Documentation Completeness
*For any* API endpoint that requires authentication, the endpoint's docstring and OpenAPI metadata should contain authorization requirements
**Validates: Requirements 2.1, 2.2, 2.3**

### Property 3: Environment Variable Naming Consistency
*For any* environment variable defined in .env files, the variable name should follow the prefix pattern (e.g., STORAGE_, CELERY_, DATABASE_)
**Validates: Requirements 3.3**

### Property 4: Environment File Structure Consistency
*For any* .env.example file, the keys in the example file should match the structure of the corresponding .env file
**Validates: Requirements 3.4**

### Property 5: Celery Task Naming Convention
*For any* Celery task defined in the codebase, the task name should follow the pattern `package.module.function_name`
**Validates: Requirements 5.1**

### Property 6: Celery Task Retry Configuration
*For any* Celery task that can fail, the task should have retry logic configured with max_retries and retry delay
**Validates: Requirements 5.3**

### Property 7: Celery Task Logging
*For any* Celery task execution, the task should log progress and errors using the centralized logging system
**Validates: Requirements 5.4**

### Property 8: SDK Dataset Method Completeness
*For any* dataset-related API endpoint in the backend, there should be a corresponding SDK method in the PixCrawlerClient class
**Validates: Requirements 7.1**

### Property 9: SDK Authentication Handling
*For any* SDK method call that requires authentication, the SDK should automatically include the API key or token in the request
**Validates: Requirements 7.2**

### Property 10: SDK Error Handling
*For any* API error response, the SDK should raise an appropriate custom exception with error details
**Validates: Requirements 7.3**

### Property 11: SDK Documentation Completeness
*For any* SDK method, the method's docstring should include usage examples
**Validates: Requirements 7.4**

### Property 12: Repository Pattern Usage
*For any* service class method that accesses the database, the method should use repository classes rather than direct database access
**Validates: Requirements 9.1**

### Property 13: Repository Inheritance
*For any* repository class defined in the codebase, the class should inherit from BaseRepository
**Validates: Requirements 9.2**

### Property 14: No Raw SQL in Services
*For any* service class file, the file should not contain raw SQL strings (SELECT, INSERT, UPDATE, DELETE)
**Validates: Requirements 9.3**

### Property 15: Repository CRUD Completeness
*For any* repository class, the class should provide standard CRUD operations (create, read, update, delete)
**Validates: Requirements 9.4**

### Property 16: Exception Handling Centralization
*For any* custom exception raised in the codebase, the exception should be defined in `backend/core/exceptions.py` and handled by centralized exception handlers
**Validates: Requirements 10.2**

### Property 17: Endpoint Response Helper Usage
*For any* API endpoint that returns a success response, the endpoint should use common response helpers rather than constructing responses manually
**Validates: Requirements 10.5**

### Property 18: Celery Task Dispatch in Endpoints
*For any* endpoint that performs long-running operations (crawl jobs, validation, dataset processing), the endpoint should dispatch a Celery task and return immediately rather than executing synchronously
**Validates: Requirements 5.1, 5.2**

### Property 19: Celery Task Registration
*For any* Celery task defined in the codebase, the task should be properly registered in the celery_core app and importable
**Validates: Requirements 5.1**

## Error Handling

### Exception Hierarchy

The system uses a layered exception hierarchy defined in `backend/core/exceptions.py`:

```python
AppException (base)
├── DatabaseException
├── AuthenticationException
│   ├── UnauthorizedException
│   └── AuthorizationException
├── ValidationException
├── NotFoundException
├── ConflictException
├── RateLimitException
├── InvalidConfigurationException
└── FeatureDisabledException
```

### Error Response Format

All API errors follow a consistent format:

```json
{
  "message": "Error Type",
  "details": [
    {
      "detail": "Specific error message",
      "error_code": "ERROR_CODE",
      "field": "field_name"
    }
  ],
  "request_id": "uuid"
}
```

### SDK Error Handling

The SDK wraps API errors in custom exceptions:

```python
class PixCrawlerError(Exception):
    """Base exception for SDK errors."""
    
class APIError(PixCrawlerError):
    """API returned an error response."""
    def __init__(self, status_code: int, message: str, details: list = None):
        self.status_code = status_code
        self.message = message
        self.details = details or []
        
class AuthenticationError(PixCrawlerError):
    """Authentication failed."""
    
class ValidationError(PixCrawlerError):
    """Request validation failed."""
    
class NotFoundError(PixCrawlerError):
    """Resource not found."""
    
class RateLimitError(PixCrawlerError):
    """Rate limit exceeded."""
```

## Testing Strategy

### Dual Testing Approach

The project uses both unit testing and property-based testing:

**Unit Tests**:
- Specific examples that demonstrate correct behavior
- Edge cases and error conditions
- Integration points between components
- Located in `backend/tests/`, `sdk/tests/`, etc.

**Property-Based Tests**:
- Universal properties that should hold across all inputs
- Uses `hypothesis` library for Python
- Minimum 100 iterations per property test
- Tagged with property number from design document

### Test Organization

```
tests/
├── unit/              # Unit tests
│   ├── api/          # API endpoint tests
│   ├── services/     # Service layer tests
│   ├── repositories/ # Repository tests
│   └── models/       # Model tests
├── integration/       # Integration tests
│   ├── test_crawl_job_cancellation.py
│   ├── test_storage_integration.py
│   └── test_metrics_integration.py
└── conftest.py       # Shared fixtures
```

### Testing Requirements

1. **Unit Tests**: Cover specific examples, edge cases, and error conditions
2. **Property Tests**: Verify universal properties across all inputs
3. **Integration Tests**: Test component interactions
4. **Coverage**: Minimum 80% coverage for critical paths
5. **Test Isolation**: Each test should be independent
6. **Fixtures**: Use pytest fixtures for common setup
7. **Mocking**: Mock external dependencies (Supabase, Redis, Azure)

### Property-Based Testing Configuration

- **Library**: `hypothesis` for Python
- **Iterations**: Minimum 100 per property test
- **Tagging**: Each property test tagged with `# Property X: description`
- **Strategies**: Custom strategies for domain objects (projects, jobs, images)

Example property test:

```python
from hypothesis import given, strategies as st
import pytest

# Property 8: SDK Dataset Method Completeness
@given(endpoint=st.sampled_from(get_dataset_api_endpoints()))
def test_sdk_has_method_for_dataset_endpoint(endpoint):
    """For any dataset API endpoint, there should be a corresponding SDK method.
    
    Property 8: SDK Dataset Method Completeness
    Validates: Requirements 7.1
    """
    sdk_client = PixCrawlerClient(token="test_token")
    method_name = endpoint_to_method_name(endpoint)
    assert hasattr(sdk_client, method_name), \
        f"SDK missing method {method_name} for endpoint {endpoint}"
```

Example Celery integration test:

```python
# Property 18: Celery Task Dispatch in Endpoints
def test_crawl_job_start_dispatches_celery_task():
    """Starting a crawl job should dispatch a Celery task, not execute synchronously.
    
    Property 18: Celery Task Dispatch
    Validates: Requirements 5.1, 5.2
    """
    from unittest.mock import patch
    
    with patch('builder.tasks.process_crawl_job_task.delay') as mock_delay:
        mock_delay.return_value.id = "task-123"
        
        response = client.post(f"/api/v1/jobs/{job_id}/start")
        
        assert response.status_code == 200
        assert mock_delay.called, "Celery task was not dispatched"
        assert "task_id" in response.json()
```

## Implementation Plan

The implementation will follow these phases:

### Phase 1: Cleanup (Priority: High)
1. Remove factory functions from manage.py
2. Remove TODO statements
3. Clean up unused imports
4. Remove placeholder implementations

### Phase 2: Environment Configuration (Priority: High)
1. Audit all .env files
2. Ensure consistency between .env and .env.example
3. Document all environment variables
4. Add production dependencies (Gunicorn)

### Phase 3: API Documentation (Priority: High)
1. Add authorization requirements to all endpoint docstrings
2. Add OpenAPI tags and metadata
3. Ensure comprehensive descriptions
4. Test all endpoints with Postman

### Phase 4: SDK Completion (Priority: Medium)
1. Implement all API methods in SDK
2. Add authentication handling
3. Add error handling with custom exceptions
4. Add usage examples to docstrings
5. Write SDK tests

### Phase 5: Celery Best Practices (Priority: Medium)
1. Audit all Celery tasks
2. Add retry logic where missing
3. Ensure proper logging
4. Verify workflow patterns
5. Test task execution

### Phase 6: Test Organization (Priority: Low)
1. Reorganize test files by type
2. Ensure all tests pass
3. Verify coverage reporting
4. Document test patterns

### Phase 7: Repository Pattern (Priority: Low)
1. Audit service layer for direct database access
2. Ensure all repositories inherit from BaseRepository
3. Verify CRUD operations
4. Remove raw SQL from services

### Phase 8: Professional FastAPI Patterns (Priority: Medium)
1. Verify settings structure
2. Ensure centralized exception handling
3. Check types.py usage
4. Verify middleware setup
5. Add response helpers
6. Verify health endpoints
7. Test CORS configuration
8. Verify rate limiting

## Security Considerations

### Authentication
- Supabase Auth only (no custom JWT)
- Service role key for backend (bypasses RLS)
- Anon key for frontend (with RLS)
- API keys for SDK access

### Authorization
- Row Level Security (RLS) policies in database
- Application-level authorization in backend
- Superuser checks for admin endpoints

### Secrets Management
- Environment variables (never in code)
- Azure Key Vault for production
- .env.local for development (gitignored)

### Rate Limiting
- Redis-backed rate limiting
- Per-endpoint rate limits
- Per-user rate limits
- API key rate limits

## Performance Considerations

### Database
- Connection pooling (asyncpg)
- Indexed columns for fast lookups
- Pagination for large result sets
- Eager loading to avoid N+1 queries

### Caching
- Redis for rate limiting
- Response caching for expensive queries
- Session storage

### Background Jobs
- Chunk-based processing
- Parallel downloads
- Progress caching for resume capability

## Deployment Considerations

### Production Dependencies
- Gunicorn: Production WSGI server
- uvicorn[standard]: ASGI server with performance extras
- Redis: Caching and task queue
- PostgreSQL: Database (via Supabase)

### Environment Variables
All production environment variables must be set:
- ENVIRONMENT=production
- DEBUG=false
- SUPABASE_* (from Supabase dashboard)
- DATABASE_URL (Supabase PostgreSQL)
- REDIS_URL (managed Redis)
- STORAGE_* (Azure credentials)

### Health Checks
- Simple: `/health` - Basic health check
- Detailed: `/health/detailed` - Check all services (database, Redis, Celery)

### Monitoring
- Azure Monitor (Application Insights)
- Structured logging with Loguru
- Request ID tracking
- Error tracking and alerting

## Success Criteria

1. **Code Quality**: No TODO statements, no placeholder implementations
2. **Documentation**: All endpoints documented with authorization requirements
3. **Configuration**: Consistent environment configuration across all packages
4. **Dependencies**: All production dependencies installed and working
5. **SDK**: Complete SDK with all API methods implemented
6. **Tests**: All tests passing, proper organization
7. **Patterns**: Following professional FastAPI patterns throughout
8. **Deployment**: Ready for production deployment with health checks and monitoring
