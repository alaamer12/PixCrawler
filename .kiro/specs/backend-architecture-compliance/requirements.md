# Requirements Document

## Introduction

This specification addresses critical architectural violations and type safety issues in the PixCrawler backend codebase. The backend currently violates the established three-layer architecture pattern (API → Service → Repository) and professional FastAPI best practices, leading to maintainability issues, type safety problems, and potential runtime errors.

The goal is to systematically refactor the backend to comply with architectural principles while maintaining functionality and improving code quality.

## Glossary

- **Backend System**: The FastAPI-based REST API server that handles HTTP requests and business logic
- **Three-Layer Architecture**: Architectural pattern with API Layer (endpoints), Service Layer (business logic), and Repository Layer (data access)
- **BaseRepository**: Abstract base class providing CRUD operations for database entities
- **Dependency Injection**: Design pattern where dependencies are provided to classes rather than created internally
- **Type Safety**: Ensuring code uses correct types to prevent runtime errors
- **HTTP Status Module**: FastAPI's status module containing HTTP status code constants
- **Service Layer**: Middle layer containing business logic and workflow orchestration
- **Repository Layer**: Data access layer responsible for database operations
- **API Layer**: HTTP endpoint layer handling requests, responses, and serialization

## Requirements

### Requirement 1

**User Story:** As a backend developer, I want all endpoint files to use correct HTTP status code imports, so that I can reference status codes without name collisions.

#### Acceptance Criteria

1. WHEN an endpoint file imports HTTP status codes THEN the Backend System SHALL import using the alias `http_status` to avoid variable name collisions
2. WHEN an endpoint file uses HTTP status codes THEN the Backend System SHALL reference them as `http_status.HTTP_*` instead of `status.HTTP_*`
3. WHEN an endpoint file imports schema enums THEN the Backend System SHALL keep schema enum imports unchanged (e.g., `APIKeyStatus`, `DatasetStatus`)
4. WHEN the Backend System processes endpoint files THEN the Backend System SHALL ensure no variable named `status` shadows the HTTP status module import

### Requirement 2

**User Story:** As a backend developer, I want all service methods to use correct repository method signatures, so that database operations execute without type errors.

#### Acceptance Criteria

1. WHEN a service calls repository create method THEN the Backend System SHALL pass data using keyword argument unpacking (`**data`) instead of passing dict directly
2. WHEN a service calls repository update method THEN the Backend System SHALL pass the model instance as first parameter followed by keyword arguments for updates
3. WHEN a service calls repository get method THEN the Backend System SHALL use `get_by_id()` method name instead of `get()`
4. WHEN a service calls any repository method THEN the Backend System SHALL match the method signature defined in BaseRepository

### Requirement 3

**User Story:** As a backend developer, I want the crawl job service to delegate crawling logic to the builder package, so that code follows DRY principle and proper architecture.

#### Acceptance Criteria

1. WHEN the crawl job service needs to perform image crawling THEN the Backend System SHALL import and use tasks from the `builder` package
2. WHEN the crawl job service orchestrates workflows THEN the Backend System SHALL focus on business logic coordination without reimplementing crawling algorithms
3. WHEN the crawl job service interacts with crawling functionality THEN the Backend System SHALL use `builder.tasks` for actual image downloading operations
4. WHEN reviewing crawl job service code THEN the Backend System SHALL contain no duplicate crawling implementation that exists in builder package

### Requirement 4

**User Story:** As a backend developer, I want database models to use correct SQLAlchemy index definitions, so that database schema is created properly.

#### Acceptance Criteria

1. WHEN defining table indexes in `__table_args__` THEN the Backend System SHALL pass column objects instead of string column names
2. WHEN the Dataset model defines indexes THEN the Backend System SHALL use syntax `Index("index_name", column_object)` instead of `Index("index_name", "column_string")`
3. WHEN SQLAlchemy creates database schema THEN the Backend System SHALL generate indexes without type mismatch errors
4. WHEN multiple columns are indexed together THEN the Backend System SHALL pass all column objects in correct order

### Requirement 5

**User Story:** As a backend developer, I want all services to have proper dependency injection, so that services are testable and follow clean architecture.

#### Acceptance Criteria

1. WHEN a service is initialized THEN the Backend System SHALL accept repository dependencies through constructor parameters
2. WHEN a service needs database access THEN the Backend System SHALL use injected repositories instead of accepting AsyncSession directly
3. WHEN an endpoint needs a service THEN the Backend System SHALL use typed dependency injection via factory functions
4. WHEN creating service instances THEN the Backend System SHALL use dependency injection pattern defined in `backend/api/dependencies.py`

### Requirement 6

**User Story:** As a backend developer, I want missing service and repository classes to be implemented, so that all endpoints have proper business logic layer.

#### Acceptance Criteria

