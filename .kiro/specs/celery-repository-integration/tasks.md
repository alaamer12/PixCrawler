# Implementation Plan
# USE .venv for running python and python scripts
- [ ] 1. Update Repository Layer with Task Management Methods
  - Add new methods to CrawlJobRepository and ImageRepository for task-related operations
  - Ensure all methods use AsyncSession properly
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

- [ ] 1.1 Add task management methods to CrawlJobRepository
  - ✅ `update_progress()` exists (persists progress, downloaded_images, valid_images)
  - ✅ `update_chunk_counts()` exists (persists active_chunks, completed_chunks, failed_chunks)
  - ✅ `update_status()` exists (persists status, completed_at, progress)
  - ❌ Missing: `add_task_id(job_id, task_id)` method
  - ❌ Missing: `mark_completed(job_id)` convenience method
  - ❌ Missing: `mark_failed(job_id, error)` convenience method
  - ❌ Missing: `get_active_tasks(job_id)` method
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 1.2 Complete missing CrawlJobRepository methods
  - Implement `add_task_id(job_id, task_id)` to append task ID to task_ids JSONB array
  - Implement `mark_completed(job_id)` as convenience wrapper for update_status
  - Implement `mark_failed(job_id, error)` as convenience wrapper for update_status
  - Implement `get_active_tasks(job_id)` to retrieve task_ids array
  - _Requirements: 9.1, 9.4, 9.5_

- [ ]* 1.3 Write property test for CrawlJobRepository task management
  - **Property 2: Task ID Persistence**
  - **Validates: Requirements 1.3**

- [ ] 1.4 Add image management methods to ImageRepository
  - ✅ `get_by_crawl_job()` exists (renamed from get_by_job)
  - ✅ `count_by_job()` exists
  - ✅ `bulk_create()` exists (can be used for create_from_download)
  - ❌ Missing: `mark_validated(image_id, validation_result)` method
  - _Requirements: 9.6, 9.7_

- [ ] 1.5 Complete missing ImageRepository methods
  - Implement `mark_validated(image_id, validation_result)` to update is_valid, is_duplicate, metadata
  - _Requirements: 9.7_

- [ ]* 1.6 Write property test for ImageRepository image creation
  - **Property 13: Image Creation from Download**
  - **Validates: Requirements 6.1**

- [x] 2. Create Request/Response Schemas





  - Define Pydantic schemas for all new API endpoints
  - Ensure proper validation and serialization
  - _Requirements: 1.1, 4.1, 5.1, 7.4_

- [x] 2.1 Create crawl job schemas


  - ✅ Schemas exist in `backend/schemas/crawl_jobs.py`
  - ✅ `CrawlJobResponse` exists (covers job details)
  - ✅ `CrawlJobProgress` exists (covers progress endpoint)
  - ❌ Missing: `JobStartResponse` (for start endpoint with task_ids)
  - ❌ Missing: `JobStopResponse` (for stop endpoint with revoked count)
  - _Requirements: 1.1, 4.1_


- [x] 2.2 Add missing crawl job response schemas
  - Create `JobStartResponse` with job_id, status, task_ids, total_chunks, message
  - Create `JobStopResponse` with job_id, status, revoked_tasks, message
  - _Requirements: 1.1, 4.1_



- [x] 2.3 Create validation schemas
  - ✅ Validation schemas exist in `backend/schemas/validation.py`
  - ✅ `ValidationAnalyzeRequest`, `ValidationBatchRequest` exist
  - ✅ `ValidationJobResponse`, `ValidationResultsResponse` exist
  - _Requirements: 5.1_

- [ ]* 2.4 Write unit tests for schema validation
  - Test schema validation with valid and invalid data
  - Test serialization and deserialization
  - _Requirements: 7.4_


- [x] 3. Implement Service Layer Orchestration




  - Create service methods for task dispatch and result handling
  - Implement business logic for job lifecycle management
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 3.1 Implement CrawlJobService.start_job method


  - ✅ `create_job()` exists with rate limiting
  - ❌ Missing: Celery task dispatch logic
  - ❌ Missing: Calculate total_chunks (keywords × engines)
  - ❌ Missing: Store task IDs in database
  - ❌ Missing: Update job status to 'running' with total_chunks
  - Note: Currently uses BackgroundTasks, needs Celery integration
  - _Requirements: 1.1, 1.2, 1.3, 1.5, 10.1, 10.2_

