# Implementation Plan

ALWAYS USE `python` from `.venv\script\python`
Always read the file #CODEBASE_ISSUES_FIX_PROMPT before starting
TRY after every file edit to test if it is working by importing its things in `python -c` command and prints `ok` if passes
ALWAYS CHECK CURRENT PROJECT SITUATION BEFORE PROCEEDING
ALWAYS use edit_file tool to edit tasks when finishing
ALWAYS COMPLETE FULL PHASE TASKS, not one of them

- [x] 1. Phase 1: Testing Infrastructure & Critical Import Fixes





  - Fix HTTP status code import collisions across all endpoint files [you could try to import all files and see errors using `python -c`]
  - Fix Dataset model index definitions
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 4.1, 4.2, 4.3, 4.4, 13.1, 13.2, 13.3, 13.4_

- [ ]* 1.3 Write property test for service constructor dependencies
  - **Property 5: Service Constructor Dependencies**
  - **Validates: Requirements 5.2**

- [ ]* 1.4 Write property test for repository inheritance
  - **Property 18: Repository Class Inheritance**
  - **Validates: Requirements 13.2**



- [x] 1.5 Fix api_keys.py endpoint imports
  - Add `from fastapi import status as http_status`
  - Replace status code references


  - Keep APIKeyStatus enum import unchanged
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 1.6 Fix crawl_jobs.py endpoint imports


  - Add `from fastapi import status as http_status`
  - Replace status code references
  - Keep CrawlJobStatus enum import unchanged
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 1.7 Fix remaining endpoint files (datasets, exports, health, notifications, projects, storage, users, validation)
  - Update all endpoint files with http_status alias


  - Ensure consistent import pattern across all files
  - _Requirements: 1.1, 1.2, 1.3, 1.4_



- [ ]* 1.8 Write property test for HTTP status import consistency
  - **Property 1: HTTP Status Import Consistency**
  - **Validates: Requirements 1.2, 1.4**

- [x] 1.9 Update Dataset model indexes
  - Change Index("ix_datasets_user_id", "user_id") to Index("ix_datasets_user_id", user_id)
  - Update all other index definitions
  - _Requirements: 4.1, 4.2_

- [x] 1.10 Verify other models have correct index syntax
  - Check CrawlJob, Project, Notification models
  - Fix any string-based index definitions
  - _Requirements: 4.1, 4.4_

- [ ]* 1.11 Write property test for SQLAlchemy index definitions
  - **Property 7: SQLAlchemy Index Definitions**
  - **Validates: Requirements 4.1, 4.4**

- [x] 2. Phase 2: Service Layer Architecture & PolicyService Implementation



  - Create missing PolicyService and infrastructure
  - Fix repository method call signatures across all services
  - Fix missing required parameters in service method calls
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 6.1, 6.2, 6.3, 6.4, 8.1, 8.2, 8.3, 8.4_

- [x] 2.1 Implement PolicyService class


  - Create backend/services/policy.py
  - Implement __init__ with repository dependencies
  - Add create_archival_policy method
  - Add create_cleanup_policy method
  - Add execute_archival_policies method
  - Add execute_cleanup_policies method
  - _Requirements: 6.1, 6.2, 6.3_

- [x] 2.2 Create PolicyService dependency injection


  - Add get_policy_service factory in backend/api/dependencies.py
  - Add PolicyServiceDep type in backend/api/types.py
  - _Requirements: 6.4_

- [ ]* 2.3 Write unit tests for PolicyService
  - Test create_archival_policy with mocked repository
  - Test create_cleanup_policy with mocked repository
  - Test policy execution methods
  - _Requirements: 6.1, 6.2, 6.3_



- [x] 2.4 Fix dataset service repository calls
  - Fix create() calls: await repo.create(**data)
  - Fix update() calls: await repo.update(instance, **updates)
  - Fix get() calls: await repo.get_by_id(id)


  - _Requirements: 2.1, 2.2, 2.3_

- [x] 2.5 Fix notification service repository calls


  - Fix create() calls to use **kwargs
  - Fix get() calls to use get_by_id()
  - _Requirements: 2.1, 2.3_



