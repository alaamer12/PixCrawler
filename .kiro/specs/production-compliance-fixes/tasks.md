# Implementation Plan

- [x] 1. Implement error classification and retry infrastructure




- [x] 1.1 Set up error classification foundation


  - Extend `builder/_exceptions.py` with PermanentError and TransientError base classes
  - Add specific exception types: ValidationError, NotFoundError, AuthenticationError, BadRequestError, RateLimitError, ServiceUnavailableError, TimeoutException, NetworkError
  - Implement `classify_http_error(status_code: int)` function with HTTP_ERROR_MAP
  - Implement `classify_network_error(error: Exception)` function
  - Add comprehensive docstrings explaining retry behavior for each exception type
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 1.2 Add Tenacity dependency and implement network retry


  - Add `tenacity>=8.2.0` to `builder/pyproject.toml` dependencies
  - Update `builder/_downloader.py` to import Tenacity decorators
  - Add `@retry` decorator to image download operations with stop_after_attempt(3)
  - Configure wait_exponential(multiplier=1, min=2, max=10) for backoff strategy
  - Configure retry_if_exception_type for transient errors only
  - Add before_sleep callback for logging retry attempts
  - Implement rate limit handling with Retry-After header support
  - Integrate error classification to raise appropriate exception types
  - Add docstrings documenting retry strategy and timing
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_



- [ ] 1.3 Fix Celery task retry logic in builder/tasks.py and validator/tasks.py
  - Remove `autoretry_for` parameter from all 12 task decorators (8 in builder, 4 in validator)
  - Add `bind=True` and `acks_late=True` to all task decorators
  - Implement try-except blocks with explicit `self.retry()` for infrastructure failures
  - Configure max_retries=3 and countdown=60 for infrastructure retries
  - Add error handling for PermanentError (fail immediately without retry)
  - Add structured logging for all retry attempts with error context
  - Update task docstrings to document retry strategy
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

- [ ]* 1.4 Write unit tests for retry behavior
  - Test error classification: HTTP status code mapping and exception hierarchy
  - Test Tenacity retry on transient errors and no retry on permanent errors
  - Test Celery tasks do NOT use autoretry_for parameter
  - Test explicit retry for infrastructure failures only
  - Test retry count limits (max 3) and timing (60s for Celery, exponential for Tenacity)
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 2. Migrate to centralized logging system







- [x] 2.1 Migrate all files to centralized logging


  - Migrate `backend/storage/datalake_blob_provider.py`
  - Migrate `builder/_generator.py`
  - Migrate `builder/_downloader.py`
  - Migrate `builder/tasks.py` with correct import path
  - Replace `import logging` with `from utility.logging_config import get_logger`
  - Replace `logger = logging.getLogger(__name__)` with `logger = get_logger(__name__)`
  - Verify all existing log calls work without modification
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

- [ ] 3. Add structured logging to critical operations

- [ ] 3.1 Add structured logging context to job creation
  - Add `logger.contextualize()` or `logger.bind()` to job creation in builder/tasks.py
  - Include context: user_id, job_id, keywords, max_images
  - Update all log calls within job creation to include structured context
  - _Requirements: 5.1, 5.2, 5.4_

- [ ] 3.2 Add structured logging context to image download
  - Add `logger.bind()` to download operations in builder/_downloader.py
  - Include context: job_id, chunk_id, url, attempt_number
  - Add structured context to retry attempt logs
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 3.3 Add structured logging context to validation, compression, and export
  - Add `logger.bind()` to validation operations in validator/tasks.py (context: job_id, image_id, validation_level)
  - Add `logger.bind()` to compression operations in utility/compress/ (context: job_id, format, compression_level, file_count)
  - Add `logger.bind()` to export operations in backend/api/v1/endpoints/exports.py (context: user_id, job_id, export_format, storage_tier)
  - Update all log calls within these operations to include structured context
  - _Requirements: 5.1, 5.2, 5.4_

- [ ]* 3.4 Write integration tests for logging and retry layers
  - Test all retry attempts are logged with structured context
  - Test log levels are appropriate (info, warning, error)
  - Test network failure triggers only Tenacity retry (not Celery)
  - Test infrastructure failure triggers only Celery retry (not Tenacity)
  - Test total attempts = 3 (not 9) for any single failure
  - _Requirements: 6.6, 6.7_

- [ ] 4. Update documentation
- [ ] 4.1 Update RETRY_ARCHITECTURE.md
  - Add implementation patterns section with actual code examples from this implementation
  - Document all exception types and their retry behavior in error classification section
  - Add test examples and coverage requirements to testing strategy section
  - Add troubleshooting section with common issues and solutions
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 4.2 Update LOGGING_GUIDE.md
  - Add structured logging examples showing logger.bind() and logger.contextualize()
  - Document which critical operations require structured logging
  - Add log filtering examples for production environments
  - _Requirements: 7.5_
