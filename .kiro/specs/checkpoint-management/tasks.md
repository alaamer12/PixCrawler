# Implementation Plan: Checkpoint Management System

- [ ] 1. Set up database schema and infrastructure
  - Create PostgreSQL tables for job_checkpoints, chunk_checkpoints, engine_checkpoints, and download_checkpoints with proper indexes and partitioning
  - Configure Redis with appropriate TTL settings and connection pooling
  - Set up Azure Blob Storage containers for checkpoint archival
  - _Requirements: 2.1, 2.2, 10.1, 10.3_

- [ ] 2. Implement checkpoint data models
- [ ] 2.1 Create Pydantic models for all checkpoint types
  - Implement BaseCheckpoint with common fields (id, type, status, created_at, updated_at, metadata)
  - Implement JobCheckpoint with job-level fields (job_id, keywords, max_images, chunk tracking)
  - Implement ChunkCheckpoint with chunk-level fields (task_id, keyword, engines_queue, progress tracking)
  - Implement EngineCheckpoint with engine-level fields (engine_name, variations_queue, offset_ranges)
  - Implement DownloadCheckpoint with download-level fields (urls_discovered, download results, validation results)
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 2.2 Create supporting data models
  - Implement VariationAttempt model with retry strategy and error tracking
  - Implement URLMetadata, DownloadResult, DownloadFailure, DuplicateInfo, ValidationResult models
  - Add serialization/deserialization methods for all models
  - _Requirements: 1.3, 1.4, 5.2, 6.2, 6.4, 6.6_

- [ ]* 2.3 Write unit tests for checkpoint models
  - Test model validation with valid and invalid data
  - Test serialization to JSON and deserialization
  - Test default values and optional fields
  - _Requirements: 1.5_

- [ ] 3. Implement persistence layer
- [ ] 3.1 Create Redis checkpoint store adapter
  - Implement RedisCheckpointStore with save, get, update, delete methods
  - Add automatic compression for checkpoints >100KB using zstandard
  - Implement batch_update for performance optimization
  - Add TTL management with different durations for active/completed/failed checkpoints
  - _Requirements: 2.1, 2.7_

- [ ] 3.2 Create PostgreSQL checkpoint store adapter
  - Implement PostgreSQLCheckpointStore with save, get, update, query methods
  - Add optimistic locking for concurrent updates
  - Implement batch_save for bulk inserts
  - Add archive and cleanup_old methods
  - _Requirements: 2.2_

- [ ] 3.3 Create unified persistence manager
  - Implement CheckpointPersistence to coordinate Redis and PostgreSQL
  - Add fallback logic when Redis unavailable (write to PostgreSQL only)
  - Add retry queue when PostgreSQL unavailable (queue writes to Redis)
  - Implement cache-aside pattern for reads (Redis first, PostgreSQL fallback)
  - _Requirements: 2.3, 2.4, 2.5_

- [ ]* 3.4 Write unit tests for persistence layer
  - Test Redis adapter with fakeredis
  - Test PostgreSQL adapter with SQLite in-memory
  - Test compression/decompression logic
  - Test fallback scenarios
  - _Requirements: 2.3, 2.4_

- [ ] 4. Implement CheckpointManager core orchestrator
- [ ] 4.1 Create CheckpointManager class with CRUD operations
  - Implement create_job_checkpoint, create_chunk_checkpoint, create_engine_checkpoint, create_download_checkpoint
  - Implement update_checkpoint with atomic updates
  - Implement get_checkpoint with caching
  - Add query methods for filtering checkpoints by job_id, status, created_at
  - _Requirements: 3.1, 3.2, 4.1, 4.2, 5.1, 6.1_

- [ ] 4.2 Add checkpoint lifecycle management
  - Implement checkpoint status transitions (PENDING → IN_PROGRESS → COMPLETED/FAILED)
  - Add validation for state transitions
  - Implement checkpoint linking (previous_checkpoint_id for retries)
  - _Requirements: 4.4, 4.5_

- [ ]* 4.3 Write unit tests for CheckpointManager
  - Test CRUD operations for all checkpoint types
  - Test error handling and fallback logic
  - Test concurrent updates with race conditions
  - _Requirements: 3.6, 4.6_

- [ ] 5. Implement checkpoint resume logic
- [ ] 5.1 Create CheckpointResume class with reconciliation
  - Implement resume_job method to load job checkpoint and build resume context
  - Implement _reconcile_with_celery to query Celery task status
  - Add _is_stale method to detect stuck tasks (no update for 30 minutes)
  - Implement _build_resume_context to calculate remaining work
  - _Requirements: 3.2, 3.3, 3.4, 3.5, 4.7, 7.1, 7.2, 7.3_

