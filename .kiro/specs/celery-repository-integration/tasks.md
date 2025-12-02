# Implementation Plan

- [x] 1. Update Repository Layer with Task Management Methods




  - Add new methods to CrawlJobRepository and ImageRepository for task-related operations
  - Ensure all methods use AsyncSession properly
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

- [ ] 1.1 Add task management methods to CrawlJobRepository

















  - Implement `add_task_id(job_id, task_id)` method
  - Implement `update_progress(job_id, progress, completed_chunks, active_chunks)` method
  - Implement `update_chunk_status(job_id, chunk_data)` method
  - Implement `mark_completed(job_id)` method
  - Implement `mark_failed(job_id, error)` method
  - Implement `get_active_tasks(job_id)` method
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

-

- [ ] 1.2 Write property test for CrawlJobRepository task management











  - **Property 2: Task ID Persistence**
  - **Validates: Requirements 1.3**



- [ ] 1.3 Add image management methods to ImageRepository



  - Implement `create_from_download(job_id, image_data)` method
  - Implement `mark_validated(image_id, validation_result)` method
  - Implement `get_by_job(job_id)` method

  - Implement `count_by_job(job_id)` method
  - _Requirements: 9.6, 9.7_
-

- [ ] 1.4 Write property test for ImageRepository image creation



  - **Property 13: Image Creation from Download**
  - **Validates: Requirements 6.1**

- [ ] 2. Create Request/Response Schemas



  - Define Pydantic schemas for all new API endpoints
  - Ensure proper validation and serialization
  - _Requirements: 1.1, 4.1, 5.1, 7.4_

- [ ] 2.1 Create crawl job schemas
  - Create `JobStartResponse` schema in `backend/schemas/crawl_jobs.py`
  - Create `JobStopResponse` schema
  - Create `JobProgressResponse` schema
  - _Requirements: 1.1, 4.1_

- [ ] 2.2 Create validation schemas
  - Create `ValidationRequest` schema in `backend/schemas/validation.py`
  - Create `ValidationResponse` schema
  - _Requirements: 5.1_

- [ ]* 2.3 Write unit tests for schema validation
  - Test schema validation with valid and invalid data
  - Test serialization and deserialization
  - _Requirements: 7.4_
-


- [ ] 3. Implement Service Layer Orchestration

  - Create service methods for task dispatch and result handling
  - Implement business logic for job lifecycle management
- [ ] 3.1 Implement CrawlJobService.start_job method

  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 3.1 Implement CrawlJobService.start_job method

  - Validate job ownership and status
  - Calculate total chunks (keywords × engines)
  - Dispatch download tasks for each keyword-engine combination
  - Store task IDs in database
  - Update job status to 'running'
  - Create notification

  --_Requirements: 1.1, 1.2, 1.3, 1.5, 10.1, 10.2_



- [ ] 3.2 Write property test for job start correctness



  - **Property 3: Job Start Correctness**
  - **Validates: Requirements 1.1, 1.5**

- [ ] 3.3 Write property test for task dispatch serialization



  - **Property 1: Task Dispatch Serialization**
  - **Validates: Requirements 1.2, 2.1, 2.2**

- [ ] 3.4 Write property test for job start idempotency



  - **Property 4: Job Start Idempotency**
  - **Validates: Requirements 1.4, 11.1**

- [ ] 3.5 Implement CrawlJobService.stop_job method



  - Validate job ownership
  - Retrieve active task IDs
  - Revoke tasks using celery_core.app.control.revoke()
  - Update job status to 'cancelled'
  - Create notification
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 10.5_
-



- [ ] 3.6 Write property test for job stop completeness


  - **Property 9: Job Stop Completeness**
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**



- [ ] 3.7 Write property test for job stop idempotency



  - **Property 10: Job Stop Idempotency**
  - **Validates: Requirements 4.5, 11.2**

- [ ] 3.8 Write property test for atomic job stop



  - **Property 24: Atomic Job Stop**
  - **Validates: Requirements 10.5**
 

- [-] 3.9 Implement CrawlJobService.handle_task_completion method


  - Update chunk counters (completed_chunks++, active_chunks--)
  - Calculate progress percentage
  - Create image records for successful downloads
  - Increment failed_chunks for failures
  - Mark job as completed when all chunks done
  - Create completion notification
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 6.1, 6.2, 6.3, 6.5, 10.3_

- [ ]* 3.10 Write property test for chunk counter invariant
  - **Property 5: Chunk Counter Invariant**
  - **Validates: Requirements 3.1, 3.2**

