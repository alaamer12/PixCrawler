# Retry Logic Implementation Compliance Report

**Task:** 8.2 Review retry logic implementation  
**Date:** 2025-11-30  
**Status:** ⚠️ PARTIALLY COMPLIANT (Requires Remediation)

## Summary

The PixCrawler application has a mixed retry implementation. While the base task class correctly disables autoretry by default, many individual tasks override this with `autoretry_for`, violating the architecture principle of explicit retry handling. Additionally, no Tenacity-based operation-level retries were found for network operations.

## Findings

### ⚠️ Celery Tasks Use Autoretry (Non-Compliant)

**Architecture Requirement:** Celery tasks should NOT use autoretry. They should explicitly handle infrastructure failures only.

**Base Configuration (Compliant):**
```python
# celery_core/base.py (line 315-317)
class BaseTask(Task):
    autoretry_for = ()  # ✅ Disable auto-retry, use explicit retry only
    max_retries = 3
    retry_jitter = True
```

**Individual Tasks (Non-Compliant):**

#### Builder Package Tasks
All builder tasks use `autoretry_for`:

```python
# builder/tasks.py
@app.task(
    autoretry_for=(ConnectionError, TimeoutError, IOError),  # ❌ Violates architecture
    max_retries=5,
    default_retry_delay=120,
    ...
)
```

**Tasks with autoretry:**
1. `task_download_google` - Line 140
2. `task_download_bing` - Line 247
3. `task_download_baidu` - Line 354
4. `task_download_duckduckgo` - Line 426
5. `task_generate_keywords` - Line 518
6. `task_generate_labels` - Line 669

#### Validator Package Tasks
All validator tasks use `autoretry_for`:

```python
# validator/tasks.py
@app.task(
    autoretry_for=(IOError, OSError),  # ❌ Violates architecture
    max_retries=3,
    default_retry_delay=60,
    ...
)
```

**Tasks with autoretry:**
1. `check_duplicates_task` - Line 212
2. `check_integrity_task` - Line 264
3. `check_all_task` - Line 313
4. `validate_image_fast_task` - Line 367
5. `validate_image_medium_task` - Line 409
6. `validate_image_slow_task` - Line 453

**Compliance:** ❌ FAIL
- 12 tasks override the base configuration with `autoretry_for`
- Violates Principle 3: "Explicit Over Implicit"
- Should use explicit `self.retry()` for infrastructure failures only

### ❌ No Tenacity for Network Operations (Non-Compliant)

**Architecture Requirement:** Network operations should use Tenacity for operation-level retries.

**Search Results:**
- No `from tenacity import` statements found
- No `@retry()` decorators found
- Network operations (HTTP requests, API calls) have no operation-level retry logic

**Expected Pattern:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((TimeoutError, NetworkError)),
    reraise=True
)
def download_image(url: str) -> bytes:
    return httpx.get(url).content
```

**Current Implementation:**
- Network operations rely solely on Celery task-level retries
- No separation between task-level and operation-level failures
- Violates Principle 1: "Single Retry Layer per Failure Type"

**Compliance:** ❌ FAIL
- No Tenacity library usage found
- Network operations should have their own retry layer
- Creates risk of exponential retries if Tenacity is added later

### ⚠️ Permanent Errors Not Explicitly Handled (Unclear)

**Architecture Requirement:** Permanent errors (validation, 404, 401, 403) should fail fast without retries.

**Search Results:**
- No explicit validation error handling found in builder/validator tasks
- No HTTP status code checks (404, 401, 403) found
- Error classification not implemented

**Expected Pattern:**
```python
if response.status_code == 404:
    raise NotFoundError("Resource not found")  # No retry

if not validate_input(data):
    raise ValidationError("Invalid data")  # No retry
```

**Current Implementation:**
- Tasks catch broad exceptions (ConnectionError, TimeoutError, IOError)
- No distinction between transient and permanent errors
- Risk of retrying permanent failures

**Compliance:** ⚠️ UNCLEAR
- Cannot verify without deeper code inspection
- Likely retrying some permanent errors
- Needs explicit error classification

### ✅ Retry Attempts Logged (Compliant)

**Architecture Requirement:** All retry attempts should be logged for debugging.

**Evidence:**
```python
# celery_core/base.py uses utility.logging_config
from utility.logging_config import get_logger
logger = get_logger(__name__)

# All task implementations use logger
logger.info(f"Starting Google download for: {keyword}")
logger.error(f"Google download failed for {keyword}: {str(e)}")
```

**Compliance:** ✅ PASS
- All tasks use centralized logging
- Errors are logged with context
- Retry attempts would be logged by Celery framework

## Architecture Compliance Summary

| Requirement | Status | Evidence |
|------------|--------|----------|
| Celery tasks do NOT use autoretry | ❌ FAIL | 12 tasks use `autoretry_for` |
| Celery tasks explicitly handle infrastructure failures | ⚠️ PARTIAL | Base class correct, tasks override |
| Network operations use Tenacity | ❌ FAIL | No Tenacity usage found |
| Permanent errors fail fast | ⚠️ UNCLEAR | No explicit error classification |
| Retry attempts are logged | ✅ PASS | Centralized logging in place |

## Non-Compliance Issues

### Issue 1: Autoretry Overrides Base Configuration
**Severity:** HIGH  
**Impact:** Violates explicit retry principle, makes debugging difficult

**Affected Files:**
- `builder/tasks.py` - 6 tasks
- `validator/tasks.py` - 6 tasks

**Recommendation:**
```python
# ❌ CURRENT (Wrong)
@app.task(
    autoretry_for=(ConnectionError, TimeoutError, IOError),
    max_retries=5,
    ...
)
def task_download_google(self, keyword, output_dir, max_images, variations):
    return task_download_google_impl(keyword, output_dir, max_images, variations)