- [ ] 5.2 Add resume point calculation
  - Implement _calculate_resume_point to determine where to resume within chunk
  - Extract last successful engine, variation, and offset from checkpoint
  - Calculate estimated remaining time based on historical performance
  - _Requirements: 5.6, 7.3_

- [ ] 5.3 Add notification integration for resume events
  - Implement _notify_user_resume to send notifications when job resumes
  - Include resume details (chunks to retry, estimated time)
  - _Requirements: 7.4_

- [ ]* 5.4 Write unit tests for resume logic
  - Test context building with various job states
  - Test Celery reconciliation with mocked results
  - Test stale checkpoint detection
  - _Requirements: 7.6_

- [ ] 6. Integrate checkpoints with Celery tasks
- [ ] 6.1 Create checkpoint decorator for tasks
  - Implement @with_checkpoint decorator to add checkpoint tracking
  - Create checkpoint at task start with task_id and metadata
  - Update checkpoint on task progress, success, and failure
  - Add error handling and traceback capture
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 6.2 Add checkpoint hooks to download tasks
  - Modify task_download_google, task_download_bing, task_download_baidu, task_download_duckduckgo
  - Add checkpoint_context parameter to tasks
  - Create chunk checkpoint at task start
  - Create engine checkpoint for each engine processed
  - Update checkpoints with progress (variations tried, offsets, images downloaded)
  - _Requirements: 4.1, 4.2, 4.3, 5.1, 5.2, 5.3_

- [ ] 6.3 Add download batch checkpoint tracking
  - Create download checkpoint for each batch of URLs
  - Track urls_attempted, urls_completed, urls_failed
  - Record successful_downloads with file metadata
  - Record failed_downloads with error details
  - Update checkpoint with duplicate detection results
  - Update checkpoint with validation results
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [ ]* 6.4 Write integration tests for Celery checkpoint integration
  - Test checkpoint updates from actual Celery tasks
  - Test task retry with checkpoint recovery
  - Test worker crash simulation
  - _Requirements: 4.6_

- [ ] 7. Implement checkpoint monitoring and diagnostics
- [ ] 7.1 Add structured logging for checkpoint operations
  - Log all checkpoint create, update, delete operations with job_id, chunk_id
  - Log checkpoint write failures with error details
  - Log slow checkpoint operations (>500ms) with timing
  - Log checkpoint validation errors with corrupted fields
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 7.2 Add metrics collection
  - Track write latency (p50, p95, p99) for Redis and PostgreSQL
  - Track read latency (p50, p95, p99) for Redis and PostgreSQL
  - Track cache hit rate
  - Track write failure rate
  - Track storage usage growth
  - _Requirements: 8.2, 8.3, 8.6_

- [ ] 7.3 Implement checkpoint health check
  - Verify Redis connectivity and response time
  - Verify PostgreSQL connectivity and response time
  - Check data consistency between Redis and PostgreSQL
  - Trigger alerts if health check fails
  - _Requirements: 8.7_

- [ ]* 7.4 Write unit tests for monitoring and diagnostics
  - Test logging with various checkpoint operations
  - Test metrics collection and aggregation
  - Test health check with Redis/PostgreSQL failures
  - _Requirements: 8.7_

- [ ] 8. Implement checkpoint cleanup and archival
- [ ] 8.1 Create CheckpointCleanup class
  - Implement cleanup_completed_jobs to archive checkpoints within 1 hour
  - Implement cleanup_failed_jobs to retain for 7 days before archival
  - Implement cleanup_old_checkpoints to move to cold storage after 30 days
  - Implement cleanup_ancient_checkpoints to delete after 90 days
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [ ] 8.2 Add archival to Azure Blob cold tier
  - Implement _archive_job_checkpoints to compress and upload to Azure
  - Clear from Redis after archival
  - Mark as archived in PostgreSQL
  - Implement retrieve_archived_checkpoint for cold storage retrieval
  - _Requirements: 10.1, 10.6_

- [ ] 8.3 Create Celery Beat tasks for scheduled cleanup
  - Create cleanup_completed_checkpoints task (run hourly)
  - Create cleanup_failed_checkpoints task (run daily at 2 AM)
  - Create cleanup_old_checkpoints task (run daily at 3 AM)
  - Create cleanup_ancient_checkpoints task (run weekly on Sunday at 4 AM)
  - _Requirements: 10.5_

- [ ]* 8.4 Write unit tests for cleanup and archival
  - Test cleanup logic with various checkpoint ages
  - Test archival to Azure Blob with mocked client
  - Test retrieval from cold storage
  - _Requirements: 10.7_