- [ ]* 3.11 Write property test for progress calculation
  - **Property 6: Progress Calculation**
  - **Validates: Requirements 3.3**

- [ ]* 3.12 Write property test for job completion detection
  - **Property 7: Job Completion Detection**
  - **Validates: Requirements 3.4, 6.5**

- [ ]* 3.13 Write property test for download counter update
  - **Property 14: Download Counter Update**
  - **Validates: Requirements 6.2**

- [ ]* 3.14 Write property test for failure counter update
  - **Property 15: Failure Counter Update**
  - **Validates: Requirements 6.3**

- [ ]* 3.15 Write property test for task result processing
  - **Property 23: Task Result Processing**
  - **Validates: Requirements 10.3**

- [ ] 3.16 Implement ValidationService.validate_job_images method
  - Retrieve all images for job
  - Select validation task based on level (fast/medium/slow)
  - Dispatch validation tasks
  - Return task IDs for tracking
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 10.4_

- [ ]* 3.17 Write property test for validation task selection
  - **Property 11: Validation Task Selection**
  - **Validates: Requirements 5.2, 5.3, 5.4, 5.5**

- [ ] 3.18 Implement ValidationService.handle_validation_result method
  - Update image validation status
  - Update is_valid and is_duplicate flags
  - Store validation metadata
  - _Requirements: 5.6_

- [ ]* 3.19 Write property test for validation result persistence
  - **Property 12: Validation Result Persistence**
  - **Validates: Requirements 5.6**

- [ ] 4. Implement API Endpoints for Crawl Jobs
  - Create FastAPI endpoints for job management
  - Implement authentication and authorization
  - _Requirements: 1.1, 1.4, 3.5, 4.1, 4.5, 7.1, 7.2, 7.3, 8.1, 8.2, 8.3, 8.4_

- [ ] 4.1 Implement POST /api/v1/jobs/{job_id}/start endpoint
  - Add endpoint to `backend/api/v1/endpoints/crawl_jobs.py`
  - Inject AsyncSession and current_user dependencies
  - Call CrawlJobService.start_job
  - Handle errors and return appropriate HTTP status codes
  - _Requirements: 1.1, 1.4, 7.1, 7.2, 7.3, 8.1, 8.2, 8.3, 8.4_

- [ ]* 4.2 Write property test for authentication enforcement
  - **Property 16: Authentication Enforcement**
  - **Validates: Requirements 8.1, 8.2**

- [ ]* 4.3 Write property test for authorization enforcement
  - **Property 17: Authorization Enforcement**
  - **Validates: Requirements 7.3, 8.4**

- [ ]* 4.4 Write property test for resource not found handling
  - **Property 18: Resource Not Found Handling**
  - **Validates: Requirements 7.2**

- [ ] 4.5 Implement POST /api/v1/jobs/{job_id}/stop endpoint
  - Add endpoint to `backend/api/v1/endpoints/crawl_jobs.py`
  - Inject AsyncSession and current_user dependencies
  - Call CrawlJobService.stop_job
  - Handle errors and return appropriate HTTP status codes
  - _Requirements: 4.1, 4.5, 7.1, 7.2, 7.3, 8.1, 8.2, 8.3, 8.4_

- [ ] 4.6 Implement GET /api/v1/jobs/{job_id}/progress endpoint
  - Add endpoint to `backend/api/v1/endpoints/crawl_jobs.py`
  - Inject AsyncSession and current_user dependencies
  - Retrieve job from repository
  - Return progress response with chunk statistics
  - _Requirements: 3.5, 7.2, 7.3, 8.1, 8.2, 8.3, 8.4_

- [ ]* 4.7 Write property test for progress endpoint accuracy
  - **Property 8: Progress Endpoint Accuracy**
  - **Validates: Requirements 3.5**

- [ ]* 4.8 Write unit tests for crawl job endpoints
  - Test successful job start
  - Test successful job stop
  - Test progress retrieval
  - Test error scenarios (404, 403, 400, 500)
  - _Requirements: 1.1, 4.1, 3.5, 7.1, 7.2, 7.3_

- [ ] 5. Implement API Endpoints for Validation
  - Create FastAPI endpoints for image validation
  - Implement authentication and authorization
  - _Requirements: 5.1, 7.1, 7.2, 7.3, 7.4, 8.1, 8.2, 8.3, 8.4_