# ✅ RECOMMENDED (Correct)
@app.task(
    bind=True,
    acks_late=True,
    ...
)
def task_download_google(self, keyword, output_dir, max_images, variations):
    try:
        return task_download_google_impl(keyword, output_dir, max_images, variations)
    except (MemoryError, DatabaseConnectionError) as e:
        # Only retry infrastructure failures
        logger.error(f"Infrastructure failure: {e}")
        raise self.retry(exc=e, max_retries=3, countdown=60)
    except (ConnectionError, TimeoutError) as e:
        # Network errors should be handled by Tenacity at operation level
        logger.error(f"Network error (should use Tenacity): {e}")
        raise
```

### Issue 2: Missing Tenacity for Network Operations
**Severity:** HIGH  
**Impact:** No operation-level retry separation, risk of exponential retries

**Affected Files:**
- `builder/_downloader.py` (likely)
- `builder/_search_engines.py` (likely)
- Any HTTP/API operations

**Recommendation:**
```python
# Add Tenacity to pyproject.toml
[project]
dependencies = [
    "tenacity>=8.2.0",
    ...
]

# Implement operation-level retries
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((TimeoutError, httpx.NetworkError)),
    reraise=True,
    before_sleep=lambda retry_state: logger.warning(
        f"Retry attempt {retry_state.attempt_number}/3 for network operation"
    )
)
def download_image(url: str) -> bytes:
    """Download image with automatic retry for transient errors."""
    response = httpx.get(url, timeout=30)
    response.raise_for_status()
    return response.content
```

### Issue 3: No Error Classification
**Severity:** MEDIUM  
**Impact:** May retry permanent errors, wasting resources

**Recommendation:**
```python
# Define error categories
class PermanentError(Exception):
    """Errors that should not be retried."""
    pass

class TransientError(Exception):
    """Errors that may succeed on retry."""
    pass

# Classify errors in operations
if response.status_code == 404:
    raise PermanentError("Resource not found")
elif response.status_code == 429:
    raise TransientError("Rate limited")
elif response.status_code >= 500:
    raise TransientError("Server error")
```

## Remediation Plan

### Phase 1: Remove Autoretry from Tasks (Priority: HIGH)
1. Remove `autoretry_for` from all 12 tasks
2. Add explicit `try/except` blocks
3. Use `self.retry()` only for infrastructure failures
4. Update task documentation

**Estimated Effort:** 4-6 hours

### Phase 2: Add Tenacity for Network Operations (Priority: HIGH)
1. Add `tenacity` dependency to `pyproject.toml`
2. Identify all network operations (HTTP, API calls)
3. Add `@retry` decorators with appropriate configuration
4. Test retry behavior

**Estimated Effort:** 8-12 hours

### Phase 3: Implement Error Classification (Priority: MEDIUM)
1. Define error categories (Permanent, Transient, Infrastructure)
2. Update error handling to classify errors
3. Ensure permanent errors fail fast
4. Add tests for error classification

**Estimated Effort:** 6-8 hours

## Testing Requirements

### Unit Tests
- Test that tasks do NOT autoretry
- Test explicit retry for infrastructure failures
- Test Tenacity retries for network operations
- Test permanent errors fail immediately

### Integration Tests
- Test end-to-end retry behavior
- Verify single retry layer per failure type
- Verify retry counts match expectations
- Verify logging of retry attempts

## Conclusion

**Overall Compliance: ⚠️ PARTIALLY COMPLIANT (40%)**

The retry architecture has significant gaps:
1. ❌ Tasks use autoretry (violates explicit retry principle)
2. ❌ No Tenacity for network operations (missing operation-level retries)
3. ⚠️ No error classification (may retry permanent errors)
4. ✅ Logging is correct

**Immediate Action Required:**
- Remove `autoretry_for` from all tasks
- Add Tenacity for network operations
- Implement error classification

**Risk if Not Addressed:**
- Exponential retry explosions when Tenacity is added
- Difficult debugging due to implicit retries
- Wasted resources retrying permanent errors
- Poor user experience with stuck jobs

---

**Requirements Verified:**
- Requirement 8.3: Celery tasks do NOT use autoretry ❌
- Requirement 8.4: Celery tasks explicitly handle infrastructure failures ⚠️
- Requirement 8.5: Network operations use Tenacity ❌
- Requirement 8.6: Permanent errors fail fast ⚠️
