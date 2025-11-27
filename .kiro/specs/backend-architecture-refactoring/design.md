# Design Document

## Overview

This design document outlines the architectural approach for refactoring three critical areas of the PixCrawler backend: utility package configuration management, API endpoint standardization, and repository pattern enforcement. The refactoring will improve code maintainability, consistency, and adherence to clean architecture principles while maintaining backward compatibility.

### Goals

1. **Unified Configuration**: Create a centralized, type-safe configuration system for the utility package that consolidates compression and logging settings
2. **API Consistency**: Standardize all backend API endpoints to follow established patterns for documentation, typing, and structure
3. **Clean Architecture**: Enforce proper separation of concerns between API, service, and repository layers
4. **Test Coverage**: Achieve minimum 85% test coverage for utility package and comprehensive architecture validation
5. **Backward Compatibility**: Maintain existing functionality during transition with deprecation warnings where needed

### Design Principles

- **Type Safety**: Leverage Pydantic V2 for runtime validation and type checking
- **Composition Over Inheritance**: Use nested configuration objects rather than deep inheritance hierarchies
- **Single Responsibility**: Each layer (API, service, repository) has one clear purpose
- **Dependency Injection**: Use FastAPI's dependency system for loose coupling
- **Test-Driven Development**: Write tests before implementation to ensure correctness
- **Documentation First**: Complete docstrings and OpenAPI documentation for all public APIs

## Architecture

### System Context

The PixCrawler monorepo consists of multiple packages with the utility package serving as a shared foundation. The backend package implements a three-layer architecture (API, Service, Repository) that needs standardization.

### Backend Layer Architecture

The backend follows a clean architecture pattern with clear separation of concerns:

**Layer 1: API (Endpoints)**
- HTTP request/response handling
- Input validation using Pydantic schemas
- OpenAPI documentation
- Authentication/authorization
- Response serialization

**Layer 2: Service (Business Logic)**
- Business rules and validation
- Workflow orchestration
- Cross-repository coordination
- Error handling and exceptions
- Data transformation

**Layer 3: Repository (Data Access)**
- CRUD operations
- Query construction
- Database transactions
- No business logic

**Layer 4: Models (SQLAlchemy)**
- Database schema definition
- Relationships
- Table mappings


## Components and Interfaces

### Component 1: Unified Utility Configuration

#### Purpose
Provide a centralized, type-safe configuration system for the utility package that consolidates compression and logging settings with environment variable support.

#### Structure

**UtilitySettings (Main Configuration Class)**
- Consolidates all utility package configuration
- Uses Pydantic V2 BaseSettings with SettingsConfigDict
- Environment prefix: `PIXCRAWLER_UTILITY_`
- Nested composition of sub-package configs
- Cross-package validation via model_validator

**CompressionSettings (Nested Configuration)**
- Inherits from existing `utility/compress/config.py`
- Maintains all current compression options
- Includes nested ArchiveSettings
- Auto-detection of worker count

**LoggingSettings (Nested Configuration)**
- Inherits from existing `utility/logging_config/config.py`
- Maintains all current logging options
- Environment-specific defaults
- Support for development, production, testing

#### Key Interfaces

```python
# Factory Functions
get_utility_settings() -> UtilitySettings  # Cached singleton
get_preset_config(preset_name: str) -> UtilitySettings  # Preset configs

# Configuration Presets
CONFIG_PRESETS = {
    'default': Default configuration,
    'production': Production-optimized settings,
    'development': Development-friendly settings,
    'testing': Test environment settings
}

# Serialization
to_dict() -> Dict[str, Any]  # Convert to dictionary
from_dict(config_dict: Dict) -> UtilitySettings  # Create from dictionary
```

#### Integration Strategy

1. **Backward Compatibility**: Existing sub-package configs remain functional
2. **Optional Migration**: Sub-packages can optionally use unified config
3. **Environment Variables**: Support both old and new prefixes during transition
4. **Deprecation Warnings**: DONT Add warnings just FORCE to use the new way


### Component 2: Standardized API Endpoints

#### Purpose
Ensure all backend API endpoints follow consistent patterns for route definition, response typing, OpenAPI documentation, and error handling.

#### Standard Endpoint Pattern

