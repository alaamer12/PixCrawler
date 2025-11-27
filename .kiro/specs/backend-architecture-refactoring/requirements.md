# Requirements Document

## Introduction

This specification addresses three critical architectural issues in the PixCrawler monorepo that impact code maintainability, consistency, and adherence to established design patterns. The refactoring will improve the utility package configuration management, standardize API endpoint patterns across the backend, and enforce proper separation of concerns through the repository pattern.

PixCrawler is a Python-based SaaS platform for automated image dataset building with a FastAPI backend, Next.js frontend, and multiple utility packages managed through UV workspace configuration. The platform serves researchers, enterprises, and individual developers who need custom image datasets for machine learning projects.

The three problems to be addressed are:
1. **Utility Package Configuration**: Missing unified configuration management across sub-packages
2. **API Endpoint Inconsistency**: Non-standard patterns in endpoint implementation and documentation
3. **Repository Pattern Violations**: Improper separation of concerns between API, service, and repository layers

## Requirements

### Requirement 1: Unified Utility Package Configuration

**User Story:** As a platform developer, I want a centralized configuration system for the utility package, so that I can manage compression and logging settings consistently across the entire application.

#### Acceptance Criteria

1. WHEN the utility package is initialized THEN a unified `utility/config.py` file SHALL exist with a `UtilitySettings` class
2. WHEN `UtilitySettings` is instantiated THEN it SHALL use Pydantic V2 `BaseSettings` with `SettingsConfigDict`
3. WHEN environment variables are loaded THEN they SHALL use the prefix `PIXCRAWLER_UTILITY_`
4. WHEN sub-package configurations are accessed THEN they SHALL be nested within `UtilitySettings` using composition pattern
5. WHEN configuration presets are requested THEN the system SHALL provide `default`, `production`, `development`, and `testing` presets
6. WHEN `get_utility_settings()` is called THEN it SHALL return a cached singleton instance
7. WHEN `get_preset_config(preset_name)` is called THEN it SHALL return the appropriate preset configuration
8. WHEN invalid configuration values are provided THEN Pydantic validators SHALL raise appropriate validation errors
9. WHEN cross-package configuration conflicts exist THEN model validators SHALL detect and report them
10. WHEN existing sub-package configs are used THEN they SHALL optionally integrate with the unified config while maintaining backward compatibility

### Requirement 2: Utility Package Testing

**User Story:** As a quality assurance engineer, I want comprehensive test coverage for the utility package, so that I can ensure configuration management and compression operations work reliably.

#### Acceptance Criteria

1. WHEN utility package tests are executed THEN code coverage SHALL be at least 85%
2. WHEN `utility/tests/test_config.py` is created THEN it SHALL test default settings, environment variable loading, nested configuration composition, validation rules, preset configurations, and cross-package consistency
3. WHEN `utility/tests/test_compress.py` is enhanced THEN it SHALL include edge case tests for corrupted images, permission errors, large file handling, concurrent compression, and error recovery
4. WHEN configuration validation paths are tested THEN all validation rules SHALL be exercised
5. WHEN error conditions are tested THEN all error handling paths SHALL be verified
6. WHEN integration tests are executed THEN full compression and logging workflows SHALL be validated

### Requirement 3: Standardized API Endpoint Patterns

**User Story:** As a backend developer, I want all API endpoints to follow consistent patterns, so that the codebase is maintainable and the API documentation is complete and accurate.

#### Acceptance Criteria

1. WHEN list endpoints are defined THEN they SHALL use `"/"` or `"/resource-name"` instead of empty string `""`
2. WHEN endpoint functions are defined THEN they SHALL have typed response models using Pydantic schemas
3. WHEN route decorators are applied THEN they SHALL include `response_model`, `summary`, `description`, `response_description`, `operation_id`, and detailed `responses` dictionary
4. WHEN operation IDs are assigned THEN they SHALL use camelCase format (e.g., `"listNotifications"`, `"getStorageUsage"`)
5. WHEN common error responses are documented THEN they SHALL use `get_common_responses()` helper function
6. WHEN endpoint docstrings are written THEN they SHALL include detailed description paragraph, authentication requirements, all parameters with types, return type documentation, and possible exceptions
7. WHEN endpoint functions return values THEN they SHALL use typed response models, not generic dictionaries
8. WHEN OpenAPI examples are provided THEN they SHALL include realistic sample data for 200 responses
9. WHEN all endpoints are audited THEN non-compliant endpoints SHALL be identified and documented
10. WHEN endpoint style guide is created THEN it SHALL be documented in `backend/api/v1/ENDPOINT_STYLE_GUIDE.md`

### Requirement 4: Repository Pattern Enforcement

