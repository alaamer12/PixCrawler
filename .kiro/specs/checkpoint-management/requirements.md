# Requirements Document: Checkpoint Management System

## Introduction

The PixCrawler platform currently has a stale checkpoint/progress tracking system in `builder/progress.py` that doesn't align with the modern Celery-based chunk orchestration architecture. This feature will implement a comprehensive checkpoint management system that enables resumability for crawl jobs, integrates seamlessly with Celery tasks and job chunks, and provides robust failure recovery.

The checkpoint system will use a **batch-based approach** to track progress at multiple levels (job, chunk, engine/keyword batch, and download batch) with comprehensive metadata including keywords used, search engine configurations, offset ranges, variations attempted, and detailed statistics. This enables jobs to resume from the last successful checkpoint after interruptions, failures, or system restarts with full context of what was attempted.

**Batch-Based Checkpoint Hierarchy:**
1. **Job Checkpoint**: Overall job metadata (keywords, max_images, project_id)
2. **Chunk Batch Checkpoint**: Per-chunk processing (task_id, engines_queue, target_images, worker_metadata)
3. **Engine Batch Checkpoint**: Per-engine/keyword processing (variations_queue, offset_ranges, images_per_variation)
4. **Download Batch Checkpoint**: Per-batch downloads (urls_discovered, download_attempts, validation_results)

**Key Integration Points:**
- **Celery Tasks**: `builder/tasks.py` (task_download_google, task_download_bing, task_download_baidu, task_download_duckduckgo)
- **Chunk Orchestration**: Database fields (total_chunks, active_chunks, completed_chunks, failed_chunks, task_ids)
- **Download Flow**: `builder/_downloader.py` (ImageDownloader with sequential engine processing), `builder/_generator.py` (Retry class with AlternativeKeyTermGenerator)
- **Search Engines**: `builder/_search_engines.py` (download_google_images, download_bing_images, etc. with offset_range and variation_step configs)
- **Engine Config**: `builder/_config.py` (get_engines() returns offset_range and variation_step per engine)
- **Progress Tracking**: `builder/progress.py` (ProgressCache, DatasetTracker, ProgressManager - to be modernized with batch support)

## Requirements

### Requirement 1: Batch-Based Checkpoint Data Model

**User Story:** As a system administrator, I want checkpoint data to be stored in batch format with comprehensive metadata, so that I can track and resume jobs with full context of what was attempted.

#### Acceptance Criteria

1. WHEN a crawl job is created THEN the system SHALL initialize a job checkpoint with job_id, project_id, keywords (JSONB), max_images, and creation_timestamp
2. WHEN a chunk starts processing THEN the system SHALL create a chunk checkpoint batch with task_id, chunk_index, keyword, engines_to_try (list), target_images, and start_timestamp
3. WHEN an engine processes a keyword THEN the system SHALL record engine checkpoint with engine_name, keyword, variations_attempted (list), offset_ranges (dict), images_discovered, images_downloaded, and processing_metadata
4. WHEN a batch of downloads completes THEN the system SHALL record batch checkpoint with urls_attempted (list), successful_downloads (list), failed_downloads (list), duplicate_count, and batch_statistics
5. IF checkpoint data becomes corrupted THEN the system SHALL detect inconsistencies, log errors with full context, and attempt recovery from last valid checkpoint
6. WHEN checkpoint data is queried THEN the system SHALL return data within 100ms for job-level queries and 500ms for detailed batch queries with full metadata

### Requirement 2: Checkpoint Persistence Layer

**User Story:** As a developer, I want checkpoints to be persisted to both Redis (for fast access) and PostgreSQL (for durability), so that the system can recover from any type of failure.

#### Acceptance Criteria

1. WHEN a checkpoint is created or updated THEN the system SHALL write to Redis cache with 24-hour TTL
2. WHEN a checkpoint is created or updated THEN the system SHALL write to PostgreSQL within 5 seconds
3. WHEN Redis is unavailable THEN the system SHALL fall back to PostgreSQL without data loss
4. WHEN PostgreSQL is unavailable THEN the system SHALL queue writes to Redis and retry with exponential backoff
5. WHEN a checkpoint is read THEN the system SHALL attempt Redis first and fall back to PostgreSQL if cache miss
6. WHEN a job completes successfully THEN the system SHALL archive checkpoint data and clear Redis cache
7. WHEN checkpoint data exceeds 1MB THEN the system SHALL compress data before storage

### Requirement 3: Job-Level Checkpoint Management

**User Story:** As a user, I want my crawl jobs to automatically resume from the last checkpoint after interruptions, so that I don't lose progress or waste credits.

#### Acceptance Criteria

1. WHEN a job is interrupted THEN the system SHALL save the current state including completed chunks, active chunks, and failed chunks
2. WHEN a job is resumed THEN the system SHALL load the last checkpoint and skip completed chunks
3. WHEN a job is resumed THEN the system SHALL retry failed chunks up to max_retries limit
4. WHEN a job is resumed THEN the system SHALL preserve task_ids for active chunks and query Celery for their status
5. IF active chunks are found to be completed in Celery THEN the system SHALL update the database accordingly
6. WHEN a job is resumed after system restart THEN the system SHALL reconcile database state with Celery state
7. WHEN a job has no valid checkpoint THEN the system SHALL start from the beginning and log a warning