**Route Definition**
- Use `"/"` or `"/resource-name"` for list endpoints (NOT empty string `""`)
- Consistent path naming: `"/{id}"` not `"/{resource_id}"`
- RESTful conventions: GET for read, POST for create, PATCH for update, DELETE for delete

**Response Models**
- All endpoints must have `response_model` parameter
- Use Pydantic schemas from `backend/schemas/`
- Return typed responses, not generic dictionaries
- List endpoints return `{data: [], meta: {}}` structure

**OpenAPI Documentation**
- `summary`: Brief description (< 50 chars)
- `description`: Detailed explanation (2-3 sentences)
- `response_description`: Describes the response content
- `operation_id`: camelCase format (e.g., `"listNotifications"`)
- `responses`: Dict with 200 example and common error responses using `get_common_responses()`

**Docstrings**
- Detailed description paragraph
- Authentication requirements (e.g., "**Authentication Required:** Bearer token")
- All parameters documented with types
- Return type documentation
- Possible exceptions listed

**Type Hints**
- All parameters must have type hints
- Return type must match `response_model`
- Use type aliases from `backend/api/types.py` (CurrentUser, DBSession, etc.)

#### Endpoint Checklist Template

```python
@router.get(
    "/resources",  # ✅ Use "/" or "/resource-name"
    response_model=ResourceListResponse,  # ✅ Typed response
    summary="List Resources",
    description="Retrieve all resources with pagination.",
    response_description="List of resources with metadata",
    operation_id="listResources",  # ✅ camelCase
    responses={
        200: {
            "description": "Successfully retrieved resources",
            "content": {
                "application/json": {
                    "example": {"data": [...], "meta": {...}}
                }
            }
        },
        **get_common_responses(401, 500)
    }
)
async def list_resources(
    current_user: CurrentUser,
    service: ResourceServiceDep,
) -> ResourceListResponse:  # ✅ Typed return
    """
    List all resources for the current user.
    
    Detailed description of what this endpoint does.
    
    **Authentication Required:** Bearer token
    
    Args:
        current_user: Current authenticated user (injected)
        service: Resource service instance (injected)
    
    Returns:
        ResourceListResponse with list of resources and metadata
    
    Raises:
        HTTPException: 401 if authentication fails
        HTTPException: 500 if database query fails
    """
    pass
```


### Component 3: Repository Pattern Enforcement

#### Purpose
Enforce clean separation of concerns between API, service, and repository layers to improve testability, maintainability, and adherence to SOLID principles.

#### Layer Responsibilities

**API Layer (Endpoints) - ALLOWED**
- HTTP request/response handling
- Input validation using Pydantic schemas
- Authentication and authorization checks
- Response serialization
- OpenAPI documentation

**API Layer (Endpoints) - NOT ALLOWED**
- Business logic
- Database queries
- Data transformation
- Direct session access

**Service Layer - ALLOWED**
- Business rules and validation
- Workflow orchestration
- Cross-repository coordination
- Error handling and custom exceptions
- Data transformation and aggregation

**Service Layer - NOT ALLOWED**
- Direct database access via AsyncSession
- HTTP concerns (request/response handling)
- Raw SQL queries

**Repository Layer - ALLOWED**
- CRUD operations
- Query construction and execution
- Database transaction management
- Data access optimization

**Repository Layer - NOT ALLOWED**
- Business logic
- HTTP concerns
- Complex data transformations
- Workflow orchestration

#### Correct Pattern Example

```python
# 1. Repository (Data Access Only)
class ProjectRepository(BaseRepository[Project]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Project)
    
    async def get_by_user(self, user_id: UUID) -> List[Project]:
        """Get all projects for a user."""
        result = await self.session.execute(
            select(Project).where(Project.user_id == user_id)
        )
        return result.scalars().all()

# 2. Service (Business Logic)
class ProjectService:
    def __init__(self, repository: ProjectRepository):
        self.repository = repository  # ✅ Depends on repository, not session
    
    async def get_projects(self, user_id: UUID) -> List[Project]:
        """Get projects with business logic."""
        projects = await self.repository.get_by_user(user_id)
        # Apply business rules, transformations, etc.
        return projects

# 3. Dependency Injection
async def get_project_service(
    session: AsyncSession = Depends(get_session)
) -> ProjectService:
    """Create service with repository."""
    repository = ProjectRepository(session)
    return ProjectService(repository)  # ✅ Inject repository into service

# 4. API Endpoint
@router.get("/projects")
async def list_projects(
    current_user: CurrentUser = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),  # ✅ Use service
) -> ProjectListResponse:
    """List projects."""
    projects = await service.get_projects(current_user["user_id"])
    return ProjectListResponse(data=projects)
```