**User Story:** As a software architect, I want proper separation of concerns between API, service, and repository layers, so that the codebase follows clean architecture principles and is easier to test and maintain.

#### Acceptance Criteria

1. WHEN services are defined THEN they SHALL NOT have direct `AsyncSession` parameters
2. WHEN services perform data operations THEN they SHALL delegate to repository methods, not execute raw SQL queries
3. WHEN repositories are defined THEN they SHALL extend `BaseRepository` and focus only on data access operations
4. WHEN repositories are implemented THEN they SHALL NOT contain business logic
5. WHEN API endpoints are defined THEN they SHALL NOT contain business logic or database queries
6. WHEN API endpoints access data THEN they SHALL use service layer methods via dependency injection
7. WHEN dependency injection is configured THEN it SHALL follow the pattern: `get_service_name(session) -> ServiceClass` where service receives repository instance
8. WHEN services are instantiated THEN they SHALL receive repository instances, not database sessions
9. WHEN architecture violations are found THEN they SHALL be documented in `backend/REPOSITORY_PATTERN_AUDIT.md`
10. WHEN architecture tests are created THEN they SHALL verify services don't import `AsyncSession` directly, repositories extend `BaseRepository`, and endpoints don't have database queries

### Requirement 5: Backward Compatibility and Migration

**User Story:** As a platform operator, I want refactoring changes to maintain backward compatibility where possible, so that existing functionality continues to work during the transition period.

#### Acceptance Criteria

1. WHEN existing configuration APIs are changed THEN deprecation warnings SHALL be added for old patterns
2. WHEN sub-package configurations are updated THEN they SHALL maintain their existing public interfaces
3. WHEN API endpoints are refactored THEN existing API contracts SHALL be preserved
4. WHEN repository patterns are fixed THEN existing service functionality SHALL remain unchanged
5. WHEN migration is performed THEN comprehensive tests SHALL verify no regressions are introduced

### Requirement 6: Documentation and Code Quality

**User Story:** As a new developer joining the project, I want comprehensive documentation and consistent code style, so that I can understand the architecture and contribute effectively.

#### Acceptance Criteria

1. WHEN unified configuration is created THEN it SHALL include comprehensive docstrings with examples
2. WHEN endpoint style guide is written THEN it SHALL include templates for route paths, response models, OpenAPI documentation, docstrings, and type hints
3. WHEN repository pattern audit is completed THEN it SHALL document all violations found and fixes applied
4. WHEN code is written THEN it SHALL follow Ruff formatting with 88 character line length
5. WHEN type hints are added THEN they SHALL use proper types from `backend/api/types.py`
6. WHEN Pydantic models are used THEN they SHALL follow Pydantic V2 patterns (`model_validate`, `model_dump`, `SettingsConfigDict`)
7. WHEN errors are handled THEN they SHALL use custom exceptions from `backend/core/exceptions.py`
8. WHEN logging is performed THEN it SHALL use Loguru logger from `utility.logging_config`

### Requirement 7: Test Coverage and Validation

**User Story:** As a continuous integration engineer, I want comprehensive automated tests, so that I can ensure code quality and catch regressions early.

#### Acceptance Criteria

1. WHEN utility package tests are run THEN coverage SHALL be at least 85%
2. WHEN configuration tests are executed THEN all validation paths SHALL be tested
3. WHEN endpoint tests are run THEN all refactored endpoints SHALL have corresponding test cases
4. WHEN architecture tests are executed THEN they SHALL verify proper layer separation
5. WHEN integration tests are run THEN they SHALL validate full workflows across layers
6. WHEN tests are written THEN they SHALL follow TDD approach (tests before implementation)
7. WHEN all tests pass THEN the refactoring SHALL be considered complete

### Requirement 8: Phased Execution and Deliverables

**User Story:** As a project manager, I want the refactoring to be executed in logical phases, so that progress can be tracked and risks can be managed.

#### Acceptance Criteria

1. WHEN Phase 1 (Utility Config) is completed THEN unified config SHALL exist, sub-packages SHALL be updated, tests SHALL be written, and documentation SHALL be complete
2. WHEN Phase 2 (API Endpoints) is completed THEN all endpoints SHALL be audited, style guide SHALL be created, non-compliant endpoints SHALL be fixed, and tests SHALL be updated
3. WHEN Phase 3 (Repository Pattern) is completed THEN all layers SHALL be audited, violations SHALL be fixed, dependency injection SHALL be consistent, and architecture tests SHALL pass
4. WHEN each phase is completed THEN a summary report SHALL document files changed, violations fixed, and test coverage improvements
5. WHEN all phases are completed THEN the system SHALL maintain full backward compatibility and all tests SHALL pass