- [x] 2.6 Fix project service repository calls
  - Fix create() calls to use **kwargs
  - Fix update() calls to pass instance


  - Fix get() calls to use get_by_id()
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 2.7 Fix user service repository calls
  - Fix update() calls to pass instance first
  - Ensure get_by_uuid() is used for UUID lookups
  - _Requirements: 2.2, 2.3_

- [x] 2.8 Fix validation service repository calls
  - Fix any incorrect repository method calls
  - _Requirements: 2.1, 2.2, 2.3_

- [ ]* 2.9 Write property test for repository create signature
  - **Property 2: Repository Create Method Signature**


  - **Validates: Requirements 2.1**

- [x]* 2.10 Write property test for repository update signature


  - **Property 3: Repository Update Method Signature**
  - **Validates: Requirements 2.2**

- [x]* 2.11 Write property test for repository get method naming

  - **Property 4: Repository Get Method Naming**



  - **Validates: Requirements 2.3**

- [x] 2.12 Fix missing user_id parameters
  - Find all get_job_with_ownership_check calls


  - Add user_id parameter from current_user context
  - _Requirements: 8.1_


- [x] 2.13 Fix missing category_name in validator calls
  - Find all validator.check_integrity calls
  - Add category_name parameter
  - _Requirements: 8.2_



- [ ]* 2.14 Write property test for required parameter completeness
  - **Property 9: Required Parameter Completeness**
  - **Validates: Requirements 8.1, 8.2**

- [x] 3. Phase 3: Crawl Job Service Refactoring & Type Safety





  - Refactor crawl_job service to use builder package
  - Fix type conversion and enum handling issues
  - Fix ActivityLog model and timestamp access
  - _Requirements: 3.1, 3.3, 3.4, 9.1, 9.2, 9.3, 9.4, 10.1, 10.2, 10.3, 10.4_










- [ ] 3.1 Analyze crawl_job.py for builder package usage
  - Identify duplicate crawling logic
  - Map service methods to builder.tasks equivalents


  - _Requirements: 3.1, 3.3_

- [x] 3.2 Replace crawling implementation with builder delegation


  - Import builder.tasks
  - Replace custom crawling with builder.tasks calls
  - Remove duplicate code




  - _Requirements: 3.1, 3.3_

- [ ] 3.3 Update crawl_job service tests
  - Mock builder.tasks in tests
  - Verify delegation works correctly
  - _Requirements: 3.3_

- [ ]* 3.4 Write property test for builder package delegation
  - **Property 8: Builder Package Delegation**
  - **Validates: Requirements 3.3**





- [ ] 3.5 Create type conversion utility functions
  - Implement uuid_to_int() helper


  - Implement ensure_enum() helper




  - _Requirements: 9.1, 9.2_

- [x] 3.6 Fix UUID to int conversions in services


  - Add explicit conversions where UUID passed to int parameter
  - Use uuid_to_int() utility
  - _Requirements: 9.1_

- [ ] 3.7 Fix enum value passing in Azure storage
  - Change priority.value to priority in rehydrate_blob
  - Fix other enum value issues
  - _Requirements: 9.2_

- [ ] 3.8 Fix model attribute name errors
  - Change properties.metadata_ to properties.metadata


  - Fix other attribute name issues
  - _Requirements: 9.3_



- [ ]* 3.9 Write property test for type conversion explicitness
  - **Property 10: Type Conversion Explicitness**
  - **Validates: Requirements 9.1**

- [ ]* 3.10 Write property test for enum value passing
  - **Property 11: Enum Value Passing**
  - **Validates: Requirements 9.2**

- [ ] 3.11 Verify ActivityLog model structure
  - Ensure ActivityLog extends TimestampMixin
  - Verify created_at is a column
  - _Requirements: 10.1_

- [ ] 3.12 Fix timestamp access across codebase
  - Search for .created_at() method calls
  - Replace with .created_at property access
  - _Requirements: 10.2, 10.3_

- [ ]* 3.13 Write property test for timestamp column access
  - **Property 12: Timestamp Column Access**
  - **Validates: Requirements 10.2**

- [x] 4. Phase 4: Documentation & OpenAPI Specifications





  - Add comprehensive documentation to all endpoint files
  - Add comprehensive documentation to all repository files
  - Add operation_id to all endpoint decorators
  - Add OpenAPI response examples
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 11.1, 11.2, 11.3, 11.4_

