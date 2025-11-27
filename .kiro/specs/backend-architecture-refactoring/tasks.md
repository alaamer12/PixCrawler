# Implementation Plan

## Phase 1: Utility Package Configuration

- [x] 1. Create unified utility configuration system





  - Create `utility/config.py` with `UtilitySettings` class using Pydantic V2 BaseSettings
  - Implement nested composition with `CompressionSettings` and `LoggingSettings`
  - Add environment variable support with `PIXCRAWLER_UTILITY_` prefix
  - Implement `@model_validator` for cross-package consistency validation
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.9_

- [x] 1.1 Implement factory functions and presets


  - Create `get_utility_settings()` function with `@lru_cache()` decorator
  - Create `get_preset_config(preset_name: str)` function
  - Define `CONFIG_PRESETS` dictionary with default, production, development, testing presets
  - Implement preset-specific configuration values
  - _Requirements: 1.6, 1.7_

- [x] 1.2 Update compression config for optional integration


  - Modify `utility/compress/config.py` to optionally use unified config
  - Add backward compatibility layer
  - Add deprecation warnings for direct usage
  - Update `get_compression_settings()` to check for unified config first
  - _Requirements: 1.10_

- [x] 1.3 Update logging config for optional integration


  - Modify `utility/logging_config/config.py` to optionally use unified config
  - Add backward compatibility layer
  - Add deprecation warnings for direct usage
  - Update `get_logging_settings()` to check for unified config first
  - _Requirements: 1.10_

- [x] 1.4 Create configuration tests


  - Create `utility/tests/test_config.py` file
  - Write test for default settings initialization
  - Write test for environment variable loading with `PIXCRAWLER_UTILITY_` prefix
  - Write test for nested configuration composition
  - Write test for field validation rules (quality, compression level, etc.)
  - Write test for preset configurations (default, production, development, testing)
  - Write test for cross-package consistency validation
  - Write test for invalid configuration values raising ValidationError
  - _Requirements: 2.2, 2.4_

- [ ]* 1.5 Enhance compression tests with edge cases
  - Add test for corrupted image handling
  - Add test for permission errors (read/write denied)
  - Add test for large file handling (>100MB)
  - Add test for concurrent compression operations
  - Add test for error recovery and retry logic
  - Add test for memory usage under load
  - Add test for archive creation and extraction

  - Note if the current implementation does not satisfy this test requirments, so ensure to add these requirments to source code and document it
  - _Requirements: 2.3, 2.5_

- [x] 1.6 Update utility package documentation


  - Update `utility/README.md` with unified config usage examples
  - Add docstrings to all new functions and classes
  - Document environment variable naming conventions
  - Add migration guide from old configs to unified config
  - Document preset configurations and when to use each
  - _Requirements: 6.1, 6.8_

- [x] 1.7 Verify test coverage and backward compatibility


  - Run pytest with coverage report
  - Ensure ≥ 85% code coverage for utility package
  - Verify all existing code still works with old configs
  - Test environment variable loading with both old and new prefixes
  - Validate no breaking changes introduced
  - _Requirements: 2.1, 2.6, 5.2, 7.1_


## Phase 2: API Endpoint Standardization

- [-] 2. Audit all backend API endpoints



  - List all files in `backend/api/v1/endpoints/` directory
  - For each endpoint file, check route path patterns (empty `""` vs `"/"`)
  - Check for response model usage in route decorators
  - Check for OpenAPI documentation completeness (operation_id, response_description, responses dict)
  - Check docstring format and detail level
  - Check type hints on return values
  - Document all violations in audit report
  - _Requirements: 3.9_

- [x] 2.1 Create endpoint style guide documentation



  - Create `backend/api/v1/ENDPOINT_STYLE_GUIDE.md` file
  - Document route path conventions (use "/" or "/resource-name", not "")
  - Document response model requirements with examples
  - Provide OpenAPI documentation template with all required fields
  - Provide docstring template with all required sections
  - Document type hint requirements and type aliases to use
  - Document error handling patterns with examples
  - Include checklist for endpoint compliance
  - _Requirements: 3.10, 6.2_

- [x] 2.2 Fix notifications endpoint





- read the files backend/api/v1/ENDPOINT_STYLE_GUIDE.md backend/api/v1/ENDPOINT_AUDIT_REPORT.md for context understanding
  - Change route path from `""` to `"/notifications"` for list endpoint
  - Add `response_model=NotificationListResponse` to list endpoint
  - Create `NotificationListResponse` schema in `backend/schemas/notifications.py`
  - Add `operation_id="listNotifications"` to list endpoint
  - Add `response_description` to list endpoint
  - Add detailed `responses` dict with 200 example to list endpoint
  - Update return type from `dict` to `NotificationListResponse`
  - Enhance docstring with detailed description, authentication note, and all sections
  - Apply same fixes to `mark_as_read` and `mark_all_read` endpoints
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.6, 3.7_