- [x] 3.2 Add Celery task dispatch to start_job


  - Import Celery tasks from builder/validator packages
  - Calculate total_chunks = len(keywords) × len(engines)
  - Dispatch download task for each keyword-engine combination
  - Collect task IDs and store using add_task_id()
  - Update job status to 'running' with total_chunks set
  - _Requirements: 1.1, 1.2, 1.3, 1.5_

- [ ]* 3.3 Write property test for job start correctness
  - **Property 3: Job Start Correctness**
  - **Validates: Requirements 1.1, 1.5**

- [ ]* 3.4 Write property test for task dispatch serialization
  - **Property 1: Task Dispatch Serialization**
  - **Validates: Requirements 1.2, 2.1, 2.2**

- [ ]* 3.5 Write property test for job start idempotency
  - **Property 4: Job Start Idempotency**
  - **Validates: Requirements 1.4, 11.1**

- [x] 3.6 Implement CrawlJobService.stop_job method


  - ✅ `cancel_job()` exists with full implementation
  - ✅ Validates job ownership
  - ✅ Revokes Celery tasks
  - ✅ Updates job status to 'cancelled'
  - ✅ Logs activity
  - ✅ Broadcasts via Supabase real-time
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 10.5_

- [ ]* 3.7 Write property test for job stop completeness
  - **Property 9: Job Stop Completeness**
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**

- [ ]* 3.8 Write property test for job stop idempotency
  - **Property 10: Job Stop Idempotency**
  - **Validates: Requirements 4.5, 11.2**

- [ ]* 3.9 Write property test for atomic job stop
  - **Property 24: Atomic Job Stop**
  - **Validates: Requirements 10.5**

- [x] 3.10 Implement CrawlJobService.handle_task_completion method


  - Create new method to handle Celery task completion callbacks
  - Update chunk counters using update_chunk_counts()
  - Calculate progress percentage
  - Create image records using bulk_create()
  - Increment failed_chunks for failures
  - Mark job as completed when all chunks done
  - Create completion notification
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 6.1, 6.2, 6.3, 6.5, 10.3_

- [ ]* 3.11 Write property test for chunk counter invariant
  - **Property 5: Chunk Counter Invariant**
  - **Validates: Requirements 3.1, 3.2**

- [ ]* 3.12 Write property test for progress calculation
  - **Property 6: Progress Calculation**
  - **Validates: Requirements 3.3**

- [ ]* 3.13 Write property test for job completion detection
  - **Property 7: Job Completion Detection**
  - **Validates: Requirements 3.4, 6.5**

- [ ]* 3.14 Write property test for download counter update
  - **Property 14: Download Counter Update**
  - **Validates: Requirements 6.2**

- [ ]* 3.15 Write property test for failure counter update
  - **Property 15: Failure Counter Update**
  - **Validates: Requirements 6.3**

- [ ]* 3.16 Write property test for task result processing
  - **Property 23: Task Result Processing**
  - **Validates: Requirements 10.3**

- [x] 3.17 Implement ValidationService.validate_job_images method


  - Retrieve all images for job using image_repo.get_by_crawl_job()
  - Select validation task based on level (fast/medium/slow)
  - Dispatch validation tasks via Celery
  - Return task IDs for tracking
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 10.4_

- [ ]* 3.18 Write property test for validation task selection
  - **Property 11: Validation Task Selection**
  - **Validates: Requirements 5.2, 5.3, 5.4, 5.5**

- [x] 3.19 Implement ValidationService.handle_validation_result method


  - Create new method to handle validation task completion
  - Update image validation status using mark_validated()
  - Update is_valid and is_duplicate flags
  - Store validation metadata
  - _Requirements: 5.6_

- [ ]* 3.20 Write property test for validation result persistence
  - **Property 12: Validation Result Persistence**
  - **Validates: Requirements 5.6**