#### Anti-Patterns to Avoid

```python
# ❌ WRONG: Service with direct session
class BadService:
    def __init__(self, session: AsyncSession):
        self.session = session  # ❌ Service shouldn't have session

# ❌ WRONG: Endpoint with business logic
@router.get("/items")
async def bad_endpoint(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Item))  # ❌ Query in endpoint
    return {"data": result.scalars().all()}

# ❌ WRONG: Repository with business logic
class BadRepository(BaseRepository[Item]):
    async def get_discounted_items(self):
        items = await self.get_all()
        for item in items:
            item.price = item.price * 0.9  # ❌ Business logic in repository
        return items
```


## Data Models

### Configuration Schema

#### UtilitySettings Structure

```python
{
    "compression": {
        "input_dir": "Path",
        "output_dir": "Path",
        "format": "webp | avif | png | jxl",
        "quality": "int (0-100)",
        "lossless": "bool",
        "workers": "int (0 = auto)",
        "archive": {
            "enable": "bool",
            "tar": "bool",
            "type": "zstd | zip | none",
            "level": "int (1-19)",
            "output": "Path"
        }
    },
    "logging": {
        "environment": "development | production | testing",
        "log_dir": "Path",
        "log_filename": "str",
        "error_filename": "str",
        "max_file_size": "str (e.g., '10 MB')",
        "backup_count": "int (1-100)",
        "console_level": "CRITICAL | ERROR | WARNING | INFO | DEBUG | TRACE",
        "file_level": "CRITICAL | ERROR | WARNING | INFO | DEBUG | TRACE",
        "use_json": "bool",
        "use_colors": "bool"
    }
}
```

### Response Models

#### Standard List Response Pattern

```python
class BaseListResponse(BaseModel):
    """Base response model for list endpoints."""
    data: List[Any]
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata (total, skip, limit, etc.)"
    )

class ResourceListResponse(BaseListResponse):
    """Typed list response for specific resource."""
    data: List[ResourceResponse]
    meta: Dict[str, Any] = Field(
        default_factory=lambda: {"total": 0, "skip": 0, "limit": 50}
    )
```

#### Standard Error Response

```python
{
    "detail": "Error message",
    "status_code": 400,
    "error_code": "VALIDATION_ERROR",  # Optional
    "errors": [  # Optional, for validation errors
        {
            "loc": ["body", "field_name"],
            "msg": "Field is required",
            "type": "value_error.missing"
        }
    ]
}
```

## Error Handling

### Configuration Validation Errors

Pydantic automatically raises ValidationError for invalid configuration:

```python
try:
    config = UtilitySettings(compression__quality=150)  # Invalid
except ValidationError as e:
    # Pydantic provides detailed error information
    # Including field location, message, and error type
    pass
```

### API Error Responses

All endpoints use FastAPI's HTTPException for consistent error handling:

```python
# 400 Bad Request - Invalid input
raise HTTPException(status_code=400, detail="Invalid request data")

# 401 Unauthorized - Authentication required
raise HTTPException(status_code=401, detail="Authentication required")

# 403 Forbidden - Insufficient permissions
raise HTTPException(status_code=403, detail="Not authorized")

# 404 Not Found - Resource doesn't exist
raise HTTPException(status_code=404, detail="Resource not found")

# 500 Internal Server Error - Unexpected error
raise HTTPException(status_code=500, detail="Internal server error")
```

### Repository Pattern Violations

Architecture tests will catch violations at test time:

```python
def test_services_dont_import_session():
    """Ensure services don't import AsyncSession directly."""
    for service_file in Path("backend/services").glob("*.py"):
        content = service_file.read_text()
        assert "AsyncSession" not in content or "TYPE_CHECKING" in content
```


## Testing Strategy

### Unit Tests

#### Configuration Tests (`utility/tests/test_config.py`)

**Test Coverage Areas:**
- Default settings initialization
- Environment variable loading with `PIXCRAWLER_UTILITY_` prefix
- Nested configuration composition (compression, logging, archive)
- Field validation rules (quality 0-100, compression level 1-19, etc.)
- Preset configurations (default, production, development, testing)
- Cross-package consistency validation
- Serialization (to_dict, from_dict)
- Error handling for invalid values

