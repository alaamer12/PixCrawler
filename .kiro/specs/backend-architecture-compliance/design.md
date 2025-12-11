# Design Document

## Overview

This design addresses critical architectural violations in the PixCrawler backend that prevent the codebase from following the established three-layer architecture pattern (API → Service → Repository). The refactoring will systematically fix type safety issues, correct method signatures, implement missing components, and establish automated compliance testing.

The design follows a phased approach to minimize risk and ensure each fix can be validated independently before proceeding to the next phase.

## Architecture

### Current State Problems

The backend currently suffers from several architectural anti-patterns:

1. **Import Collisions**: Variable names shadow module imports (e.g., `status` parameter shadows `fastapi.status`)
2. **Broken Abstraction**: Services bypass repositories and access AsyncSession directly
3. **Incorrect Method Signatures**: Repository method calls don't match BaseRepository interface
4. **Missing Components**: PolicyService and related infrastructure don't exist
5. **Type Mismatches**: UUID/int conversions, enum value access, attribute name errors
6. **Documentation Gaps**: Missing docstrings and OpenAPI specifications
7. **No Compliance Testing**: No automated tests to prevent architectural violations

### Target State Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     API Layer (Endpoints)                    │
│  - HTTP request/response handling                            │
│  - Input validation (Pydantic)                               │
│  - Authentication/authorization                              │
│  - Uses: http_status alias for status codes                 │
│  - Depends on: Typed service dependencies (ServiceDep)      │
└────────────────────────┬────────────────────────────────────┘
                         │ Dependency Injection
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Service Layer (Business Logic)              │
│  - Business rules and validation                             │
│  - Workflow orchestration                                    │
│  - Cross-repository coordination                             │
│  - Depends on: Repository interfaces only                   │
│  - Never: Direct AsyncSession access                         │
└────────────────────────┬────────────────────────────────────┘
                         │ Repository Pattern
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                Repository Layer (Data Access)                │
│  - CRUD operations via BaseRepository                        │
│  - Query construction and execution                          │
│  - Transaction management                                    │
│  - Methods: create(**kwargs), update(instance, **kwargs)    │
│  - Methods: get_by_id(id), get_by_uuid(uuid)               │
└────────────────────────┬────────────────────────────────────┘
                         │ SQLAlchemy ORM
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Database (PostgreSQL)                       │
│  - Supabase-managed PostgreSQL                               │
│  - Proper indexes using column objects                      │
│  - TimestampMixin for created_at/updated_at                 │
└─────────────────────────────────────────────────────────────┘
```


## Components and Interfaces

### 1. Import Management System

**Purpose**: Ensure consistent and correct imports across all endpoint files

**Components**:
- `http_status` alias for `fastapi.status` module
- Schema enum imports (APIKeyStatus, DatasetStatus, etc.)
- Import validation utilities

**Interface**:
```python
# Standard import pattern for all endpoint files
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status  # Alias to avoid collision

from backend.schemas.api_keys import APIKeyStatus  # Schema enums unchanged
```

### 2. Repository Pattern Enforcement

**Purpose**: Ensure all repository method calls match BaseRepository interface

**BaseRepository Interface**:
```python
class BaseRepository(Generic[ModelType]):
    async def create(self, **kwargs) -> ModelType:
        """Create new instance with keyword arguments"""
        
    async def update(self, instance: ModelType, **kwargs) -> ModelType:
        """Update instance with keyword arguments"""
        
    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """Get instance by integer ID"""
        
    async def get_by_uuid(self, uuid: UUID) -> Optional[ModelType]:
        """Get instance by UUID"""
        
    async def delete(self, instance: ModelType) -> None:
        """Delete instance"""
```

**Correct Usage Patterns**:
```python
# CREATE - Use keyword argument unpacking
data = {"name": "test", "status": "active"}
instance = await repository.create(**data)  # ✅ Correct

# UPDATE - Pass instance first, then kwargs
instance = await repository.get_by_id(1)
updated = await repository.update(instance, status="completed")  # ✅ Correct

# GET - Use specific method names
instance = await repository.get_by_id(1)  # ✅ Correct for int IDs
instance = await repository.get_by_uuid(uuid_value)  # ✅ Correct for UUIDs
```

### 3. Service Layer Architecture

**Purpose**: Enforce clean separation between business logic and data access

**Service Base Class**:
```python
class BaseService:
    """Base class for all services with logging support"""
    
    def log_operation(self, operation: str, **kwargs) -> None:
        """Log service operation with context"""