- [x] 4. Implement API Endpoints for Crawl Jobs
  - Create FastAPI endpoints for job management
  - Implement authentication and authorization
  - _Requirements: 1.1, 1.4, 3.5, 4.1, 4.5, 7.1, 7.2, 7.3, 8.1, 8.2, 8.3, 8.4_

- [x] 4.1 Implement POST /api/v1/jobs/{job_id}/start endpoint




  - ✅ POST /api/v1/jobs/ exists (creates and starts job)
  - ❌ Missing: Separate POST /api/v1/jobs/{job_id}/start endpoint
  - ❌ Missing: Return JobStartResponse with task_ids
  - Note: Current implementation creates and starts in one call
  - _Requirements: 1.1, 1.4, 7.1, 7.2, 7.3, 8.1, 8.2, 8.3, 8.4_

- [x] 4.2 Add POST /api/v1/jobs/{job_id}/start endpoint






  - Add new endpoint for starting existing pending jobs
  - Call CrawlJobService.start_job with job_id
  - Return JobStartResponse with task_ids, total_chunks
  - Handle errors (404, 403, 400 for invalid status)
  - _Requirements: 1.1, 1.4, 7.1, 7.2, 7.3, 8.1, 8.2, 8.3, 8.4_

- [ ]* 4.3 Write property test for authentication enforcement
  - **Property 16: Authentication Enforcement**
  - **Validates: Requirements 8.1, 8.2**

- [ ]* 4.4 Write property test for authorization enforcement
  - **Property 17: Authorization Enforcement**
  - **Validates: Requirements 7.3, 8.4**

- [ ]* 4.5 Write property test for resource not found handling
  - **Property 18: Resource Not Found Handling**
  - **Validates: Requirements 7.2**
-

- [x] 4.6 Implement POST /api/v1/jobs/{job_id}/stop endpoint




  - ✅ POST /api/v1/jobs/{job_id}/cancel exists
  - ✅ Calls CrawlJobService.cancel_job
  - ✅ Handles errors appropriately
  - ❌ Missing: Return JobStopResponse with revoked_tasks count
  - _Requirements: 4.1, 4.5, 7.1, 7.2, 7.3, 8.1, 8.2, 8.3, 8.4_

- [x] 4.7 Update cancel endpoint to return JobStopResponse






  - Modify response to include revoked_tasks count
  - Use JobStopResponse schema
  - _Requirements: 4.1, 4.5_
-

- [x] 4.8 Implement GET /api/v1/jobs/{job_id}/progress endpoint



  - ✅ Endpoint exists
  - ✅ Returns CrawlJobProgress with chunk statistics
  - ✅ Handles authentication and authorization
  - _Requirements: 3.5, 7.2, 7.3, 8.1, 8.2, 8.3, 8.4_

- [ ]* 4.9 Write property test for progress endpoint accuracy
  - **Property 8: Progress Endpoint Accuracy**
  - **Validates: Requirements 3.5**

- [ ]* 4.10 Write unit tests for crawl job endpoints
  - Test successful job start
  - Test successful job stop
  - Test progress retrieval
  - Test error scenarios (404, 403, 400, 500)
  - _Requirements: 1.1, 4.1, 3.5, 7.1, 7.2, 7.3_

- [x] 5. Implement API Endpoints for Validation





  - Create FastAPI endpoints for image validation
  - Implement authentication and authorization
  - _Requirements: 5.1, 7.1, 7.2, 7.3, 7.4, 8.1, 8.2, 8.3, 8.4_

- [x] 5.1 Implement POST /api/v1/validation/job/{job_id} endpoint





  - ✅ Validation endpoints exist in `backend/api/v1/endpoints/validation.py`
  - ✅ POST /validation/batch/ exists (similar functionality)
  - ❌ Missing: POST /validation/job/{job_id} specific endpoint
  - ❌ Missing: ValidationService implementation (currently stubs)
  - _Requirements: 5.1, 7.1, 7.2, 7.3, 7.4, 8.1, 8.2, 8.3, 8.4_

