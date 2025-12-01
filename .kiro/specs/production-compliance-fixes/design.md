# Design Document: Production Compliance Fixes

## Overview

This design document outlines the technical approach for resolving all architectural compliance issues identified in the production readiness compliance reports. The implementation addresses 7 key requirements spanning retry logic, error classification, logging migration, structured logging, testing, and documentation.

The implementation will bring retry logic compliance from 40% to 100% and logging compliance from 85% to 100%.

## Architecture

### High-Level Architecture

```
Celery Task Layer (Infrastructure Failures)
    ↓
Business Logic Layer (Error Classification)
    ↓
Operation Layer - Tenacity (Network Failures)
    ↓
Centralized Logging (Loguru)
```

### Retry Strategy

**Single Retry Layer Principle:**
- Celery: Infrastructure failures (MemoryError, DatabaseConnectionError)
- Tenacity: Network failures (TimeoutError, NetworkError, 429/503/504)
- No Retry: Permanent errors (ValidationError, 404, 401, 403, 400)

**Maximum Retry Attempts:**
- Celery: 3 retries with 60s countdown
- Tenacity: 3 retries with exponential backoff (2s, 4s, 8s)
- Total worst case: 3 attempts (not 3×3=9)

**Design Rationale:**
This architecture prevents exponential retry explosions by ensuring each failure type is handled by exactly one retry mechanism. The separation of concerns allows infrastructure failures to be handled at the task level while network operations handle their own transient failures, maintaining predictable system behavior.

## Components and Interfaces

### 1. Error Classification Module

**Location:** `builder/_exceptions.py` (extend existing)

**Purpose:** Provide a clear taxonomy of errors to guide retry decisions across the application.

**Classes:**
```python
class PermanentError(Exception):
    """Errors that should not be retried."""
    pass

class TransientError(Exception):
    """Errors that may succeed on retry."""
    pass

class ValidationError(PermanentError):
    """Validation failures - no retry."""
    pass

class NotFoundError(PermanentError):
    """Resource not found (404) - no retry."""
    pass

class AuthenticationError(PermanentError):
    """Authentication failures (401, 403) - no retry."""
    pass

class BadRequestError(PermanentError):
    """Bad request (400) - no retry."""
    pass

class RateLimitError(TransientError):
    """Rate limit (429) - retry with backoff."""
    pass

class ServiceUnavailableError(TransientError):
    """Service unavailable (503, 504) - retry."""
    pass

class TimeoutException(TransientError):
    """Network timeout - retry."""
    pass

class NetworkError(TransientError):
    """Network connectivity issues - retry."""
    pass
```

**Interface:**
- `classify_http_error(status_code: int) -> Type[Exception]`: Classify HTTP errors
- `classify_network_error(error: Exception) -> Type[Exception]`: Classify network errors

**Design Rationale:**
By creating explicit exception types for permanent vs transient errors, we enable type-based retry logic that is self-documenting and prevents accidental retries of operations that will never succeed.



### 2. Celery Task Retry Implementation

**Affected Files:**
- `builder/tasks.py` (8 tasks)
- `validator/tasks.py` (4 tasks)

**Pattern:**
```python
from celery import Task
from utility.logging_config import get_logger

logger = get_logger(__name__)

@celery_app.task(bind=True, acks_late=True)
def process_chunk_task(self, chunk_id: str) -> dict:
    """
    Process a chunk of images with explicit retry handling.
    
    Retry Strategy:
        - Infrastructure failures: Retry up to 3 times with 60s delay
        - Network failures: Delegated to operation layer (Tenacity)
        - Permanent errors: Fail immediately
    """
    try:
        processor = ChunkProcessor()
        result = processor.process_chunk(chunk_id)
        logger.info(f"Chunk {chunk_id} processed successfully", chunk_id=chunk_id)
        return result
        
    except (MemoryError, DatabaseConnectionError) as e:
        logger.error(
            f"Infrastructure failure for chunk {chunk_id}: {e}",
            chunk_id=chunk_id,
            error_type=type(e).__name__,
            retry_count=self.request.retries
        )
        raise self.retry(exc=e, max_retries=3, countdown=60)
        
    except PermanentError as e:
        logger.error(
            f"Permanent error for chunk {chunk_id}: {e}",
            chunk_id=chunk_id,
            error_type=type(e).__name__
        )
        raise
        
    except Exception as e:
        logger.exception(
            f"Unexpected error for chunk {chunk_id}: {e}",
            chunk_id=chunk_id,
            error_type=type(e).__name__
        )
        raise
```

