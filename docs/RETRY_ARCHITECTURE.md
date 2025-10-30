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
            httpx.TimeoutException,
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
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
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

### Transient Errors (Retryable)

**Network Errors:**
- `httpx.TimeoutException`
- `httpx.NetworkError`
- `httpx.ConnectError`
- `ConnectionError`

**HTTP Status Codes:**
- `429 Too Many Requests`
- `503 Service Unavailable`
- `504 Gateway Timeout`

**Database Errors:**
- `sqlalchemy.exc.OperationalError`
- `psycopg2.OperationalError`

### Permanent Errors (Non-Retryable)

**Validation Errors:**
- `ValidationError`
- `ValueError`
- `TypeError`

**HTTP Status Codes:**
- `400 Bad Request`
- `401 Unauthorized`
- `403 Forbidden`
- `404 Not Found`
- `422 Unprocessable Entity`

**Business Logic:**
- `InsufficientCreditsError`
- `QuotaExceededError`
- `InvalidStateError`

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
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

NETWORK_RETRY_CONFIG = {
    'stop': stop_after_attempt(3),
    'wait': wait_exponential(multiplier=1, min=2, max=10),
    'retry': retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    'reraise': True
}

@retry(**NETWORK_RETRY_CONFIG)
def download_image(url: str) -> bytes:
    return httpx.get(url).content
```

---

## Testing Strategy

### Unit Testing Retries

```python
import pytest
from unittest.mock import Mock

def test_download_retries_on_timeout():
    """Test that download retries on timeout."""
    mock_client = Mock()
    mock_client.get.side_effect = [
        httpx.TimeoutException("Timeout 1"),
        httpx.TimeoutException("Timeout 2"),
        Mock(content=b"image_data", status_code=200)
    ]
    
    processor = ChunkProcessor()
    processor.http_client = mock_client
    
    result = processor._download_image("http://example.com/image.jpg")
    
    assert result == b"image_data"
    assert mock_client.get.call_count == 3

def test_download_no_retry_on_404():
    """Test that download doesn't retry on 404."""
    mock_client = Mock()
    response = Mock(status_code=404)
    mock_client.get.return_value = response
    response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Not found", request=None, response=response
    )
    
    processor = ChunkProcessor()
    processor.http_client = mock_client
    
    with pytest.raises(httpx.HTTPStatusError):
        processor._download_image("http://example.com/image.jpg")
    
    assert mock_client.get.call_count == 1
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