- [ ] 9. Implement checkpoint REST API endpoints
- [ ] 9.1 Create checkpoint API endpoints
  - Implement GET /api/v1/jobs/{job_id}/checkpoint for job-level checkpoint
  - Implement GET /api/v1/jobs/{job_id}/checkpoints/chunks for chunk checkpoints
  - Implement GET /api/v1/jobs/{job_id}/checkpoints/keywords for keyword progress
  - Implement POST /api/v1/jobs/{job_id}/resume for job resumption
  - Implement DELETE /api/v1/jobs/{job_id}/checkpoint for checkpoint deletion (admin only)
  - Implement GET /api/v1/checkpoints/stats for system-wide statistics (admin only)
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [ ] 9.2 Create response models for API
  - Implement JobCheckpointResponse, ChunkCheckpointResponse, KeywordProgressResponse
  - Implement ResumeResponse, CheckpointStatsResponse
  - Add proper error handling with HTTP status codes
  - _Requirements: 9.7_

- [ ] 9.3 Add authentication and authorization
  - Verify user owns job before returning checkpoint data
  - Restrict admin endpoints to admin users only
  - Add rate limiting to prevent abuse
  - _Requirements: 9.1, 9.5, 9.6_

- [ ]* 9.4 Write integration tests for API endpoints
  - Test all endpoints with valid and invalid requests
  - Test authentication and authorization
  - Test error handling
  - _Requirements: 9.7_

- [ ] 10. Integrate with existing systems
- [ ] 10.1 Create progress tracking adapter
  - Implement ProgressCheckpointAdapter to bridge checkpoint system with legacy progress tracking
  - Add fallback to legacy system if checkpoint not found
  - Convert checkpoint format to legacy progress format
  - _Requirements: 3.1, 3.2_

- [ ] 10.2 Update database models
  - Add checkpoint_enabled, last_checkpoint_id, checkpoint_created_at, checkpoint_updated_at to crawl_jobs table
  - Create migration script for schema changes
  - Add checkpoint property to CrawlJob model for lazy loading
  - _Requirements: 3.1_

- [ ] 10.3 Add frontend API client methods
  - Implement checkpointApi methods in frontend/lib/api/index.ts
  - Create useCheckpointProgress React hook for real-time progress
  - Add TypeScript types for checkpoint responses
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [ ] 10.4 Integrate with notification system
  - Implement CheckpointNotificationService for checkpoint events
  - Send notifications for job resumed, checkpoint failed
  - _Requirements: 7.4, 8.1_

- [ ] 11. Add error handling and recovery
- [ ] 11.1 Implement Redis failure handling
  - Add automatic fallback to PostgreSQL when Redis unavailable
  - Implement retry logic with exponential backoff
  - Add alerting for persistent Redis failures
  - _Requirements: 2.3_

- [ ] 11.2 Implement PostgreSQL failure handling
  - Queue writes to Redis with extended TTL when PostgreSQL unavailable
  - Implement background job to flush queue when database recovers
  - Add alerting for persistent PostgreSQL failures
  - _Requirements: 2.4_

- [ ] 11.3 Add checkpoint corruption detection and recovery
  - Validate checkpoint data on read using Pydantic models
  - Attempt repair by filling missing fields with defaults
  - Fall back to previous checkpoint if repair fails
  - Log corruption details for investigation
  - _Requirements: 1.5, 7.5_

- [ ]* 11.4 Write failure scenario tests
  - Test Redis failure and fallback
  - Test PostgreSQL failure and queuing
  - Test checkpoint corruption and recovery
  - Test worker crash and reconciliation
  - _Requirements: 2.3, 2.4, 7.5_

- [ ] 12. Deploy and monitor
- [ ] 12.1 Deploy to staging environment
  - Deploy database schema changes
  - Deploy checkpoint service code
  - Configure Redis and PostgreSQL connections
  - Set up Azure Blob Storage for archival
  - _Requirements: 2.1, 2.2_

- [ ] 12.2 Run integration and performance tests
  - Execute end-to-end tests with real services
  - Run load tests with 1000+ concurrent jobs
  - Verify performance targets (write <100ms, read <50ms)
  - Test cleanup and archival processes
  - _Requirements: 1.6, 8.5_

- [ ] 12.3 Set up monitoring and alerting
  - Configure Prometheus metrics collection
  - Create Grafana dashboards for checkpoint metrics
  - Set up Azure Monitor alerts for failures
  - Configure log aggregation for checkpoint operations
  - _Requirements: 8.1, 8.2, 8.3, 8.6, 8.7_

- [ ] 12.4 Phased rollout to production
  - Enable checkpoints for 10% of jobs (week 1)
  - Monitor error rates and performance
  - Increase to 50% of jobs (week 2)
  - Enable for 100% of jobs (week 3)
  - Deprecate legacy progress tracking (week 4)
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [ ] 12.5 Validate success criteria
  - Verify >95% resumption success rate
  - Verify checkpoint operations meet latency targets
  - Verify <0.1% corruption rate
  - Verify checkpoint storage <5% of total storage
  - Gather user feedback on resume functionality
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_