- [x] 5.2 Add POST /api/v1/validation/job/{job_id} endpoint

  - Add new endpoint for job-specific validation
  - Accept ValidationRequest with level (fast/medium/slow)
  - Call ValidationService.validate_job_images
  - Return ValidationResponse with task_ids
  - _Requirements: 5.1, 7.1, 7.2, 7.3, 7.4, 8.1, 8.2, 8.3, 8.4_

- [ ]* 5.3 Write property test for validation error handling
  - **Property 19: Validation Error Handling**
  - **Validates: Requirements 7.4**

- [ ]* 5.4 Write unit tests for validation endpoints
  - Test successful validation dispatch
  - Test validation with different levels (fast, medium, slow)
  - Test error scenarios (404, 403, 422)
  - _Requirements: 5.1, 7.1, 7.2, 7.3, 7.4_

- [x] 6. Implement Error Handling and Logging





  - Add comprehensive error handling across all layers
  - Implement structured logging with context
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 8.5_

- [x] 6.1 Add error handling to service layer


  - ✅ Service layer uses custom exceptions (NotFoundError, ValidationError)
  - ✅ Structured logging with Loguru
  - ✅ Context included in logs (job_id, user_id)
  - _Requirements: 7.1, 7.5, 8.5_

- [ ]* 6.2 Write property test for task dispatch error handling
  - **Property 20: Task Dispatch Error Handling**
  - **Validates: Requirements 7.1**

- [x] 6.3 Add error handling to API endpoints


  - ✅ Endpoints map exceptions to HTTP status codes
  - ✅ Consistent error response format via HTTPException
  - ✅ Error details included in responses
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ]* 6.4 Write unit tests for error handling
  - Test all error scenarios (400, 401, 403, 404, 422, 500)
  - Verify error response format
  - Verify logging occurs for all errors
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 7. Implement Idempotency and Deduplication






  - Add idempotency checks for job operations
  - Implement result deduplication
  - _Requirements: 11.1, 11.2, 11.3, 11.4_

- [x] 7.1 Add idempotency checks to CrawlJobService.start_job


  - Check job status before starting
  - Return existing task_ids if job already running
  - Return 400 error if job not in pending status
  - _Requirements: 11.1_

- [x] 7.2 Add idempotency checks to CrawlJobService.stop_job


  - ✅ cancel_job validates status before stopping
  - ✅ Returns ValidationError if job not running/pending
  - _Requirements: 11.2_

- [x] 7.3 Implement result deduplication in task completion handler


  - Track processed task IDs to prevent duplicate processing
  - Use database transaction to ensure atomic updates
  - Check if task_id already processed before updating counters
  - _Requirements: 11.3_

- [ ]* 7.4 Write property test for result deduplication
  - **Property 25: Result Deduplication**
  - **Validates: Requirements 11.3**

- [x] 7.5 Implement retry logic with counter reset


  - ✅ POST /api/v1/jobs/{job_id}/retry exists
  - ✅ retry_job() resets progress and counters
  - ✅ Validates status (only failed/cancelled can retry)
  - _Requirements: 11.4_

- [ ]* 7.6 Write property test for retry counter reset
  - **Property 26: Retry Counter Reset**
  - **Validates: Requirements 11.4**

- [ ]* 8. Add Integration Tests
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

- [x] 9. Update API Documentation






  - Update OpenAPI schema with new endpoints
  - Add request/response examples
  - Document error codes
  - _Requirements: All_

- [x] 9.1 Update OpenAPI schema


  - ✅ Endpoints documented via FastAPI decorators
  - ✅ Request/response schemas defined
  - ✅ Error responses documented
  - ✅ OpenAPI auto-generated at /openapi.json
  - _Requirements: 1.1, 4.1, 3.5, 5.1_

- [x] 9.2 Add API documentation examples


  - Add cURdd API documor new endpoints (start, stop)
  - Add Python client examples
  - Update error response examples
  - Document Celery task integration
  - _Requirements: All_

- [x] 10. Checkpoint - Ensure all tests pass





  - Ensure all tests pass, ask the user if questions arise.