1. WHEN the policy endpoint requires a service THEN the Backend System SHALL provide a PolicyService class in `backend/services/policy.py`
2. WHEN PolicyService is created THEN the Backend System SHALL accept ArchivalPolicyRepository, CleanupPolicyRepository, and PolicyExecutionLogRepository as dependencies
3. WHEN PolicyService methods are called THEN the Backend System SHALL delegate data access to injected repositories
4. WHEN PolicyService is needed in endpoints THEN the Backend System SHALL provide a factory function in `backend/api/dependencies.py` and typed dependency in `backend/api/types.py`

### Requirement 7

**User Story:** As a backend developer, I want all endpoint files to have comprehensive documentation, so that API consumers understand endpoint behavior.

#### Acceptance Criteria

1. WHEN an endpoint file is created THEN the Backend System SHALL include a module-level docstring describing all endpoints
2. WHEN an endpoint decorator is defined THEN the Backend System SHALL include `operation_id` parameter for OpenAPI specification
3. WHEN an endpoint has responses THEN the Backend System SHALL include example response bodies in the `responses` parameter
4. WHEN an endpoint requires authentication THEN the Backend System SHALL document authentication requirements in the docstring

### Requirement 8

**User Story:** As a backend developer, I want all service method calls to include required parameters, so that methods execute without missing argument errors.

#### Acceptance Criteria

1. WHEN a service method requires `user_id` parameter THEN the Backend System SHALL pass the user_id value from current_user context
2. WHEN calling validator.check_integrity THEN the Backend System SHALL include the required `category_name` parameter
3. WHEN a service method signature changes THEN the Backend System SHALL update all call sites to match new signature
4. WHEN type checking is performed THEN the Backend System SHALL report no missing required argument errors

### Requirement 9

**User Story:** As a backend developer, I want type conversions to be explicit and correct, so that type mismatches don't cause runtime errors.

#### Acceptance Criteria

1. WHEN passing UUID to a method expecting int THEN the Backend System SHALL explicitly convert UUID to int with proper type checking
2. WHEN passing enum values to Azure SDK methods THEN the Backend System SHALL pass the enum object instead of calling `.value`
3. WHEN accessing model properties THEN the Backend System SHALL use correct attribute names (e.g., `metadata` not `metadata_`)
4. WHEN MyPy type checking runs THEN the Backend System SHALL report no type mismatch errors in service and repository layers

### Requirement 10

**User Story:** As a backend developer, I want ActivityLog model to use correct timestamp access, so that created_at is accessed as a column not a method.

#### Acceptance Criteria

1. WHEN ActivityLog model is defined THEN the Backend System SHALL extend TimestampMixin to inherit created_at column
2. WHEN code accesses created_at THEN the Backend System SHALL use `.created_at` property syntax instead of `.created_at()` method syntax
3. WHEN searching codebase for timestamp access THEN the Backend System SHALL find no instances of `.created_at()` method calls
4. WHEN ActivityLog instances are queried THEN the Backend System SHALL successfully access created_at without AttributeError

### Requirement 11

**User Story:** As a backend developer, I want all repository classes to have comprehensive docstrings, so that data access patterns are well-documented.

#### Acceptance Criteria

1. WHEN a repository file is created THEN the Backend System SHALL include module-level docstring describing repository purpose
2. WHEN a repository class is defined THEN the Backend System SHALL include class-level docstring describing data access responsibilities
3. WHEN a repository method is defined THEN the Backend System SHALL include method-level docstring with Args, Returns, and Raises sections
4. WHEN reviewing repository code THEN the Backend System SHALL follow consistent documentation style across all repository files

### Requirement 12

**User Story:** As a backend developer, I want endpoint files to follow consistent patterns, so that API code is maintainable and predictable.

#### Acceptance Criteria

1. WHEN an endpoint requires admin access THEN the Backend System SHALL use a `require_admin()` helper function for authorization checks
2. WHEN an endpoint returns data THEN the Backend System SHALL use Pydantic response models for serialization
3. WHEN an endpoint handles errors THEN the Backend System SHALL convert service exceptions to appropriate HTTPException responses
4. WHEN an endpoint is defined THEN the Backend System SHALL follow the pattern: validate input → delegate to service → serialize response

### Requirement 13

**User Story:** As a backend developer, I want architecture tests to verify compliance, so that architectural violations are caught automatically.

#### Acceptance Criteria

1. WHEN architecture tests run THEN the Backend System SHALL verify services don't import AsyncSession directly
2. WHEN architecture tests run THEN the Backend System SHALL verify all repositories extend BaseRepository
3. WHEN architecture tests run THEN the Backend System SHALL verify endpoints don't execute database queries directly
4. WHEN architecture tests run THEN the Backend System SHALL verify all services use dependency injection pattern