**Example Test Cases:**
```python
def test_default_settings()
def test_environment_variable_loading()
def test_nested_configuration_composition()
def test_validation_rules()
def test_preset_configurations()
def test_cross_package_consistency()
def test_serialization()
def test_invalid_configuration_raises_error()
```

#### Compression Tests (`utility/tests/test_compress.py`)

**Enhanced Test Coverage:**
- Corrupted image handling
- Permission errors (read/write denied)
- Large file handling (>100MB)
- Concurrent compression operations
- Error recovery and retry logic
- Memory usage under load
- Archive creation and extraction
- Format conversion edge cases

**Example Test Cases:**
```python
def test_corrupted_image_handling()
def test_permission_errors()
def test_large_file_handling()
def test_concurrent_compression()
def test_error_recovery()
def test_memory_usage()
def test_archive_creation()
```

### Integration Tests

#### Endpoint Integration Tests

**Test Coverage Areas:**
- Complete request/response flow
- Authentication and authorization
- Input validation
- Response serialization
- Error handling
- OpenAPI schema generation

**Example Test Cases:**
```python
async def test_list_resources_complete_flow(client, auth_headers)
async def test_create_resource_validation(client, auth_headers)
async def test_update_resource_authorization(client, auth_headers)
async def test_delete_resource_not_found(client, auth_headers)
async def test_openapi_schema_generation(client)
```

### Architecture Tests (`backend/tests/test_architecture.py`)

**Test Coverage Areas:**
- Services don't import AsyncSession directly
- Repositories extend BaseRepository
- Endpoints don't execute database queries
- Dependency injection pattern consistency
- Layer separation enforcement

**Example Test Cases:**
```python
def test_services_dont_import_async_session()
def test_repositories_extend_base_repository()
def test_endpoints_dont_have_queries()
def test_dependency_injection_pattern()
def test_no_business_logic_in_repositories()
def test_no_business_logic_in_endpoints()
```

### Test Coverage Goals

- **Utility Package**: ≥ 85% code coverage
- **Configuration Module**: 100% coverage (all validation paths)
- **API Endpoints**: ≥ 90% coverage (all routes tested)
- **Services**: ≥ 85% coverage (all business logic tested)
- **Repositories**: ≥ 80% coverage (all queries tested)
- **Architecture Tests**: 100% coverage (all constraints verified)


## Implementation Phases

### Phase 1: Utility Configuration (Week 1)

**Objective**: Create unified configuration system for utility package

**Deliverables:**
1. `utility/config.py` with `UtilitySettings` class
2. Updated `utility/compress/config.py` for optional integration
3. Updated `utility/logging_config/config.py` for optional integration
4. `utility/tests/test_config.py` with comprehensive tests
5. Enhanced `utility/tests/test_compress.py` with edge cases
6. Documentation updates in docstrings and README

**Success Criteria:**
- All tests pass with ≥ 85% coverage
- Backward compatibility maintained
- Environment variables work with new prefix
- Preset configurations functional
- No breaking changes to existing code

**Estimated Effort**: 3-4 days

### Phase 2: API Endpoint Standardization (Week 2)

**Objective**: Standardize all backend API endpoints to follow consistent patterns

**Deliverables:**
1. `backend/api/v1/ENDPOINT_STYLE_GUIDE.md` documentation
2. Audit report of all endpoints with violations documented
3. Fixed `backend/api/v1/endpoints/notifications.py`
4. Fixed all other non-compliant endpoints
5. Updated/created response models in `backend/schemas/`
6. Updated endpoint tests in `backend/tests/api/`
7. Verified OpenAPI schema generation

**Success Criteria:**
- All endpoints follow standard pattern
- OpenAPI schema validates correctly
- All endpoints have typed responses
- All endpoints have complete documentation
- All endpoint tests pass
- No breaking changes to API contracts

**Estimated Effort**: 4-5 days

### Phase 3: Repository Pattern Enforcement (Week 3)

**Objective**: Enforce proper separation of concerns across all layers

**Deliverables:**
1. `backend/REPOSITORY_PATTERN_AUDIT.md` with violations documented
2. Fixed services to remove direct session access
3. Fixed repositories to remove business logic
4. Fixed endpoints to remove business logic
5. Updated dependency injection patterns
6. `backend/tests/test_architecture.py` with architecture tests
7. Updated service and repository tests