### Requirement 4: Chunk-Level Batch Checkpoint Management

**User Story:** As a system operator, I want chunk-level batch checkpoints to track individual Celery task progress with full metadata, so that I can monitor, debug, and resume distributed processing.

#### Acceptance Criteria

1. WHEN a chunk task starts THEN the system SHALL create a batch checkpoint with task_id, chunk_index, keyword, engines_queue (list of engines to try), target_images, chunk_metadata (worker_id, queue_name, priority), and start_time
2. WHEN a chunk task progresses THEN the system SHALL update checkpoint batch with current_engine, variations_tried (list), images_discovered_per_engine (dict), images_downloaded_per_engine (dict), current_offset_ranges (dict), and progress_percentage
3. WHEN a chunk task completes THEN the system SHALL finalize checkpoint batch with end_time, total_images, success_rate, engines_used (list), total_variations_attempted, final_offset_ranges (dict), and completion_metadata
4. WHEN a chunk task fails THEN the system SHALL record error_type, error_message, traceback, failed_engine, failed_variation, last_successful_offset, retry_count, and failure_metadata in checkpoint batch
5. WHEN a chunk task is retried THEN the system SHALL create a new checkpoint batch linked to original with retry_count incremented, previous_checkpoint_id, and resume_from_metadata (engine, variation, offset)
6. WHEN chunk checkpoint is queried THEN the system SHALL return real-time status by checking both database and Celery, including full batch metadata and progress breakdown by engine
7. IF chunk task is stuck (no update for 30 minutes) THEN the system SHALL mark checkpoint batch as stale, record stale_detection_time and last_known_state, and trigger reconciliation with Celery

### Requirement 5: Engine/Keyword Batch Checkpoint Management

**User Story:** As a developer, I want engine/keyword batch checkpoints to track which search engines, variations, and offsets have been attempted for each keyword, so that the system can avoid duplicate work and optimize retry strategies.

#### Acceptance Criteria

1. WHEN a keyword is processed by an engine THEN the system SHALL create an engine batch checkpoint with keyword, engine_name (google/bing/baidu/duckduckgo), engine_config (offset_range, variation_step), variations_queue (list of templates to try), and start_metadata
2. WHEN a search variation is attempted THEN the system SHALL record variation_template, formatted_query, retry_count, offset_start, offset_end, images_discovered, images_downloaded, processing_time, and attempt_metadata
3. WHEN a variation succeeds THEN the system SHALL mark it as completed with final_offset, images_downloaded_count, success_rate, duplicate_count, and completion_metadata
4. WHEN a variation fails THEN the system SHALL record error_type, error_message, failed_offset, retry_strategy (from AlternativeKeyTermGenerator), next_variation_to_try, and failure_metadata
5. WHEN an engine has exhausted all variations for a keyword THEN the system SHALL mark engine batch checkpoint as completed with total_variations_attempted, total_images_downloaded, total_offsets_processed, and final_statistics
6. WHEN a keyword is resumed THEN the system SHALL load engine batch checkpoint, skip completed engine/variation/offset combinations, and resume from last successful offset with next variation
7. WHEN engine batch checkpoint shows no progress after max_retries attempts THEN the system SHALL mark engine as failed with failure_reason, attempted_variations (list), attempted_offsets (dict), and trigger fallback to next engine or DuckDuckGo

### Requirement 6: Download Batch Checkpoint Management

**User Story:** As a quality assurance engineer, I want download batch checkpoints to track batches of download attempts with comprehensive metadata, so that I can identify patterns in failures and optimize retry strategies.

#### Acceptance Criteria

1. WHEN a batch of image URLs is discovered THEN the system SHALL create a download batch checkpoint with urls_discovered (list), engine, keyword, variation, offset_range, discovery_metadata (search_rank, thumbnail_url, source_page), and discovery_time
2. WHEN a download batch is processed THEN the system SHALL update checkpoint with urls_attempted (list), urls_in_progress (list), urls_completed (list), urls_failed (list), attempt_count_per_url (dict), and batch_progress_percentage
3. WHEN downloads in batch succeed THEN the system SHALL record successful_downloads (list with filename, file_size, download_duration, final_path), total_bytes_downloaded, average_download_speed, and success_metadata
4. WHEN downloads in batch fail THEN the system SHALL record failed_downloads (list with url, error_type, error_message, attempt_count), retry_queue (list of urls to retry), failure_patterns (dict), and failure_metadata
5. WHEN duplicate detection runs on batch THEN the system SHALL update checkpoint with duplicates_found (list with original_url, duplicate_of_filename, hash_value), duplicate_count, and deduplication_metadata
6. WHEN validation runs on batch (via validator package) THEN the system SHALL update checkpoint with validation_results (list with filename, is_valid, validation_errors, dimensions, format), invalid_count, and validation_metadata
7. WHEN download batch checkpoint is queried THEN the system SHALL return current batch status, per-URL attempt history, aggregate statistics (success_rate, failure_rate, duplicate_rate), and full metadata

