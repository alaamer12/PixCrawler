# Retry Architecture & Strategy Guide

**Document Version:** 1.0  
**Last Updated:** 2025-10-30  
**Status:** Architecture Decision Record (ADR)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [The Problem](#the-problem)
3. [Architecture Principles](#architecture-principles)
4. [Retry Layers](#retry-layers)
5. [When to Use What](#when-to-use-what)
6. [Implementation Patterns](#implementation-patterns)
7. [Anti-Patterns](#anti-patterns)
8. [Error Classification](#error-classification)
9. [Configuration Guidelines](#configuration-guidelines)
10. [Testing Strategy](#testing-strategy)

---

## Overview

### Purpose

This document defines the retry strategy architecture for PixCrawler's distributed task processing system. It establishes clear guidelines for when and how to use different retry mechanisms to avoid exponential retry explosions while maintaining system reliability.

### Scope

- Celery task-level retries
- Tenacity operation-level retries
- Error classification and handling
- Retry configuration standards

### Goals

- **Prevent exponential retries** (e.g., 3 × 3 × 3 = 27 attempts)
- **Single retry layer per failure type**
- **Clear separation of concerns**
- **Predictable failure behavior**
- **Observable retry patterns**

---

## The Problem

### Exponential Retry Hell

```python
# ❌ WRONG: Multiple retry layers
@celery_app.task(autoretry_for=(Exception,), max_retries=3)  # Layer 1: 3 retries
def process_chunk(chunk_id):
    return download_and_process(chunk_id)

@retry(stop=stop_after_attempt(3))  # Layer 2: 3 retries
def download_and_process(chunk_id):
    for url in urls:
        download_image(url)

@retry(stop=stop_after_attempt(3))  # Layer 3: 3 retries
def download_image(url):
    return httpx.get(url)

# Result: 3 × 3 × 3 = 27 total attempts per chunk! 😱
```

### Consequences

- **Resource exhaustion**: 27× more load than intended
- **Increased latency**: Hours instead of minutes
- **Cost explosion**: 27× API calls, bandwidth, compute
- **Poor user experience**: Jobs appear stuck
- **Difficult debugging**: Unclear which layer is retrying

---

## Architecture Principles

### Principle 1: Single Retry Layer

**Each failure type should be handled by exactly ONE retry mechanism.**

```
Failure Type          → Retry Layer
---------------------|-------------
Task-level failure   → Celery
Network/API errors   → Tenacity
Transient errors     → Tenacity
Permanent errors     → None
```

### Principle 2: Fail Fast for Permanent Errors

**Don't retry errors that will never succeed.**

```python
# ✅ CORRECT: Fail immediately
if not validate_input(data):
    raise ValidationError("Invalid data")  # No retry

if response.status_code == 404:
    raise NotFoundError("Resource not found")  # No retry
```

### Principle 3: Explicit Over Implicit

**Disable automatic retries, handle explicitly.**

```python
# ✅ CORRECT: Explicit retry control
@celery_app.task(bind=True, acks_late=True)  # No autoretry
def my_task(self, data):
    try:
        return process(data)
    except InfrastructureError as e:
        # Explicitly retry only infrastructure failures
        raise self.retry(exc=e, max_retries=3, countdown=60)
```

### Principle 4: Observability First

**Always log retry attempts for debugging.**

```python
@retry(
    stop=stop_after_attempt(3),
    before_sleep=lambda retry_state: logger.warning(
        f"Retry attempt {retry_state.attempt_number}/3"
    )
)
def operation():
    pass
```

---

## Retry Layers

### Layer 1: Celery Task Retries (Infrastructure Level)

**Purpose:** Handle infrastructure and worker-level failures.

**Scope:**
- Worker crashes
- Out of memory errors
- Database connection pool exhaustion
- Unexpected system exceptions

**Configuration:**
```python
@celery_app.task(
    bind=True,
    acks_late=True,
    reject_on_worker_lost=True
)
def process_chunk_task(self, chunk_id: str):
    try:
        processor = ChunkProcessor()
        return processor.process_chunk(chunk_id)
    except (MemoryError, DatabaseConnectionError) as e:
        logger.error(f"Infrastructure failure: {e}")
        raise self.retry(exc=e, max_retries=3, countdown=60)
    except Exception as e:
        logger.error(f"Task failed permanently: {e}")
        raise
```

**When to Use:**
- ✅ Worker process crashes
- ✅ System resource exhaustion
- ✅ Database connection failures
- ✅ Unexpected exceptions that might be transient

**When NOT to Use:**
- ❌ Network timeouts (use Tenacity)
- ❌ API rate limits (use Tenacity)
- ❌ Validation errors (fail fast)
- ❌ Business logic errors (fail fast)

---

### Layer 2: Tenacity Operation Retries (Operation Level)

**Purpose:** Handle transient failures in specific operations.

**Scope:**
- HTTP/API timeouts
- Network errors
- Rate limiting (429 errors)
- Temporary service unavailability (503 errors)

**Configuration:**

```python
import _exceptions
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)


class ChunkProcessor:

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((
                _exceptions.TimeoutException,
                httpx.NetworkError,
                httpx.HTTPStatusError
        )),
        reraise=True
    )
    def _download_image(self, url: str) -> bytes:
        """
        Download image with automatic retry for transient errors.
        
        Retries:
            - Attempt 1: Immediate
            - Attempt 2: Wait 2s
            - Attempt 3: Wait 4s
        
        Raises:
            httpx.HTTPError: After all retries exhausted
        """
        response = httpx.get(url, timeout=30)

        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 5))
            time.sleep(retry_after)
            raise httpx.HTTPStatusError("Rate limited", request=None, response=response)

        response.raise_for_status()
        return response.content
```

**When to Use:**
- ✅ HTTP requests to external APIs
- ✅ Network operations
- ✅ File I/O operations
- ✅ Database queries (transient deadlocks)

**When NOT to Use:**
- ❌ On Celery task functions
- ❌ For validation logic
- ❌ For permanent errors (404, 401, 403)
- ❌ Nested inside other retry decorators

---

## When to Use What

### Decision Tree

```
Is this a Celery task function?
├─ YES → Use Celery retry (only for infrastructure failures)
└─ NO → Is this a network/API operation?
    ├─ YES → Use Tenacity retry
    └─ NO → Is the error transient?
        ├─ YES → Use Tenacity retry
        └─ NO → Fail fast (no retry)
```

### Quick Reference Table

| Error Type | Example | Retry Layer | Max Retries | Wait Strategy |
|-----------|---------|-------------|-------------|---------------|
| Worker crash | Process killed | Celery | 3 | 60s fixed |
| Out of memory | MemoryError | Celery | 3 | 60s fixed |
| Network timeout | TimeoutError | Tenacity | 3 | Exponential (2-10s) |
| API rate limit | 429 Too Many Requests | Tenacity | 3 | Exponential + Retry-After |
| Service unavailable | 503 Service Unavailable | Tenacity | 3 | Exponential (2-10s) |
| Validation error | Invalid input | None | 0 | Fail immediately |
| Not found | 404 Not Found | None | 0 | Fail immediately |
| Unauthorized | 401/403 | None | 0 | Fail immediately |

---

## Implementation Patterns

### Pattern 1: Celery Task with No Autoretry

```python
@celery_app.task(bind=True, acks_late=True)
def process_chunk_task(self, chunk_id: str) -> dict[str, Any]:
    """
    Process a chunk of images.
    
    Retry Strategy:
        - Only retries infrastructure failures
        - Business logic handles its own retries
        - Permanent errors fail immediately
    """
    try:
        processor = ChunkProcessor()
        result = processor.process_chunk(chunk_id)
        return result
        
    except (MemoryError, DatabaseConnectionError) as e:
        logger.error(f"Infrastructure failure for chunk {chunk_id}: {e}")
        raise self.retry(exc=e, max_retries=3, countdown=60)
        
    except ValidationError as e:
        logger.error(f"Validation failed for chunk {chunk_id}: {e}")
        raise
        
    except Exception as e:
        logger.exception(f"Unexpected error for chunk {chunk_id}: {e}")
        raise
```

### Pattern 2: Business Logic with Tenacity

```python
import _exceptions


class ChunkProcessor:
    """Processes image chunks with operation-level retries."""

    def process_chunk(self, chunk_id: str) -> dict[str, Any]:
        """Process chunk without retry decorator."""
        chunk = self._get_chunk(chunk_id)
        results = {'successful': 0, 'failed': 0}

        for url in chunk.urls:
            try:
                image_data = self._download_image(url)
                self._validate_and_save(image_data, chunk_id)
                results['successful'] += 1
            except httpx.HTTPError as e:
                logger.warning(f"Failed to download {url}: {e}")
                results['failed'] += 1
                continue

        return results

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((_exceptions.TimeoutException, httpx.NetworkError)),
        reraise=True
    )
    def _download_image(self, url: str) -> bytes:
        """Download image with automatic retry."""
        response = httpx.get(url, timeout=30)
        response.raise_for_status()
        return response.content
```

---

## Anti-Patterns

### ❌ Anti-Pattern 1: Nested Retry Decorators

```python
# ❌ WRONG
@celery_app.task(autoretry_for=(Exception,), max_retries=3)
def process_task(data):
    return process_with_retry(data)

@retry(stop=stop_after_attempt(3))
def process_with_retry(data):
    return operation_with_retry(data)

# Result: 3 × 3 = 9 attempts
```

**Fix:**
```python
# ✅ CORRECT
@celery_app.task(bind=True, acks_late=True)
def process_task(self, data):
    try:
        return process_logic(data)
    except InfrastructureError as e:
        raise self.retry(exc=e, max_retries=3)

def process_logic(data):
    return operation_with_retry(data)

@retry(stop=stop_after_attempt(3))
def operation_with_retry(data):
    return httpx.get(data)
```

### ❌ Anti-Pattern 2: Retrying Permanent Errors

```python
# ❌ WRONG
@retry(stop=stop_after_attempt(3))
def validate_and_process(data):
    if not is_valid(data):
        raise ValidationError("Invalid data")  # Will retry 3 times
    return process(data)
```

**Fix:**
```python
# ✅ CORRECT
def validate_and_process(data):
    if not is_valid(data):
        raise ValidationError("Invalid data")  # No retry
    return process_with_retry(data)

@retry(stop=stop_after_attempt(3))
def process_with_retry(data):
    return httpx.post(API_URL, json=data)
```

---

## Error Classification

### Custom Exception Hierarchy

PixCrawler implements a custom exception hierarchy in `builder/_exceptions.py` to enable type-based retry logic:

```python
# builder/_exceptions.py

class PermanentError(Exception):
    """Base class for errors that should NOT be retried.
    
    These errors indicate problems that will not be resolved by retrying
    the operation (e.g., validation failures, resource not found, auth errors).
    """
    pass


class TransientError(Exception):
    """Base class for errors that MAY succeed on retry.
    
    These errors indicate temporary problems that might be resolved by
    retrying after a delay (e.g., network timeouts, rate limits, service unavailable).
    """
    pass


# Permanent Error Types (No Retry)
class ValidationError(PermanentError):
    """Validation failures - data is invalid and won't become valid."""
    pass


class NotFoundError(PermanentError):
    """Resource not found (404) - resource doesn't exist."""
    pass


class AuthenticationError(PermanentError):
    """Authentication failures (401, 403) - credentials are invalid."""
    pass


class BadRequestError(PermanentError):
    """Bad request (400) - request is malformed."""
    pass


# Transient Error Types (Retry with Tenacity)
class RateLimitError(TransientError):
    """Rate limit exceeded (429) - retry after backoff."""
    pass


class ServiceUnavailableError(TransientError):
    """Service unavailable (503, 504) - temporary outage."""
    pass


class TimeoutException(TransientError):
    """Network timeout - connection or read timeout."""
    pass


class NetworkError(TransientError):
    """Network connectivity issues - DNS, connection refused, etc."""
    pass
```

### Error Classification Functions

```python
# builder/_exceptions.py

# HTTP status code to exception type mapping
HTTP_ERROR_MAP = {
    400: BadRequestError,
    401: AuthenticationError,
    403: AuthenticationError,
    404: NotFoundError,
    429: RateLimitError,
    503: ServiceUnavailableError,
    504: ServiceUnavailableError,
}


def classify_http_error(status_code: int) -> type[Exception]:
    """
    Classify HTTP status codes into permanent or transient errors.
    
    Args:
        status_code: HTTP status code from response
        
    Returns:
        Exception class (PermanentError or TransientError subclass)
        
    Examples:
        >>> classify_http_error(404)
        <class 'NotFoundError'>
        >>> classify_http_error(429)
        <class 'RateLimitError'>
        >>> classify_http_error(500)
        <class 'PermanentError'>
    """
    return HTTP_ERROR_MAP.get(status_code, PermanentError)


def classify_network_error(error: Exception) -> type[Exception]:
    """
    Classify network exceptions into appropriate error types.
    
    Args:
        error: Exception from network operation
        
    Returns:
        Exception class (TransientError subclass)
        
    Examples:
        >>> import httpx
        >>> classify_network_error(httpx.TimeoutException("timeout"))
        <class 'TimeoutException'>
        >>> classify_network_error(httpx.NetworkError("connection refused"))
        <class 'NetworkError'>
    """
    import httpx
    
    if isinstance(error, httpx.TimeoutException):
        return TimeoutException
    elif isinstance(error, (httpx.NetworkError, httpx.ConnectError)):
        return NetworkError
    else:
        return TransientError
```

### Transient Errors (Retryable)

**Custom Network Errors:**
- `builder._exceptions.TimeoutException` - Network timeouts
- `builder._exceptions.NetworkError` - Connection failures
- `builder._exceptions.RateLimitError` - Rate limiting (429)
- `builder._exceptions.ServiceUnavailableError` - Service down (503, 504)

**Standard Library Errors:**
- `httpx.TimeoutException` - HTTP client timeouts
- `httpx.NetworkError` - HTTP network errors
- `httpx.ConnectError` - Connection failures
- `ConnectionError` - Generic connection errors

**HTTP Status Codes:**
- `429 Too Many Requests` → `RateLimitError`
- `503 Service Unavailable` → `ServiceUnavailableError`
- `504 Gateway Timeout` → `ServiceUnavailableError`

**Database Errors:**
- `sqlalchemy.exc.OperationalError` - Database connection issues
- `psycopg2.OperationalError` - PostgreSQL connection issues

### Permanent Errors (Non-Retryable)

**Custom Validation Errors:**
- `builder._exceptions.ValidationError` - Data validation failures
- `builder._exceptions.NotFoundError` - Resource not found (404)
- `builder._exceptions.AuthenticationError` - Auth failures (401, 403)
- `builder._exceptions.BadRequestError` - Malformed requests (400)

**Standard Library Errors:**
- `ValueError` - Invalid values
- `TypeError` - Type mismatches
- `KeyError` - Missing required keys

**HTTP Status Codes:**
- `400 Bad Request` → `BadRequestError`
- `401 Unauthorized` → `AuthenticationError`
- `403 Forbidden` → `AuthenticationError`
- `404 Not Found` → `NotFoundError`
- `422 Unprocessable Entity` → `ValidationError`

**Business Logic:**
- `InsufficientCreditsError` - User out of credits
- `QuotaExceededError` - Usage quota exceeded
- `InvalidStateError` - Invalid state transition

### Usage in Code

```python
import builder._exceptions as exceptions
from tenacity import retry, retry_if_exception_type

# Use in Tenacity retry decorator
@retry(
    retry=retry_if_exception_type((
        exceptions.TimeoutException,
        exceptions.NetworkError,
        exceptions.RateLimitError,
        exceptions.ServiceUnavailableError
    ))
)
def download_image(url: str) -> bytes:
    try:
        response = httpx.get(url, timeout=30)
        
        # Classify HTTP errors
        if response.status_code >= 400:
            error_class = exceptions.classify_http_error(response.status_code)
            raise error_class(f"HTTP {response.status_code}: {url}")
            
        return response.content
        
    except httpx.TimeoutException as e:
        raise exceptions.TimeoutException(f"Timeout: {url}") from e
    except httpx.NetworkError as e:
        raise exceptions.NetworkError(f"Network error: {url}") from e
```

---

## Configuration Guidelines

### Celery Task Configuration

```python
CELERY_TASK_CONFIG = {
    'autoretry_for': (),  # Disable autoretry
    'acks_late': True,
    'reject_on_worker_lost': True,
    'task_time_limit': 1800,
    'task_soft_time_limit': 1500,
    'default_retry_delay': 60,
    'max_retries': 3,
}
```

### Tenacity Configuration

```python
import _exceptions
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

NETWORK_RETRY_CONFIG = {
    'stop': stop_after_attempt(3),
    'wait': wait_exponential(multiplier=1, min=2, max=10),
    'retry': retry_if_exception_type((_exceptions.TimeoutException, httpx.NetworkError)),
    'reraise': True
}


@retry(**NETWORK_RETRY_CONFIG)
def download_image(url: str) -> bytes:
    return httpx.get(url).content
```

---

## Testing Strategy

### Test Coverage Requirements

**Minimum Coverage**: 90% for retry-related code

**Required Test Categories**:
1. Error classification tests
2. Celery task retry tests
3. Tenacity operation retry tests
4. Integration tests for retry layers
5. Logging verification tests

### Unit Testing Error Classification

```python
# tests/test_error_classification.py
import pytest
import builder._exceptions as exceptions


def test_classify_http_error_permanent():
    """Test classification of permanent HTTP errors."""
    assert exceptions.classify_http_error(400) == exceptions.BadRequestError
    assert exceptions.classify_http_error(401) == exceptions.AuthenticationError
    assert exceptions.classify_http_error(403) == exceptions.AuthenticationError
    assert exceptions.classify_http_error(404) == exceptions.NotFoundError


def test_classify_http_error_transient():
    """Test classification of transient HTTP errors."""
    assert exceptions.classify_http_error(429) == exceptions.RateLimitError
    assert exceptions.classify_http_error(503) == exceptions.ServiceUnavailableError
    assert exceptions.classify_http_error(504) == exceptions.ServiceUnavailableError


def test_classify_http_error_unknown():
    """Test classification of unknown HTTP errors defaults to permanent."""
    assert exceptions.classify_http_error(500) == exceptions.PermanentError
    assert exceptions.classify_http_error(418) == exceptions.PermanentError


def test_exception_hierarchy():
    """Test that exception hierarchy is correct."""
    # Permanent errors
    assert issubclass(exceptions.ValidationError, exceptions.PermanentError)
    assert issubclass(exceptions.NotFoundError, exceptions.PermanentError)
    assert issubclass(exceptions.AuthenticationError, exceptions.PermanentError)
    assert issubclass(exceptions.BadRequestError, exceptions.PermanentError)
    
    # Transient errors
    assert issubclass(exceptions.RateLimitError, exceptions.TransientError)
    assert issubclass(exceptions.ServiceUnavailableError, exceptions.TransientError)
    assert issubclass(exceptions.TimeoutException, exceptions.TransientError)
    assert issubclass(exceptions.NetworkError, exceptions.TransientError)
```

### Unit Testing Celery Task Retries

```python
# tests/test_task_retry.py
import pytest
from unittest.mock import Mock, patch
from builder.tasks import process_chunk_task
import builder._exceptions as exceptions


def test_task_no_autoretry():
    """Verify task does not use autoretry_for parameter."""
    # Check task configuration
    task_options = process_chunk_task.options
    assert 'autoretry_for' not in task_options or task_options.get('autoretry_for') == ()
    assert task_options.get('bind') is True
    assert task_options.get('acks_late') is True


def test_task_explicit_retry_infrastructure_failure():
    """Verify task retries on infrastructure failures."""
    with patch('builder.tasks.ChunkProcessor') as mock_processor:
        mock_processor.return_value.process_chunk.side_effect = MemoryError("OOM")
        
        # Create mock task instance
        mock_self = Mock()
        mock_self.request.retries = 0
        
        with pytest.raises(Exception):  # Will raise retry exception
            process_chunk_task(mock_self, "chunk_123")
        
        # Verify retry was called
        mock_self.retry.assert_called_once()
        call_kwargs = mock_self.retry.call_args[1]
        assert call_kwargs['max_retries'] == 3
        assert call_kwargs['countdown'] == 60


def test_task_no_retry_permanent_error():
    """Verify task does not retry permanent errors."""
    with patch('builder.tasks.ChunkProcessor') as mock_processor:
        mock_processor.return_value.process_chunk.side_effect = exceptions.ValidationError("Invalid")
        
        mock_self = Mock()
        
        with pytest.raises(exceptions.ValidationError):
            process_chunk_task(mock_self, "chunk_123")
        
        # Verify retry was NOT called
        mock_self.retry.assert_not_called()


def test_task_retry_count_limit():
    """Verify task respects max retry limit."""
    with patch('builder.tasks.ChunkProcessor') as mock_processor:
        mock_processor.return_value.process_chunk.side_effect = MemoryError("OOM")
        
        mock_self = Mock()
        mock_self.request.retries = 3  # Already at max
        mock_self.retry.side_effect = Exception("Max retries exceeded")
        
        with pytest.raises(Exception):
            process_chunk_task(mock_self, "chunk_123")
```

### Unit Testing Tenacity Retries

```python
# tests/test_network_retry.py
import pytest
from unittest.mock import Mock, patch
import builder._exceptions as exceptions
from builder._downloader import ImageDownloader


def test_download_retries_on_timeout():
    """Test that download retries on timeout."""
    mock_client = Mock()
    mock_client.get.side_effect = [
        exceptions.TimeoutException("Timeout 1"),
        exceptions.TimeoutException("Timeout 2"),
        Mock(content=b"image_data", status_code=200)
    ]

    downloader = ImageDownloader()
    downloader.http_client = mock_client

    result = downloader.download_image("http://example.com/image.jpg")

    assert result == b"image_data"
    assert mock_client.get.call_count == 3


def test_download_retries_on_network_error():
    """Test that download retries on network errors."""
    mock_client = Mock()
    mock_client.get.side_effect = [
        exceptions.NetworkError("Connection refused"),
        Mock(content=b"image_data", status_code=200)
    ]

    downloader = ImageDownloader()
    downloader.http_client = mock_client

    result = downloader.download_image("http://example.com/image.jpg")

    assert result == b"image_data"
    assert mock_client.get.call_count == 2


def test_download_no_retry_on_404():
    """Test that download doesn't retry on 404."""
    mock_client = Mock()
    mock_response = Mock(status_code=404)
    mock_client.get.return_value = mock_response

    downloader = ImageDownloader()
    downloader.http_client = mock_client

    with pytest.raises(exceptions.NotFoundError):
        downloader.download_image("http://example.com/image.jpg")

    assert mock_client.get.call_count == 1


def test_download_no_retry_on_401():
    """Test that download doesn't retry on authentication errors."""
    mock_client = Mock()
    mock_response = Mock(status_code=401)
    mock_client.get.return_value = mock_response

    downloader = ImageDownloader()
    downloader.http_client = mock_client

    with pytest.raises(exceptions.AuthenticationError):
        downloader.download_image("http://example.com/image.jpg")

    assert mock_client.get.call_count == 1


def test_download_max_retries():
    """Test that download respects max retry limit."""
    mock_client = Mock()
    mock_client.get.side_effect = exceptions.TimeoutException("Timeout")

    downloader = ImageDownloader()
    downloader.http_client = mock_client

    with pytest.raises(exceptions.TimeoutException):
        downloader.download_image("http://example.com/image.jpg")

    # Should try 3 times total
    assert mock_client.get.call_count == 3


def test_download_exponential_backoff():
    """Test that download uses exponential backoff."""
    import time
    
    mock_client = Mock()
    call_times = []
    
    def record_time(*args, **kwargs):
        call_times.append(time.time())
        raise exceptions.TimeoutException("Timeout")
    
    mock_client.get.side_effect = record_time

    downloader = ImageDownloader()
    downloader.http_client = mock_client

    with pytest.raises(exceptions.TimeoutException):
        downloader.download_image("http://example.com/image.jpg")

    # Verify exponential backoff timing
    assert len(call_times) == 3
    # Second attempt should be ~2s after first
    assert call_times[1] - call_times[0] >= 2.0
    # Third attempt should be ~4s after second
    assert call_times[2] - call_times[1] >= 4.0
```

### Integration Testing Retry Layers

```python
# tests/integration/test_retry_layers.py
import pytest
from unittest.mock import Mock, patch
import builder._exceptions as exceptions


def test_single_retry_layer_network_failure():
    """Verify only Tenacity retries on network failure, not Celery."""
    retry_count = {'tenacity': 0, 'celery': 0}
    
    def mock_download(*args, **kwargs):
        retry_count['tenacity'] += 1
        if retry_count['tenacity'] < 3:
            raise exceptions.TimeoutException("Timeout")
        return b"image_data"
    
    with patch('builder._downloader.ImageDownloader.download_image', side_effect=mock_download):
        # Simulate task execution
        from builder.tasks import process_chunk_task
        
        mock_self = Mock()
        mock_self.request.retries = 0
        
        # Should succeed after Tenacity retries
        result = process_chunk_task(mock_self, "chunk_123")
        
        # Verify only Tenacity retried (3 attempts)
        assert retry_count['tenacity'] == 3
        # Verify Celery did NOT retry
        mock_self.retry.assert_not_called()


def test_single_retry_layer_infrastructure_failure():
    """Verify only Celery retries on infrastructure failure, not Tenacity."""
    with patch('builder.tasks.ChunkProcessor') as mock_processor:
        mock_processor.return_value.process_chunk.side_effect = MemoryError("OOM")
        
        mock_self = Mock()
        mock_self.request.retries = 0
        
        with pytest.raises(Exception):
            from builder.tasks import process_chunk_task
            process_chunk_task(mock_self, "chunk_123")
        
        # Verify Celery retry was called
        mock_self.retry.assert_called_once()
        call_kwargs = mock_self.retry.call_args[1]
        assert call_kwargs['max_retries'] == 3


def test_total_attempts_not_exponential():
    """Verify total attempts = 3, not 9 (3×3)."""
    attempt_count = 0
    
    def mock_download(*args, **kwargs):
        nonlocal attempt_count
        attempt_count += 1
        raise exceptions.TimeoutException("Timeout")
    
    with patch('builder._downloader.ImageDownloader.download_image', side_effect=mock_download):
        from builder.tasks import process_chunk_task
        
        mock_self = Mock()
        
        with pytest.raises(exceptions.TimeoutException):
            process_chunk_task(mock_self, "chunk_123")
        
        # Should be exactly 3 attempts (Tenacity only)
        assert attempt_count == 3
        # Celery should NOT have retried
        mock_self.retry.assert_not_called()
```

### Testing Logging

```python
# tests/test_retry_logging.py
import pytest
from unittest.mock import Mock, patch
import builder._exceptions as exceptions


def test_retry_attempts_logged(caplog):
    """Test that all retry attempts are logged."""
    with patch('builder._downloader.httpx.get') as mock_get:
        mock_get.side_effect = [
            exceptions.TimeoutException("Timeout 1"),
            exceptions.TimeoutException("Timeout 2"),
            Mock(content=b"data", status_code=200)
        ]
        
        from builder._downloader import ImageDownloader
        downloader = ImageDownloader()
        downloader.download_image("http://example.com/image.jpg")
        
        # Verify retry attempts were logged
        assert "Retry attempt 1" in caplog.text or "attempt_number" in caplog.text
        assert "Retry attempt 2" in caplog.text or "attempt_number" in caplog.text


def test_log_levels_appropriate(caplog):
    """Test that log levels are appropriate for different scenarios."""
    # Success should be INFO
    # Retries should be WARNING
    # Final failure should be ERROR
    pass  # Implementation depends on actual logging setup
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Tasks Retrying Too Many Times

**Symptoms:**
- Tasks appear to retry 9, 27, or more times
- Logs show multiple retry layers executing
- High resource usage and costs

**Diagnosis:**
```python
# Check task configuration
print(my_task.options)
# Should NOT have 'autoretry_for' or it should be empty tuple ()

# Check for nested retry decorators
# Search codebase for multiple @retry decorators in call chain
```

**Solution:**
```python
# ✅ Remove autoretry_for from task decorator
@celery_app.task(bind=True, acks_late=True)  # No autoretry_for
def my_task(self, data):
    try:
        return process(data)
    except InfrastructureError as e:
        raise self.retry(exc=e, max_retries=3, countdown=60)

# ✅ Remove nested retry decorators
# Only apply @retry to the lowest-level operation
```

#### Issue 2: Permanent Errors Being Retried

**Symptoms:**
- 404, 401, 403 errors being retried
- Validation errors being retried
- Wasted resources on operations that will never succeed

**Diagnosis:**
```python
# Check if error classification is being used
# Look for broad exception catching in retry decorators
@retry(retry=retry_if_exception_type(Exception))  # ❌ Too broad!
```

**Solution:**
```python
# ✅ Use specific exception types
import builder._exceptions as exceptions

@retry(
    retry=retry_if_exception_type((
        exceptions.TimeoutException,
        exceptions.NetworkError,
        exceptions.RateLimitError,
        exceptions.ServiceUnavailableError
    ))
)
def download_image(url: str) -> bytes:
    try:
        response = httpx.get(url)
        
        # Classify errors properly
        if response.status_code >= 400:
            error_class = exceptions.classify_http_error(response.status_code)
            raise error_class(f"HTTP {response.status_code}")
            
        return response.content
    except httpx.TimeoutException as e:
        raise exceptions.TimeoutException(str(e)) from e
```

#### Issue 3: Retries Not Happening When Expected

**Symptoms:**
- Operations fail immediately without retry
- Expected transient errors not being retried

**Diagnosis:**
```python
# Check exception types being raised
# Verify they match retry configuration

# Check if reraise=True is set
@retry(reraise=True)  # Required to propagate final failure
```

**Solution:**
```python
# ✅ Ensure correct exception types
@retry(
    retry=retry_if_exception_type((
        exceptions.TimeoutException,  # Must match raised exception
        exceptions.NetworkError
    )),
    reraise=True  # Required
)
def operation():
    try:
        return httpx.get(url)
    except httpx.TimeoutException as e:
        # Convert to custom exception type
        raise exceptions.TimeoutException(str(e)) from e
```

#### Issue 4: Retry Timing Issues

**Symptoms:**
- Retries happening too fast (overwhelming service)
- Retries happening too slow (poor user experience)

**Diagnosis:**
```python
# Check wait strategy configuration
@retry(wait=wait_fixed(1))  # Too fast for rate limits
@retry(wait=wait_fixed(300))  # Too slow for timeouts
```

**Solution:**
```python
# ✅ Use exponential backoff with limits
@retry(
    wait=wait_exponential(
        multiplier=1,  # Base multiplier
        min=2,         # Minimum wait (2s)
        max=10         # Maximum wait (10s)
    )
)
# Results in: 2s, 4s, 8s (capped at 10s)

# ✅ For rate limits, respect Retry-After header
if response.status_code == 429:
    retry_after = int(response.headers.get('Retry-After', 5))
    time.sleep(retry_after)
    raise exceptions.RateLimitError("Rate limited")
```

#### Issue 5: Missing Retry Logs

**Symptoms:**
- Cannot see retry attempts in logs
- Difficult to debug retry behavior

**Diagnosis:**
```python
# Check if before_sleep callback is configured
@retry(stop=stop_after_attempt(3))  # No logging!
```

**Solution:**
```python
# ✅ Add before_sleep callback
from utility.logging_config import get_logger

logger = get_logger(__name__)

@retry(
    stop=stop_after_attempt(3),
    before_sleep=lambda retry_state: logger.warning(
        "Retry attempt",
        attempt_number=retry_state.attempt_number,
        max_attempts=3,
        exception=str(retry_state.outcome.exception())
    )
)
def operation():
    pass
```

#### Issue 6: Database Connection Pool Exhaustion

**Symptoms:**
- "Too many connections" errors
- Tasks failing with connection errors
- Retries making problem worse

**Diagnosis:**
```python
# Check if connections are being properly closed
# Check connection pool size vs concurrent tasks
```

**Solution:**
```python
# ✅ Use context managers for connections
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,          # Max connections
    max_overflow=20,       # Extra connections when needed
    pool_timeout=30,       # Wait time for connection
    pool_recycle=3600      # Recycle connections after 1 hour
)

# ✅ Always use context managers
with engine.connect() as conn:
    result = conn.execute(query)
# Connection automatically returned to pool

# ✅ Retry database connection errors
@celery_app.task(bind=True, acks_late=True)
def my_task(self, data):
    try:
        return process(data)
    except sqlalchemy.exc.OperationalError as e:
        logger.error("Database connection error", error=str(e))
        raise self.retry(exc=e, max_retries=3, countdown=60)
```

#### Issue 7: Celery Task Not Retrying

**Symptoms:**
- Task fails immediately without retry
- `self.retry()` not working

**Diagnosis:**
```python
# Check if bind=True is set
@celery_app.task()  # ❌ Missing bind=True
def my_task(data):
    self.retry()  # ❌ 'self' not available!
```

**Solution:**
```python
# ✅ Add bind=True to task decorator
@celery_app.task(bind=True, acks_late=True)
def my_task(self, data):  # Note: 'self' parameter added
    try:
        return process(data)
    except InfrastructureError as e:
        raise self.retry(exc=e, max_retries=3, countdown=60)
```

### Debugging Checklist

When debugging retry issues, check:

- [ ] Task has `bind=True` and `acks_late=True`
- [ ] Task does NOT have `autoretry_for` parameter
- [ ] Only ONE retry layer per failure type
- [ ] Exception types match retry configuration
- [ ] Error classification is being used
- [ ] Permanent errors are NOT in retry list
- [ ] `reraise=True` is set on Tenacity decorators
- [ ] Retry attempts are being logged
- [ ] Wait strategy is appropriate for error type
- [ ] Max retries is set to 3 (not higher)
- [ ] Connection pools are properly configured
- [ ] Context managers are used for resources

### Performance Monitoring

**Key Metrics to Track:**

```python
# Log these metrics for monitoring
logger.info(
    "Retry metrics",
    operation="download_image",
    total_attempts=3,
    successful_attempt=2,
    total_duration_sec=6.5,
    error_type="TimeoutException"
)
```

**Azure Monitor Queries:**

```kusto
// Average retry count per operation
logs
| where message contains "Retry metrics"
| summarize avg(total_attempts) by operation

// Most common retry errors
logs
| where message contains "Retry metrics"
| summarize count() by error_type
| order by count_ desc

// Operations with high retry rates
logs
| where message contains "Retry metrics"
| where total_attempts >= 3
| summarize count() by operation
| order by count_ desc
```

---

## Summary

### Key Takeaways

1. **Single retry layer per failure type**
2. **Celery for infrastructure failures**
3. **Tenacity for operation failures**
4. **Fail fast for permanent errors**
5. **Always log retries**
6. **Test retry behavior**

### Quick Decision Guide

```
Need to retry?
├─ Is it a Celery task? → Use Celery retry (infrastructure only)
├─ Is it a network call? → Use Tenacity retry
├─ Is it transient? → Use Tenacity retry
└─ Is it permanent? → Don't retry
```

### Configuration Checklist

- [ ] Disable Celery autoretry by default
- [ ] Use `acks_late=True` for all tasks
- [ ] Classify all error types
- [ ] Add Tenacity to network operations
- [ ] Log all retry attempts
- [ ] Write retry tests
- [ ] Document retry strategy per task

---

**Document Owner:** Backend Team  
**Review Cycle:** Quarterly  
**Next Review:** 2025-01-30