**Key Changes:**
- Remove `autoretry_for` parameter from all task decorators
- Add `bind=True` and `acks_late=True` to all tasks
- Implement explicit `self.retry()` calls for infrastructure failures only
- Add structured logging with context for all retry attempts

**Design Rationale:**
Explicit retry handling gives us fine-grained control over which errors trigger retries, preventing the exponential retry problem. The `acks_late=True` setting ensures tasks are re-queued if a worker crashes, improving reliability.

### 3. Tenacity Network Retry Implementation

**Affected Files:**
- `builder/_downloader.py`

**Dependencies:**
Add to `builder/pyproject.toml`:
```toml
dependencies = [
    # ... existing dependencies
    "tenacity>=8.2.0",
]
```

**Pattern:**
```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
from utility.logging_config import get_logger
import builder._exceptions as exceptions

logger = get_logger(__name__)

class ImageDownloader:
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((
            exceptions.TimeoutException,
            exceptions.NetworkError,
            exceptions.RateLimitError,
            exceptions.ServiceUnavailableError
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
    def download_image(self, url: str) -> bytes:
        """
        Download image with automatic retry for transient errors.
        
        Retry Strategy:
            - Attempt 1: Immediate
            - Attempt 2: Wait 2s
            - Attempt 3: Wait 4s
            - Max wait: 10s
        
        Raises:
            PermanentError: For non-retryable errors (404, 401, etc.)
            TransientError: After all retries exhausted
        """
        try:
            response = httpx.get(url, timeout=30)
            
            # Handle rate limiting with Retry-After header
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 5))
                logger.warning(f"Rate limited, waiting {retry_after}s", url=url)
                time.sleep(retry_after)
                raise exceptions.RateLimitError(f"Rate limited: {url}")
            
            # Classify HTTP errors
            if response.status_code >= 400:
                error_class = exceptions.classify_http_error(response.status_code)
                raise error_class(f"HTTP {response.status_code}: {url}")
            
            return response.content
            
        except httpx.TimeoutException as e:
            raise exceptions.TimeoutException(f"Timeout downloading {url}") from e
        except httpx.NetworkError as e:
            raise exceptions.NetworkError(f"Network error downloading {url}") from e
```

**Design Rationale:**
Tenacity provides declarative retry logic with exponential backoff, which is ideal for handling transient network failures. The `before_sleep` callback ensures all retry attempts are logged for observability. By using `reraise=True`, we ensure the final failure propagates correctly to the calling code.

### 4. Centralized Logging Migration

**Affected Files:**
- `backend/storage/datalake_blob_provider.py`
- `builder/_generator.py`
- `builder/_downloader.py`
- `builder/tasks.py`

**Migration Pattern:**

**Before:**
```python
import logging

logger = logging.getLogger(__name__)
```

**After:**
```python
from utility.logging_config import get_logger

logger = get_logger(__name__)
```

**No Other Changes Required:**
The `get_logger()` function returns a Loguru logger that is API-compatible with Python's standard logging module, so existing log calls (`logger.info()`, `logger.error()`, etc.) work without modification.

**Design Rationale:**
Centralized logging through the utility package ensures consistent log formatting, structured logging support, and centralized configuration. This makes it easier to integrate with monitoring systems like Azure Monitor and provides better debugging capabilities in production.

### 5. Structured Logging Context

**Implementation Pattern:**

```python
from utility.logging_config import get_logger

logger = get_logger(__name__)

# Add context to all logs in a scope
with logger.contextualize(
    user_id=user_id,
    job_id=job_id,
    operation="image_download"
):
    logger.info("Starting image download")
    # All logs within this block include the context
    download_images(urls)
    logger.info("Download complete")

# Or bind context for specific log calls
logger.bind(
    chunk_id=chunk_id,
    retry_count=retry_count,
    error_type="NetworkError"
).warning("Retrying chunk processing")
```

**Critical Operations to Instrument:**
1. **Job Creation** (`builder/tasks.py:create_crawl_job_task`)
   - Context: `user_id`, `job_id`, `keywords`, `max_images`
   
2. **Image Download** (`builder/_downloader.py`)
   - Context: `job_id`, `chunk_id`, `url`, `attempt_number`
   
3. **Validation** (`validator/tasks.py`)
   - Context: `job_id`, `image_id`, `validation_level`
   