- [ ] 5.1 Implement POST /api/v1/validation/job/{job_id} endpoint
  - Add endpoint to `backend/api/v1/endpoints/validation.py`
  - Inject AsyncSession and current_user dependencies
  - Validate request schema (ValidationRequest)
  - Call ValidationService.validate_job_images
  - Handle errors and return appropriate HTTP status codes
  - _Requirements: 5.1, 7.1, 7.2, 7.3, 7.4, 8.1, 8.2, 8.3, 8.4_

- [ ]* 5.2 Write property test for validation error handling
  - **Property 19: Validation Error Handling**
  - **Validates: Requirements 7.4**

- [ ]* 5.3 Write unit tests for validation endpoints
  - Test successful validation dispatch
  - Test validation with different levels (fast, medium, slow)
  - Test error scenarios (404, 403, 422)
  - _Requirements: 5.1, 7.1, 7.2, 7.3, 7.4_

- [ ] 6. Implement Error Handling and Logging
  - Add comprehensive error handling across all layers
  - Implement structured logging with context
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 8.5_

- [ ] 6.1 Add error handling to service layer
  - Catch and re-raise exceptions with appropriate error types
  - Add structured logging for all errors
  - Include request context in logs (job_id, user_id, request_id)
  - _Requirements: 7.1, 7.5, 8.5_

- [ ]* 6.2 Write property test for task dispatch error handling
  - **Property 20: Task Dispatch Error Handling**
  - **Validates: Requirements 7.1**

- [ ] 6.3 Add error handling to API endpoints
  - Map service exceptions to HTTP status codes
  - Return consistent error response format
  - Include error details and request_id
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ]* 6.4 Write unit tests for error handling
  - Test all error scenarios (400, 401, 403, 404, 422, 500)
  - Verify error response format
  - Verify logging occurs for all errors
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 7. Implement Idempotency and Deduplication
  - Add idempotency checks for job operations
  - Implement result deduplication
  - _Requirements: 11.1, 11.2, 11.3, 11.4_

- [ ] 7.1 Add idempotency checks to CrawlJobService
  - Check job status before starting (return existing tasks if running)
  - Check job status before stopping (return success if already stopped)
  - _Requirements: 11.1, 11.2_

- [ ] 7.2 Implement result deduplication in task completion handler
  - Track processed task IDs to prevent duplicate processing
  - Use database transaction to ensure atomic updates
  - _Requirements: 11.3_

- [ ]* 7.3 Write property test for result deduplication
  - **Property 25: Result Deduplication**
  - **Validates: Requirements 11.3**

- [ ] 7.4 Implement retry logic with counter reset
  - Add retry endpoint (POST /api/v1/jobs/{job_id}/retry)
  - Reset chunk counters before dispatching new tasks
  - _Requirements: 11.4_

- [ ]* 7.5 Write property test for retry counter reset
  - **Property 26: Retry Counter Reset**
  - **Validates: Requirements 11.4**

- [ ] 8. Add Integration Tests
  - Test end-to-end workflows
  - Verify database state at each step
  - _Requirements: All_

- [ ]* 8.1 Write integration test for job lifecycle
  - Create job → Start job → Monitor progress → Complete job
  - Verify database state at each step
  - Verify notifications are created
  - _Requirements: 1.1, 3.1, 3.2, 3.3, 3.4, 6.5_

- [ ]* 8.2 Write integration test for job cancellation
  - Create job → Start job → Stop job
  - Verify tasks are revoked
  - Verify job status is updated
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ]* 8.3 Write integration test for validation workflow
  - Create job → Download images → Validate images
  - Verify validation results are stored
  - Test all validation levels
  - _Requirements: 5.1, 5.2, 5.6_

- [ ]* 8.4 Write integration test for error scenarios
  - Test authentication failures
  - Test authorization failures
  - Test invalid job states
  - Test task dispatch failures
  - _Requirements: 7.1, 7.2, 7.3, 8.1, 8.2_

- [ ] 9. Update API Documentation
  - Update OpenAPI schema with new endpoints
  - Add request/response examples
  - Document error codes
  - _Requirements: All_

- [ ] 9.1 Update OpenAPI schema
  - Add endpoint definitions for /jobs/{job_id}/start
  - Add endpoint definitions for /jobs/{job_id}/stop
  - Add endpoint definitions for /jobs/{job_id}/progress
  - Add endpoint definitions for /validation/job/{job_id}
  - Include request/response schemas
  - _Requirements: 1.1, 4.1, 3.5, 5.1_

- [ ] 9.2 Add API documentation examples
  - Add cURL examples for each endpoint
  - Add Python client examples
  - Add error response examples
  - Document authentication requirements
  - _Requirements: All_

- [ ] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