- [x] 4.1 Add module docstrings to endpoint files


  - Add comprehensive module docstring to each endpoint file
  - Document all endpoints in the module
  - Document authentication requirements
  - _Requirements: 7.1, 7.4_

- [x] 4.2 Add operation_id to all endpoint decorators


  - Add operation_id parameter to all @router decorators
  - Use camelCase naming convention
  - _Requirements: 7.2_

- [x] 4.3 Add OpenAPI response examples

  - Add example response bodies to responses parameter
  - Include success and error examples
  - _Requirements: 7.3_

- [x] 4.4 Add module docstrings to repository files


  - Add comprehensive module docstring to each repository
  - Document repository purpose and methods
  - _Requirements: 11.1_

- [x] 4.5 Add class and method docstrings to repositories


  - Add class docstrings to all repository classes
  - Add method docstrings with Args, Returns, Raises
  - _Requirements: 11.2, 11.3_

- [ ]* 4.6 Write property test for module docstring presence
  - **Property 13: Module Docstring Presence**
  - **Validates: Requirements 7.1, 11.1**

- [ ]* 4.7 Write property test for endpoint operation IDs
  - **Property 14: Endpoint Operation IDs**
  - **Validates: Requirements 7.2**



- [x] 5. Phase 5: Endpoint Patterns & Error Handling Standardization



  - Create authorization helper functions
  - Standardize endpoint patterns and error handling
  - Run MyPy type checking and fix all errors
  - _Requirements: 8.4, 9.4, 12.1, 12.2, 12.3, 12.4_

- [x] 5.1 Create authorization helper functions


  - Implement require_admin() in backend/api/dependencies.py
  - Implement require_role() for flexible role checking
  - _Requirements: 12.1_

- [x] 5.2 Update policy endpoints to use helpers


  - Replace inline admin checks with require_admin()
  - Ensure consistent authorization pattern
  - _Requirements: 12.1_

- [x] 5.3 Verify all endpoints use response models


  - Check all endpoint decorators have response_model
  - Add missing response models
  - _Requirements: 12.2_

- [x] 5.4 Standardize error handling in endpoints


  - Ensure try/except blocks convert to HTTPException
  - Use consistent status codes for error types
  - _Requirements: 12.3_

- [ ]* 5.5 Write property test for admin authorization pattern
  - **Property 16: Admin Authorization Pattern**
  - **Validates: Requirements 12.1**

- [ ]* 5.6 Write property test for response model usage
  - **Property 15: Response Model Usage**
  - **Validates: Requirements 12.2**

- [ ]* 5.7 Write property test for exception conversion
  - **Property 17: Exception to HTTPException Conversion**
  - **Validates: Requirements 12.3**

- [x] 5.8 Run MyPy and collect errors


  - Execute: uv run mypy backend/
  - Document all type errors
  - _Requirements: 8.4, 9.4_

- [x] 5.9 Fix type errors in services


  - Address type mismatches
  - Add missing type annotations
  - _Requirements: 8.4, 9.4_

- [x] 5.10 Fix type errors in repositories

  - Address type mismatches
  - Ensure BaseRepository compliance
  - _Requirements: 8.4, 9.4_

- [x] 5.11 Fix type errors in endpoints

  - Address type mismatches
  - Ensure proper type annotations
  - _Requirements: 8.4, 9.4_

- [x] 5.12 Checkpoint - Ensure all tests pass


  - Ensure all tests pass, ask the user if questions arise.


- [-] 6. Phase 6: Documentation & Final Verification


  - Update ARCHITECTURE.md documentation
  - Create migration guide
  - Final compliance verification
  - _Requirements: All_


- [x] 6.1 Update architecture documentation

  - Document http_status import pattern
  - Document repository method signatures
  - Document service dependency injection
  - Add PolicyService example
  - _Requirements: All_


- [x] 6.2 Create migration guide

  - Document common mistakes and fixes
  - Provide before/after examples
  - Add checklist for new code
  - _Requirements: All_

- [ ] 6.3 Final Checkpoint - Verify all compliance
  - Ensure all tests pass, ask the user if questions arise.