```

**Service Pattern**:
```python
class ExampleService(BaseService):
    def __init__(
        self,
        primary_repo: PrimaryRepository,
        secondary_repo: SecondaryRepository
    ) -> None:
        """Initialize with repository dependencies only"""
        super().__init__()
        self.primary_repo = primary_repo
        self.secondary_repo = secondary_repo
        # ❌ NEVER: self.session = session
    
    async def business_operation(self, data: dict) -> Model:
        """Business logic delegates to repositories"""
        # ✅ Business validation
        if not self._validate_business_rules(data):
            raise ValidationError("Invalid data")
        
        # ✅ Delegate to repository
        return await self.primary_repo.create(**data)
```

### 4. Dependency Injection System

**Purpose**: Provide type-safe service instantiation for endpoints

**Factory Pattern**:
```python
# In backend/api/dependencies.py
async def get_example_service(
    session: AsyncSession = Depends(get_session)
) -> ExampleService:
    """Create service with all dependencies"""
    primary_repo = PrimaryRepository(session)
    secondary_repo = SecondaryRepository(session)
    return ExampleService(primary_repo, secondary_repo)

# In backend/api/types.py
ExampleServiceDep = Annotated[
    ExampleService,
    Depends(get_example_service)
]
```

**Endpoint Usage**:
```python
@router.post("/resource")
async def create_resource(
    data: CreateRequest,
    current_user: CurrentUser,
    service: ExampleServiceDep,  # ✅ Typed dependency
) -> ResponseModel:
    result = await service.business_operation(data.model_dump())
    return ResponseModel.model_validate(result)
```

### 5. PolicyService Implementation

**Purpose**: Provide business logic for dataset lifecycle policies

**Class Structure**:
```python
class PolicyService(BaseService):
    """Service for policy business logic"""
    
    def __init__(
        self,
        archival_repo: ArchivalPolicyRepository,
        cleanup_repo: CleanupPolicyRepository,
        execution_log_repo: PolicyExecutionLogRepository
    ) -> None:
        super().__init__()
        self.archival_repo = archival_repo
        self.cleanup_repo = cleanup_repo
        self.execution_log_repo = execution_log_repo
    
    async def create_archival_policy(
        self,
        policy_in: ArchivalPolicyCreate
    ) -> ArchivalPolicy:
        """Create archival policy with validation"""
        
    async def execute_archival_policies(self) -> Dict[str, Any]:
        """Execute all active archival policies"""
```

### 6. Type Conversion Utilities

**Purpose**: Provide explicit and safe type conversions

**Utility Functions**:
```python
def uuid_to_int(value: UUID) -> int:
    """Convert UUID to int safely"""
    return int(value) if isinstance(value, UUID) else value

def ensure_enum(value: Any, enum_class: Type[Enum]) -> Enum:
    """Ensure value is enum instance, not string"""
    if isinstance(value, enum_class):
        return value
    return enum_class(value)
```


## Data Models

### 1. Database Model Corrections

**Dataset Model Index Definitions**:
```python
class Dataset(Base, TimestampMixin):
    __tablename__ = "datasets"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    
    # ✅ CORRECT - Pass column objects, not strings
    __table_args__ = (
        Index("ix_datasets_user_id", user_id),  # Column object
        Index("ix_datasets_status", status),  # Column object
        Index("ix_datasets_user_status", user_id, status),  # Multiple columns
        Index("ix_datasets_created_at", created_at),  # Column object
    )
```

**ActivityLog Model**:
```python
class ActivityLog(Base, TimestampMixin):
    """Activity log model with proper timestamp mixin"""
    __tablename__ = "activity_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
    )
    action: Mapped[str] = mapped_column(String(100))
    resource_type: Mapped[str] = mapped_column(String(50))
    
    # ✅ Inherited from TimestampMixin
    # created_at: Mapped[datetime]  # Column, not method
    # updated_at: Mapped[datetime]  # Column, not method
```

### 2. Schema Models

**Policy Schemas**:
```python
class ArchivalPolicyCreate(BaseModel):
    """Schema for creating archival policy"""
    name: str = Field(..., min_length=1, max_length=100)
    is_active: bool = True
    age_days: int = Field(..., ge=1, le=3650)
    min_access_count: int = Field(0, ge=0)