- [x] 2.3 Audit and fix remaining endpoints



- read the files backend/api/v1/ENDPOINT_STYLE_GUIDE.md backend/api/v1/ENDPOINT_AUDIT_REPORT.md for context understanding
  - Review `backend/api/v1/endpoints/auth.py` for compliance
  - Review `backend/api/v1/endpoints/crawl_jobs.py` for compliance
  - Review `backend/api/v1/endpoints/datasets.py` for compliance
  - Review `backend/api/v1/endpoints/exports.py` for compliance
  - Review `backend/api/v1/endpoints/health.py` for compliance
  - Review `backend/api/v1/endpoints/users.py` for compliance
  - Review `backend/api/v1/endpoints/validation.py` for compliance
  - Fix any non-compliant endpoints following the same pattern as notifications
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_

- [-] 2.4 Create or update response models



- read the files backend/api/v1/ENDPOINT_STYLE_GUIDE.md backend/api/v1/ENDPOINT_AUDIT_REPORT.md for context understanding
  - Review all schemas in `backend/schemas/` directory
  - Create missing list response models (e.g., `NotificationListResponse`)
  - Ensure all response models follow `{data: [], meta: {}}` structure
  - Add proper type hints and field descriptions
  - Add examples to response models
  - Validate all models with Pydantic V2 patterns
  - _Requirements: 3.2, 3.7, 6.6_

- [ ]* 2.5 Update endpoint tests
- read the files backend/api/v1/ENDPOINT_STYLE_GUIDE.md backend/api/v1/ENDPOINT_AUDIT_REPORT.md for context understanding
  - Review all tests in `backend/tests/api/` directory
  - Ensure all refactored endpoints have corresponding tests
  - Ensure each endpoint has its own tests suite in a independent file
  - Add tests for response model validation
  - Add tests for OpenAPI schema generation
  - Add integration tests for complete request/response flows
  - Verify all tests pass
  - _Requirements: 3.11, 7.3_

- [ ] 2.6 Verify OpenAPI schema generation
- read the files backend/api/v1/ENDPOINT_STYLE_GUIDE.md backend/api/v1/ENDPOINT_AUDIT_REPORT.md for context understanding
  - Start FastAPI application
  - Access `/docs` endpoint and verify Swagger UI loads correctly
  - Verify all endpoints appear with correct operation IDs
  - Verify all response models are documented
  - Verify all examples are present
  - Access `/openapi.json` and validate schema structure
  - Test API calls through Swagger UI
  - _Requirements: 3.12, 7.3_


## Phase 3: Repository Pattern Enforcement

- [ ] 3. Audit all services for repository pattern violations
  - List all files in `backend/services/` directory
  - For each service, check if it has direct `AsyncSession` parameter in `__init__`
  - Check if service performs raw SQL queries using `session.execute()`
  - Check if service has database-specific logic that should be in repository
  - Check if service properly uses repository methods
  - Document all violations with file name, line number, and violation type
  - _Requirements: 4.1, 4.2, 4.9_

- [ ] 3.1 Audit all repositories for pattern violations
  - List all files in `backend/repositories/` directory
  - For each repository, check if it extends `BaseRepository`
  - Check if repository contains business logic (calculations, transformations, etc.)
  - Check if repository methods are focused on data access only
  - Check for proper use of SQLAlchemy query patterns
  - Document all violations with file name, line number, and violation type
  - _Requirements: 4.3, 4.4_

- [ ] 3.2 Audit all API endpoints for pattern violations
  - List all files in `backend/api/v1/endpoints/` directory
  - For each endpoint, check if it contains business logic
  - Check if endpoint directly accesses database session
  - Check if endpoint properly uses service layer via dependency injection
  - Check if endpoint only handles HTTP concerns
  - Document all violations with file name, line number, and violation type
  - _Requirements: 4.5, 4.6_

- [ ] 3.3 Create repository pattern audit report
  - Create `backend/REPOSITORY_PATTERN_AUDIT.md` file
  - Document all service violations found
  - Document all repository violations found
  - Document all endpoint violations found
  - Provide examples of correct patterns for each violation type
  - Prioritize violations by severity and impact
  - Create remediation plan for each violation
  - _Requirements: 4.9_

- [ ] 3.4 Fix service layer violations
  - For each service with direct `AsyncSession`, refactor to use repository
  - Move raw SQL queries from services to repository methods
  - Ensure services only orchestrate business logic
  - Update service `__init__` to accept repository instances, not sessions
  - Maintain existing service method signatures for backward compatibility
  - Add deprecation warnings if any public APIs change
  - _Requirements: 4.1, 4.2, 4.8, 5.4_