### Requirement 7: Checkpoint Recovery and Resumption

**User Story:** As a user, I want the system to automatically detect interrupted jobs and offer to resume them, so that I can continue where I left off without manual intervention.

#### Acceptance Criteria

1. WHEN the system starts THEN it SHALL scan for jobs with status "running" and check if they have active checkpoints
2. WHEN an interrupted job is detected THEN the system SHALL query Celery for task status and reconcile with database
3. WHEN a job can be resumed THEN the system SHALL calculate remaining work and estimate completion time
4. WHEN a job is resumed THEN the system SHALL send notification to user with resume details
5. WHEN a job cannot be resumed (checkpoint corrupted) THEN the system SHALL mark job as failed and notify user
6. WHEN multiple jobs are interrupted THEN the system SHALL prioritize resumption based on user credits and job age
7. WHEN a resumed job completes THEN the system SHALL merge checkpoint data with final results

### Requirement 8: Checkpoint Monitoring and Diagnostics

**User Story:** As a system administrator, I want comprehensive monitoring and diagnostics for checkpoints, so that I can identify and resolve issues proactively.

#### Acceptance Criteria

1. WHEN checkpoint operations occur THEN the system SHALL log events with structured logging including job_id, chunk_id, and operation type
2. WHEN checkpoint write fails THEN the system SHALL increment failure counter and trigger alert if threshold exceeded
3. WHEN checkpoint read is slow (>500ms) THEN the system SHALL log performance warning with timing details
4. WHEN checkpoint data is inconsistent THEN the system SHALL log validation errors and attempt auto-repair
5. WHEN checkpoint storage exceeds 80% capacity THEN the system SHALL trigger cleanup of old checkpoints
6. WHEN checkpoint metrics are queried THEN the system SHALL return statistics including total checkpoints, active checkpoints, and storage usage
7. WHEN checkpoint health check runs THEN the system SHALL verify Redis and PostgreSQL connectivity and data consistency

### Requirement 9: Checkpoint API Integration

**User Story:** As a frontend developer, I want REST API endpoints to query checkpoint status, so that I can display real-time progress to users.

#### Acceptance Criteria

1. WHEN GET /api/v1/jobs/{job_id}/checkpoint is called THEN the system SHALL return job-level checkpoint with chunk progress
2. WHEN GET /api/v1/jobs/{job_id}/checkpoints/chunks is called THEN the system SHALL return all chunk checkpoints with status
3. WHEN GET /api/v1/jobs/{job_id}/checkpoints/keywords is called THEN the system SHALL return keyword-level progress
4. WHEN POST /api/v1/jobs/{job_id}/resume is called THEN the system SHALL validate checkpoint and resume job
5. WHEN DELETE /api/v1/jobs/{job_id}/checkpoint is called THEN the system SHALL clear checkpoint data (admin only)
6. WHEN GET /api/v1/checkpoints/stats is called THEN the system SHALL return system-wide checkpoint statistics
7. IF API request fails THEN the system SHALL return appropriate HTTP status code and error message

### Requirement 10: Checkpoint Cleanup and Archival

**User Story:** As a system administrator, I want automatic cleanup of old checkpoints, so that storage costs remain manageable and performance stays optimal.

#### Acceptance Criteria

1. WHEN a job completes successfully THEN the system SHALL archive checkpoint data to cold storage within 1 hour
2. WHEN a job fails permanently THEN the system SHALL retain checkpoint data for 7 days before archival
3. WHEN checkpoint data is older than 30 days THEN the system SHALL compress and move to Azure Blob cold tier
4. WHEN checkpoint data is older than 90 days THEN the system SHALL delete from hot storage (keep archive only)
5. WHEN cleanup runs THEN the system SHALL process checkpoints in batches of 100 to avoid performance impact
6. WHEN archived checkpoint is requested THEN the system SHALL retrieve from cold storage with 5-minute SLA
7. WHEN cleanup fails THEN the system SHALL retry with exponential backoff and alert if persistent failure

## Success Metrics

- **Resumption Success Rate**: >95% of interrupted jobs successfully resume from checkpoint
- **Checkpoint Write Latency**: <100ms for Redis, <5s for PostgreSQL
- **Checkpoint Read Latency**: <50ms for Redis cache hit, <500ms for PostgreSQL fallback
- **Storage Efficiency**: Checkpoint data <5% of total image data size
- **Recovery Time**: Jobs resume within 30 seconds of system restart
- **Data Consistency**: <0.1% checkpoint data corruption rate
- **API Response Time**: <200ms for checkpoint status queries

## Non-Functional Requirements

- **Scalability**: Support 10,000+ concurrent jobs with checkpoints
- **Reliability**: 99.9% checkpoint write success rate
- **Performance**: Checkpoint operations should not impact task processing throughput
- **Security**: Checkpoint data must be encrypted at rest and in transit
- **Compliance**: Checkpoint data retention must comply with GDPR (user data deletion)
- **Monitoring**: All checkpoint operations must be observable via Azure Monitor
- **Documentation**: Comprehensive API documentation and troubleshooting guides