class ArchivalPolicyResponse(BaseModel):
    """Schema for archival policy response"""
    id: int
    name: str
    is_active: bool
    age_days: int
    min_access_count: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ArchivalPolicyUpdate(BaseModel):
    """Schema for updating archival policy"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None
    age_days: Optional[int] = Field(None, ge=1, le=3650)
    min_access_count: Optional[int] = Field(None, ge=0)
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: HTTP Status Import Consistency

*For any* endpoint file in the backend, all HTTP status code references should use the `http_status` alias and no variable named `status` should shadow the import.

**Validates: Requirements 1.2, 1.4**

### Property 2: Repository Create Method Signature

*For any* service method that calls repository.create(), the call should use keyword argument unpacking (`**data`) instead of passing a dict directly.

**Validates: Requirements 2.1**

### Property 3: Repository Update Method Signature

*For any* service method that calls repository.update(), the call should pass the model instance as the first parameter followed by keyword arguments.

**Validates: Requirements 2.2**

### Property 4: Repository Get Method Naming

*For any* service method that retrieves a single entity by ID, the call should use `get_by_id()` or `get_by_uuid()` method names, never `get()`.

**Validates: Requirements 2.3**

### Property 5: Service Constructor Dependencies

*For any* service class constructor, it should accept only repository dependencies and never accept AsyncSession directly.

**Validates: Requirements 5.2**

### Property 6: Endpoint Service Dependencies

*For any* endpoint function that needs a service, it should use typed dependency injection (ServiceDep) rather than creating service instances directly.

**Validates: Requirements 5.3**

### Property 7: SQLAlchemy Index Definitions

*For any* model class with `__table_args__` containing Index definitions, the Index constructor should receive column objects, not string column names.

**Validates: Requirements 4.1, 4.4**

### Property 8: Builder Package Delegation

*For any* crawl job service method that performs image crawling operations, it should import and delegate to `builder.tasks` rather than implementing crawling logic directly.

**Validates: Requirements 3.3**

### Property 9: Required Parameter Completeness

*For any* method call where the method signature includes required parameters, all required parameters should be provided in the call.

**Validates: Requirements 8.1, 8.2**

### Property 10: Type Conversion Explicitness

*For any* function call where a UUID is passed to a parameter expecting int, an explicit type conversion should be performed with type checking.

**Validates: Requirements 9.1**

### Property 11: Enum Value Passing

*For any* Azure SDK method call that accepts enum parameters, the enum object should be passed directly, not the `.value` attribute.

**Validates: Requirements 9.2**

### Property 12: Timestamp Column Access

*For any* code that accesses the `created_at` attribute on a model with TimestampMixin, it should use property syntax (`.created_at`) not method syntax (`.created_at()`).

**Validates: Requirements 10.2**

### Property 13: Module Docstring Presence

*For any* endpoint or repository file, it should contain a module-level docstring describing its purpose and components.

**Validates: Requirements 7.1, 11.1**

### Property 14: Endpoint Operation IDs

*For any* endpoint decorator (`@router.get`, `@router.post`, etc.), it should include an `operation_id` parameter for OpenAPI specification.

**Validates: Requirements 7.2**

### Property 15: Response Model Usage

*For any* endpoint function that returns data, it should specify a `response_model` parameter in the decorator and return that model type.

**Validates: Requirements 12.2**

### Property 16: Admin Authorization Pattern

*For any* endpoint that requires admin access, it should call a `require_admin()` helper function to verify authorization.

**Validates: Requirements 12.1**

### Property 17: Exception to HTTPException Conversion

*For any* endpoint function that catches service exceptions, it should convert them to HTTPException with appropriate status codes.

**Validates: Requirements 12.3**

### Property 18: Repository Class Inheritance

*For any* repository class, it should extend BaseRepository[ModelType] where ModelType is the SQLAlchemy model it manages.

**Validates: Requirements 13.2**


## Error Handling

### Exception Hierarchy

The refactoring will maintain and use the existing exception hierarchy:

```python
# Core exceptions (backend/core/exceptions.py)
class AppException(Exception):
    """Base application exception"""

class ValidationError(AppException):
    """Raised when validation fails"""

class NotFoundError(AppException):
    """Raised when resource not found"""

class AuthorizationError(AppException):
    """Raised when user lacks permissions"""
```

### Error Handling Patterns

**In Services**:
```python
async def get_resource(self, resource_id: int) -> Resource:
    """Get resource with proper error handling"""
    resource = await self.repository.get_by_id(resource_id)
    if not resource:
        raise NotFoundError(f"Resource {resource_id} not found")
    return resource
```

**In Endpoints**:
```python
@router.get("/resource/{resource_id}")
async def get_resource(
    resource_id: int,
    service: ResourceServiceDep,
) -> ResourceResponse:
    """Get resource with HTTP error conversion"""
    try:
        resource = await service.get_resource(resource_id)
        return ResourceResponse.model_validate(resource)
    except NotFoundError as e:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
```

### Type Error Prevention

**UUID to Int Conversion**:
```python
def safe_uuid_to_int(value: UUID | int) -> int:
    """Safely convert UUID to int"""
    if isinstance(value, UUID):
        return int(value)
    return value
```

**Enum Value Handling**:
```python
# ❌ WRONG
blob_client.set_standard_blob_tier(
    tier,
    rehydrate_priority=priority.value  # Passing string
)

# ✅ CORRECT
blob_client.set_standard_blob_tier(
    tier,
    rehydrate_priority=priority  # Passing enum
)
```


## Testing Strategy

### Unit Testing Approach

Unit tests will verify individual components in isolation using mocks:

**Service Unit Tests**:
```python
async def test_service_uses_repository_correctly():
    """Test service delegates to repository with correct signature"""
    # Arrange
    mock_repo = Mock(spec=ResourceRepository)
    mock_repo.create = AsyncMock(return_value=Resource(id=1, name="test"))
    service = ResourceService(repository=mock_repo)
    
    # Act
    data = {"name": "test", "status": "active"}
    result = await service.create_resource(data)
    
    # Assert
    mock_repo.create.assert_called_once_with(**data)  # Verify **kwargs
    assert result.id == 1
```

**Repository Unit Tests**:
```python
async def test_repository_create_with_kwargs():
    """Test repository create accepts keyword arguments"""
    # Arrange
    session = AsyncMock(spec=AsyncSession)
    repo = ResourceRepository(session)
    
    # Act
    result = await repo.create(name="test", status="active")
    
    # Assert
    assert result.name == "test"
    assert result.status == "active"
```

### Property-Based Testing

Property-based tests will verify universal properties across many inputs using Hypothesis:

**Library**: Hypothesis (Python property-based testing library)

**Configuration**: Each property test will run a minimum of 100 iterations

**Test Tagging**: Each property test will include a comment referencing the design document property

**Property Test Examples**:

```python
from hypothesis import given, strategies as st
import pytest

# **Feature: backend-architecture-compliance, Property 2: Repository Create Method Signature**
@given(
    data=st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.one_of(st.text(), st.integers(), st.booleans())
    )
)
@pytest.mark.asyncio
async def test_property_repository_create_uses_kwargs(data):
    """
    Property: All repository.create() calls should use **kwargs unpacking
    
    For any dictionary of data, when passed to repository.create(),
    it should be unpacked as keyword arguments.
    """
    mock_repo = Mock(spec=BaseRepository)
    mock_repo.create = AsyncMock(return_value=Mock(id=1))
    
    # Simulate service calling repository
    await mock_repo.create(**data)
    
    # Verify call was made with unpacked kwargs
    mock_repo.create.assert_called_once()
    call_kwargs = mock_repo.create.call_args.kwargs
    assert call_kwargs == data


# **Feature: backend-architecture-compliance, Property 5: Service Constructor Dependencies**
@given(
    service_class=st.sampled_from([
        UserService,
        ProjectService,
        NotificationService,
        DatasetService
    ])
)
def test_property_service_no_session_dependency(service_class):
    """
    Property: No service constructor should accept AsyncSession
    
    For any service class, its __init__ method should not have
    AsyncSession as a parameter type.
    """
    import inspect
    sig = inspect.signature(service_class.__init__)
    
    for param_name, param in sig.parameters.items():
        if param_name == 'self':
            continue
        # Verify no parameter is typed as AsyncSession
        assert param.annotation != AsyncSession, \
            f"{service_class.__name__}.__init__ has AsyncSession parameter: {param_name}"


# **Feature: backend-architecture-compliance, Property 7: SQLAlchemy Index Definitions**
@given(
    model_class=st.sampled_from([
        Dataset,
        CrawlJob,
        Project,
        Notification
    ])
)
def test_property_index_uses_column_objects(model_class):
    """
    Property: All Index definitions should use column objects
    
    For any model with __table_args__, all Index instances should
    receive column objects, not string column names.
    """
    if not hasattr(model_class, '__table_args__'):
        return
    
    table_args = model_class.__table_args__
    for arg in table_args:
        if isinstance(arg, Index):
            # Check that index columns are Column objects, not strings
            for col in arg.columns:
                assert not isinstance(col, str), \
                    f"{model_class.__name__} has Index with string column: {col}"


# **Feature: backend-architecture-compliance, Property 12: Timestamp Column Access**
@given(
    model_instance=st.builds(ActivityLog, id=st.integers(min_value=1))
)
def test_property_created_at_is_column_not_method(model_instance):
    """
    Property: created_at should be accessed as column, not method
    
    For any model instance with TimestampMixin, created_at should
    be a column attribute, not a callable method.
    """
    # Verify created_at exists and is not callable
    assert hasattr(model_instance, 'created_at')
    assert not callable(model_instance.created_at), \
        "created_at should be a column, not a method"
```

### Architecture Compliance Tests

Architecture tests will verify structural constraints:

```python
def test_architecture_services_no_async_session_import():
    """
    Verify services don't import AsyncSession directly
    
    **Feature: backend-architecture-compliance, Property 5**
    """
    service_files = Path("backend/services").glob("*.py")
    
    for service_file in service_files:
        if service_file.name == "__init__.py":
            continue
            
        content = service_file.read_text()
        
        # Allow TYPE_CHECKING imports for type hints
        if "from sqlalchemy.ext.asyncio import AsyncSession" in content:
            assert "if TYPE_CHECKING:" in content, \
                f"{service_file.name} imports AsyncSession outside TYPE_CHECKING"


def test_architecture_repositories_extend_base():
    """
    Verify all repositories extend BaseRepository
    
    **Feature: backend-architecture-compliance, Property 18**
    """
    import inspect
    from backend.repositories.base import BaseRepository
    import backend.repositories as repo_module
    
    for name, obj in inspect.getmembers(repo_module, inspect.isclass):
        if name == "BaseRepository" or name.startswith("_"):
            continue
        if name.endswith("Repository"):
            assert issubclass(obj, BaseRepository), \
                f"{name} does not extend BaseRepository"


def test_architecture_endpoints_no_direct_queries():
    """
    Verify endpoints don't execute database queries directly
    
    **Feature: backend-architecture-compliance, Property 6**
    """
    endpoint_files = Path("backend/api/v1/endpoints").glob("*.py")
    
    for endpoint_file in endpoint_files:
        content = endpoint_file.read_text()
        
        # Check for direct query execution patterns
        forbidden_patterns = [
            "session.execute(",
            "session.query(",
            "select(",
        ]
        
        for pattern in forbidden_patterns:
            if pattern in content:
                # Allow in TYPE_CHECKING or comments
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if pattern in line and not line.strip().startswith('#'):
                        pytest.fail(
                            f"{endpoint_file.name}:{i+1} contains direct query: {pattern}"
                        )


def test_architecture_http_status_import_pattern():
    """
    Verify all endpoints use http_status alias
    
    **Feature: backend-architecture-compliance, Property 1**
    """
    endpoint_files = Path("backend/api/v1/endpoints").glob("*.py")
    
    for endpoint_file in endpoint_files:
        content = endpoint_file.read_text()
        
        if "from fastapi import" in content and "status" in content:
            # Should use alias
            assert "status as http_status" in content, \
                f"{endpoint_file.name} should import 'status as http_status'"
            
            # Should not use bare 'status.HTTP_'
            if "status.HTTP_" in content:
                assert "http_status.HTTP_" in content, \
                    f"{endpoint_file.name} should use http_status.HTTP_* not status.HTTP_*"
```

### Integration Testing

Integration tests will verify multiple layers working together:

```python
async def test_integration_endpoint_service_repository(client, auth_headers):
    """Test full stack: endpoint → service → repository → database"""
    # Act
    response = await client.post(
        "/api/v1/resources",
        json={"name": "test", "status": "active"},
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test"
    assert data["status"] == "active"
    
    # Verify in database
    resource = await ResourceRepository(session).get_by_id(data["id"])
    assert resource is not None
    assert resource.name == "test"
```

### Test Coverage Requirements

- **Unit Tests**: Minimum 80% coverage for services and repositories
- **Property Tests**: All 18 correctness properties must have corresponding property-based tests
- **Architecture Tests**: All 4 architecture constraints must have compliance tests
- **Integration Tests**: Critical user flows must have end-to-end tests