**Success Criteria:**
- No services have direct `AsyncSession` parameters
- All repositories extend `BaseRepository`
- No endpoints have database queries
- All architecture tests pass
- Consistent dependency injection throughout
- No breaking changes to service interfaces

**Estimated Effort**: 4-5 days

### Phase 4: Documentation and Finalization (Week 4)

**Objective**: Complete documentation and ensure smooth deployment

**Deliverables:**
1. Updated README files for all affected packages
2. Migration guide for developers
3. API documentation updates
4. Architecture documentation
5. Final test coverage report
6. Deployment checklist
7. Summary report of all changes

**Success Criteria:**
- All documentation complete and accurate
- Migration guide tested by team
- Test coverage meets all goals
- All tests pass in CI/CD pipeline
- Ready for production deployment

**Estimated Effort**: 2-3 days


## Migration Strategy

### Backward Compatibility Approach

#### Configuration Migration

**Phase 1: Dual Support (Weeks 1-4)**
- Keep existing config files functional
- Add unified config as optional alternative
- Support both old and new environment variable prefixes
- No breaking changes

**Phase 2: Deprecation Warnings (Weeks 5-8)**
- Add deprecation warnings when old config methods are used
- Update documentation to recommend new unified config
- Provide migration examples

**Phase 3: Migration (Weeks 9-12)**
- Gradually migrate internal usage to unified config
- Monitor for any issues
- Keep old configs as thin wrappers

**Phase 4: Cleanup (After 3 months)**
- Remove deprecation warnings
- Old configs remain as compatibility layer indefinitely

#### API Migration

**No Breaking Changes Required**
- All changes are additive (better documentation, typing)
- Existing API contracts remain unchanged
- Response structure stays the same
- Only internal implementation improves

#### Repository Pattern Migration

**Incremental Refactoring**
- Refactor one service at a time
- Maintain existing service interfaces
- Add tests before refactoring each service
- Deploy incrementally with monitoring

### Rollout Plan

#### Week 1: Utility Configuration
- Deploy to development environment
- Monitor for configuration errors
- Validate environment variable loading
- Test backward compatibility
- Deploy to staging
- Deploy to production (low risk)

#### Week 2: API Endpoints
- Deploy to development environment
- Monitor API response times
- Validate OpenAPI schema generation
- Test with frontend integration
- Deploy to staging
- Deploy to production (low risk)

#### Week 3: Repository Pattern
- Deploy to development environment
- Monitor database query performance
- Validate service behavior
- Run comprehensive integration tests
- Deploy to staging with extra monitoring
- Deploy to production with gradual rollout

#### Week 4: Finalization
- Complete documentation
- Team training on new patterns
- Final production deployment
- Post-deployment monitoring

### Rollback Strategy

**Configuration Changes**
- Can rollback by reverting environment variables
- Old config files still functional
- Zero downtime rollback

**API Changes**
- Can rollback via deployment revert
- No database migrations required
- Zero downtime rollback

**Repository Changes**
- Can rollback via deployment revert
- No database schema changes
- Monitor for performance regressions
- Zero downtime rollback


## Performance Considerations

### Configuration Loading

**Impact**: Negligible (< 1ms overhead)

**Optimizations:**
- Use `@lru_cache()` for singleton settings instances
- Lazy load sub-configurations only when needed
- Cache environment variable parsing
- Pydantic V2 provides fast validation

**Monitoring:**
- Track configuration loading time at startup
- Monitor memory usage of cached configs
- Alert on configuration validation errors

### API Response Serialization

**Impact**: 10-20% faster with Pydantic V2

**Optimizations:**
- Pydantic V2 uses Rust core for faster serialization
- Use `response_model_exclude_unset=True` for sparse responses
- Consider response caching for expensive queries
- Use streaming responses for large datasets

**Monitoring:**
- Track endpoint response times
- Monitor serialization overhead
- Compare before/after performance metrics

### Repository Pattern

**Impact**: Neutral to positive (0-5% improvement)

**Benefits:**
- Better query optimization opportunities
- Easier to add caching at repository level
- Improved testability leads to better performance tuning
- Clear separation allows for targeted optimization