4. **Compression** (`utility/compress/`)
   - Context: `job_id`, `format`, `compression_level`, `file_count`
   
5. **Export** (`backend/api/v1/endpoints/exports.py`)
   - Context: `user_id`, `job_id`, `export_format`, `storage_tier`

**Design Rationale:**
Structured logging with context makes it trivial to filter and analyze logs in production. For example, you can easily find all logs related to a specific job or user, or track the complete lifecycle of a request through the system.

## Data Models

### Error Classification Mapping

```python
# HTTP Status Code → Exception Type
HTTP_ERROR_MAP = {
    400: BadRequestError,
    401: AuthenticationError,
    403: AuthenticationError,
    404: NotFoundError,
    429: RateLimitError,
    503: ServiceUnavailableError,
    504: ServiceUnavailableError,
}

def classify_http_error(status_code: int) -> Type[Exception]:
    """
    Classify HTTP status codes into permanent or transient errors.
    
    Args:
        status_code: HTTP status code
        
    Returns:
        Exception class (PermanentError or TransientError subclass)
    """
    return HTTP_ERROR_MAP.get(status_code, PermanentError)
```

## Error Handling

### Error Flow Diagram

```
HTTP Request
    ↓
[Network Error?] → Yes → TimeoutException/NetworkError (Tenacity retries)
    ↓ No
[HTTP 4xx?] → Yes → PermanentError (No retry)
    ↓ No
[HTTP 429/503/504?] → Yes → TransientError (Tenacity retries)
    ↓ No
[Success]
```

### Retry Decision Matrix

| Error Type | Celery Retry | Tenacity Retry | Fail Fast |
|------------|--------------|----------------|-----------|
| MemoryError | ✅ (3x, 60s) | ❌ | ❌ |
| DatabaseConnectionError | ✅ (3x, 60s) | ❌ | ❌ |
| TimeoutException | ❌ | ✅ (3x, exp) | ❌ |
| NetworkError | ❌ | ✅ (3x, exp) | ❌ |
| RateLimitError (429) | ❌ | ✅ (3x, exp) | ❌ |
| ServiceUnavailableError (503/504) | ❌ | ✅ (3x, exp) | ❌ |
| ValidationError | ❌ | ❌ | ✅ |
| NotFoundError (404) | ❌ | ❌ | ✅ |
| AuthenticationError (401/403) | ❌ | ❌ | ✅ |
| BadRequestError (400) | ❌ | ❌ | ✅ |

## Testing Strategy

### Unit Tests

**Test Coverage:**
1. **Celery Task Retry Behavior** (`tests/test_task_retry.py`)
   - Verify tasks do NOT use autoretry
   - Verify explicit retry for infrastructure failures
   - Verify no retry for permanent errors
   - Verify retry count limits (max 3)
   - Verify countdown delays (60s)

2. **Tenacity Operation Retry** (`tests/test_network_retry.py`)
   - Verify retry on transient errors (timeout, network, 429, 503, 504)
   - Verify no retry on permanent errors (404, 401, 403, 400)
   - Verify exponential backoff timing
   - Verify max retry attempts (3)
   - Verify final exception propagation

3. **Error Classification** (`tests/test_error_classification.py`)
   - Verify HTTP status code mapping
   - Verify exception hierarchy (PermanentError vs TransientError)
   - Verify classify_http_error() function
   - Verify classify_network_error() function

**Example Test:**
```python
import pytest
from unittest.mock import Mock, patch
from builder.tasks import process_chunk_task
from builder._exceptions import ValidationError, NetworkError

def test_task_no_autoretry():
    """Verify task does not use autoretry_for parameter."""
    task_config = process_chunk_task.__dict__
    assert 'autoretry_for' not in task_config or task_config['autoretry_for'] == ()

def test_task_explicit_retry_infrastructure_failure(celery_app):
    """Verify task retries on infrastructure failures."""
    with patch('builder.tasks.ChunkProcessor') as mock_processor:
        mock_processor.return_value.process_chunk.side_effect = MemoryError("OOM")
        
        task = process_chunk_task.apply(args=["chunk_123"])
        
        # Should retry up to 3 times
        assert task.retries <= 3
        assert task.countdown == 60

def test_task_no_retry_permanent_error(celery_app):
    """Verify task does not retry permanent errors."""
    with patch('builder.tasks.ChunkProcessor') as mock_processor:
        mock_processor.return_value.process_chunk.side_effect = ValidationError("Invalid")
        
        with pytest.raises(ValidationError):
            process_chunk_task.apply(args=["chunk_123"])
        
        # Should fail immediately without retry
        assert process_chunk_task.request.retries == 0
```