- [ ] 3.5 Fix repository layer violations
  - Move business logic from repositories to services
  - Ensure repositories only perform CRUD operations
  - Verify all repositories extend `BaseRepository`
  - Simplify repository methods to focus on data access
  - Add new repository methods as needed for service requirements
  - _Requirements: 4.3, 4.4_

- [ ] 3.6 Fix API endpoint violations
  - Remove business logic from endpoints and move to services
  - Remove direct database queries from endpoints
  - Ensure endpoints only handle HTTP concerns (validation, serialization, errors)
  - Update endpoints to use service layer via dependency injection
  - Maintain existing API contracts for backward compatibility
  - _Requirements: 4.5, 4.6, 5.3_

- [ ] 3.7 Update dependency injection patterns
  - Review all `get_*_service` dependency functions
  - Ensure pattern: `get_service(session) -> Service` where service receives repository
  - Update service factory functions to create repository and inject into service
  - Ensure consistent pattern across all endpoints
  - Verify type hints are correct using types from `backend/api/types.py`
  - _Requirements: 4.7, 4.8, 6.5_

- [ ] 3.8 Create architecture tests
  - Create `backend/tests/test_architecture.py` file
  - Write test to verify services don't import `AsyncSession` directly
  - Write test to verify repositories extend `BaseRepository`
  - Write test to verify endpoints don't execute database queries
  - Write test to verify dependency injection pattern consistency
  - Write test to verify no business logic in repositories
  - Write test to verify no business logic in endpoints
  - _Requirements: 4.10, 7.4_

- [ ]* 3.9 Update service and repository tests
  - Review all tests in `backend/tests/services/` directory
  - Update tests to work with refactored services
  - Add tests for new repository methods
  - Ensure all business logic is tested at service level
  - Ensure all data access is tested at repository level
  - Verify all tests pass
  - _Requirements: 7.4, 7.5_

- [ ] 3.10 Verify architecture compliance
  - Run all architecture tests
  - Verify no violations remain
  - Run full test suite to ensure no regressions
  - Check test coverage for services (≥ 85%) and repositories (≥ 80%)
  - Validate backward compatibility maintained
  - _Requirements: 4.10, 5.4, 7.4, 7.5_


## Phase 4: Documentation and Finalization

- [ ] 4. Update package documentation
  - Update `utility/README.md` with unified config documentation
  - Update `backend/README.md` with architecture documentation
  - Document repository pattern in `backend/ARCHITECTURE.md`
  - Add examples of correct patterns for each layer
  - Document common anti-patterns to avoid
  - _Requirements: 6.3, 6.8_

- [ ] 4.1 Create migration guide
  - Create `docs/MIGRATION_GUIDE.md` file
  - Document migration from old utility configs to unified config
  - Document changes to API endpoints (if any breaking changes)
  - Document changes to service/repository patterns
  - Provide code examples for each migration scenario
  - Include troubleshooting section
  - _Requirements: 5.1, 6.8_

- [ ] 4.2 Update API documentation
  - Verify all OpenAPI documentation is complete
  - Update API usage examples in documentation
  - Document authentication requirements clearly
  - Document error response formats
  - Add Postman collection updates if needed
  - _Requirements: 6.2_

- [ ] 4.3 Create final test coverage report
  - Run pytest with coverage for utility package
  - Run pytest with coverage for backend package
  - Generate HTML coverage reports
  - Verify utility package ≥ 85% coverage
  - Verify backend endpoints ≥ 90% coverage
  - Verify backend services ≥ 85% coverage
  - Verify backend repositories ≥ 80% coverage
  - Document any gaps in coverage
  - _Requirements: 7.1, 7.3, 7.4, 7.5_

- [ ] 4.4 Create deployment checklist
  - Document environment variables to set/update
  - Document configuration changes needed
  - Document database migration steps (if any)
  - Document rollback procedures
  - Document monitoring and alerting setup
  - Create smoke test checklist for post-deployment
  - _Requirements: 8.1, 8.2, 8.3_

- [ ] 4.5 Create summary report
  - List all files created
  - List all files modified
  - Document all violations found and fixed
  - Document test coverage improvements
  - Document performance impact (if any)
  - Document backward compatibility status
  - Include before/after metrics
  - _Requirements: 8.4, 8.5_

- [ ] 4.6 Final validation and testing
  - Run full test suite (unit, integration, architecture)
  - Verify all tests pass
  - Run linting (Ruff) and fix any issues
  - Run type checking (MyPy) and fix any issues
  - Test in development environment
  - Test in staging environment
  - Verify no breaking changes
  - _Requirements: 6.4, 7.6, 7.7_

- [ ] 4.7 Prepare for production deployment
  - Review deployment checklist
  - Update CI/CD pipeline if needed
  - Prepare rollback plan
  - Schedule deployment window
  - Notify team of changes
  - Set up monitoring and alerts
  - _Requirements: 8.1, 8.2, 8.3, 8.5_