**Monitoring:**
- Track database query execution times
- Monitor connection pool usage
- Track transaction rollback rates
- Alert on slow queries (> 100ms)

### Expected Performance Metrics

**Configuration:**
- Startup time: < 100ms for config loading
- Memory overhead: < 1MB for cached configs
- Validation time: < 1ms per config instance

**API Endpoints:**
- Response time: No degradation expected
- Serialization: 10-20% faster with Pydantic V2
- Memory usage: Slight reduction due to better typing

**Repository Pattern:**
- Query time: No change expected
- Transaction time: No change expected
- Connection pool: Better utilization possible

## Security Considerations

### Configuration Security

**Sensitive Data Handling:**
- Never log sensitive configuration values
- Use environment variables for secrets
- Validate file paths to prevent directory traversal
- Restrict quarantine directory to safe locations

**Validation:**
- Validate all configuration inputs
- Reject dangerous path values (system directories)
- Enforce reasonable limits on numeric values
- Sanitize string inputs

### API Security

**Authentication & Authorization:**
- Maintain authentication on all endpoints
- Validate user ownership in service layer
- Use Supabase Auth tokens exclusively
- Apply rate limiting on expensive operations

**Input Validation:**
- Validate all input using Pydantic schemas
- Sanitize user-provided strings
- Enforce size limits on uploads
- Validate file types and extensions

**Error Handling:**
- Return appropriate error codes
- Don't leak sensitive information in errors
- Log security-relevant errors
- Monitor for suspicious patterns

### Repository Security

**Query Safety:**
- Use parameterized queries (SQLAlchemy handles this)
- Validate user ownership before data access
- Apply row-level security where appropriate
- Audit all data access operations

**Transaction Safety:**
- Use proper transaction isolation levels
- Handle deadlocks gracefully
- Rollback on errors
- Monitor for long-running transactions

## Monitoring and Observability

### Configuration Monitoring

**Metrics to Track:**
- Configuration loading time at startup
- Configuration validation errors
- Environment variable usage
- Preset configuration usage

**Alerts:**
- Configuration validation failures
- Missing required environment variables
- Configuration inconsistencies
- Unexpected configuration changes

### API Monitoring

**Metrics to Track:**
- Endpoint response times (p50, p95, p99)
- Error rates by endpoint
- Request rates by endpoint
- Validation error rates

**Alerts:**
- Response time > 1s (p95)
- Error rate > 1%
- Validation error rate > 5%
- Unusual traffic patterns

### Repository Monitoring

**Metrics to Track:**
- Query execution times
- Database connection pool usage
- Transaction rollback rates
- Slow query frequency

**Alerts:**
- Query time > 100ms
- Connection pool exhaustion
- High rollback rate (> 5%)
- Deadlock detection

### Logging Strategy

**Configuration Logs:**
- Log configuration loading at startup (INFO)
- Log validation errors (ERROR)
- Log preset usage (DEBUG)

**API Logs:**
- Log all requests (INFO)
- Log validation errors (WARNING)
- Log authentication failures (WARNING)
- Log internal errors (ERROR)

**Repository Logs:**
- Log slow queries (WARNING)
- Log transaction rollbacks (WARNING)
- Log connection errors (ERROR)

## Documentation Requirements

### Code Documentation

**Docstrings:**
- Comprehensive docstrings for all public APIs
- Type hints on all function signatures
- Examples in docstrings where helpful
- Inline comments for complex logic

**Format:**
- Google-style docstrings
- Include Args, Returns, Raises sections
- Provide usage examples
- Document side effects

### API Documentation

**OpenAPI/Swagger:**
- Complete endpoint documentation
- Request/response examples
- Authentication requirements
- Error response documentation

**Additional Documentation:**
- API versioning strategy
- Rate limiting policies
- Pagination conventions
- Error code reference

### Architecture Documentation

**Design Documents:**
- Layer responsibility documentation
- Dependency flow diagrams
- Anti-pattern examples
- Best practices guide

**Style Guides:**
- Endpoint style guide
- Service pattern guide
- Repository pattern guide
- Testing guidelines

### User Documentation

**Configuration Guide:**
- Environment variable reference
- Preset configuration guide
- Migration guide from old configs
- Troubleshooting guide

**Developer Guide:**
- Getting started guide
- Architecture overview
- Contributing guidelines
- Testing guide