### Integration Tests

**Test Scenarios:**
1. **Single Retry Layer Verification** (`tests/integration/test_retry_layers.py`)
   - Simulate network failure in download operation
   - Verify only Tenacity retries (not Celery)
   - Verify total attempts = 3 (not 9)

2. **Logging Verification** (`tests/integration/test_logging.py`)
   - Verify all retry attempts are logged
   - Verify structured context is included
   - Verify log levels are appropriate

3. **End-to-End Job Processing** (`tests/integration/test_job_processing.py`)
   - Create job with transient failures
   - Verify job completes successfully after retries
   - Verify logs show retry attempts

## Documentation

### Documentation Structure

**Location:** `docs/RETRY_ARCHITECTURE.md` (already exists, will be updated)

**Sections to Update:**
1. **Implementation Patterns** - Add actual code examples from this implementation
2. **Error Classification** - Document all exception types and their retry behavior
3. **Testing Strategy** - Add test examples and coverage requirements
4. **Troubleshooting** - Add common issues and solutions

**Additional Documentation:**

**Location:** `docs/LOGGING_GUIDE.md` (already exists, will be updated)

**Sections to Add:**
1. **Structured Logging Examples** - Show how to use `logger.bind()` and `logger.contextualize()`
2. **Critical Operations** - Document which operations require structured logging
3. **Log Filtering** - Show how to filter logs by context in production

**Code Documentation:**

All modified files will include:
- Docstrings explaining retry strategy
- Inline comments for error classification logic
- Examples in docstrings showing expected behavior

**Example:**
```python
def download_image(self, url: str) -> bytes:
    """
    Download image with automatic retry for transient errors.
    
    This method uses Tenacity for operation-level retries. It will retry
    up to 3 times with exponential backoff for transient errors like
    network timeouts and rate limiting.
    
    Retry Strategy:
        - Attempt 1: Immediate
        - Attempt 2: Wait 2s
        - Attempt 3: Wait 4s
        - Max wait: 10s
    
    Args:
        url: Image URL to download
        
    Returns:
        Image content as bytes
        
    Raises:
        PermanentError: For non-retryable errors (404, 401, etc.)
        TransientError: After all retries exhausted
        
    Example:
        >>> downloader = ImageDownloader()
        >>> content = downloader.download_image("https://example.com/image.jpg")
    """
```

## Implementation Phases

### Phase 1: Foundation (Week 1)
1. Add Tenacity dependency to builder package
2. Extend `builder/_exceptions.py` with error classification
3. Implement error classification functions
4. Write unit tests for error classification

### Phase 2: Retry Logic (Week 1-2)
1. Update all 12 Celery tasks to remove autoretry
2. Implement explicit retry logic in tasks
3. Add Tenacity decorators to network operations in `_downloader.py`
4. Write unit tests for retry behavior

### Phase 3: Logging Migration (Week 2)
1. Migrate 4 files to centralized logging
2. Add structured logging context to 5 critical operations
3. Update log calls to include context
4. Write integration tests for logging

### Phase 4: Testing & Documentation (Week 2-3)
1. Write comprehensive unit tests (target: 90% coverage)
2. Write integration tests for retry layers
3. Update `docs/RETRY_ARCHITECTURE.md`
4. Update `docs/LOGGING_GUIDE.md`
5. Add code documentation to all modified files

### Phase 5: Validation (Week 3)
1. Run full test suite
2. Manual testing of retry scenarios
3. Review logs for structured context
4. Performance testing under load
5. Final compliance audit

## Success Metrics

1. **Retry Logic Compliance:** 100% (up from 40%)
   - All 12 tasks use explicit retry (not autoretry)
   - All network operations use Tenacity
   - No exponential retry explosions

2. **Logging Compliance:** 100% (up from 85%)
   - All 4 files use centralized logging
   - 5+ critical operations use structured logging
   - All retry attempts are logged

3. **Test Coverage:** 90%+ for modified code
   - Unit tests for all retry scenarios
   - Integration tests for retry layers
   - Error classification tests

4. **Performance:** No degradation
   - Retry overhead < 5% of total processing time
   - Logging overhead < 1% of total processing time

5. **Observability:** Improved debugging capability
   - Can trace any job through logs using job_id
   - Can identify retry patterns in production
   - Can measure retry success rates
