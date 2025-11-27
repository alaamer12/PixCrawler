# API v1 Endpoint Tests

This directory contains comprehensive integration tests for all refactored API v1 endpoints.

## Test Files

### ✅ test_auth.py
Tests for authentication endpoints (`/api/v1/auth`):
- GET `/me` - Get current user profile
- POST `/verify-token` - Verify JWT token
- POST `/sync-profile` - Sync user profile
- Response model validation
- OpenAPI schema generation
- Complete authentication flow integration tests

**Test Classes:**
- `TestGetCurrentUserProfile` - 3 tests
- `TestVerifyToken` - 3 tests
- `TestSyncUserProfile` - 4 tests
- `TestOpenAPISchema` - 4 tests
- `TestIntegrationFlow` - 1 test

**Total: 15 tests**

### ✅ test_crawl_jobs.py
Tests for crawl job endpoints (`/api/v1/crawl-jobs`):
- GET `/` - List crawl jobs with pagination
- POST `/` - Create crawl job
- GET `/{job_id}` - Get crawl job details
- POST `/{job_id}/cancel` - Cancel crawl job
- POST `/{job_id}/retry` - Retry failed job
- GET `/{job_id}/logs` - Get job logs
- GET `/{job_id}/progress` - Get job progress
- Response model validation
- OpenAPI schema generation

**Test Classes:**
- `TestListCrawlJobs` - 3 tests
- `TestCreateCrawlJob` - 3 tests
- `TestGetCrawlJob` - 3 tests
- `TestCancelCrawlJob` - 3 tests
- `TestRetryCrawlJob` - 2 tests
- `TestGetCrawlJobLogs` - 1 test
- `TestGetCrawlJobProgress` - 1 test
- `TestOpenAPISchema` - 2 tests

**Total: 18 tests**

### ✅ test_notifications.py
Tests for notification endpoints (`/api/v1/notifications`):
- GET `/notifications` - List notifications with pagination
- PATCH `/notifications/{notification_id}` - Mark as read
- POST `/notifications/mark-all-read` - Mark all as read
- Response model validation
- OpenAPI schema generation
- Complete notification workflow integration tests

**Test Classes:**
- `TestListNotifications` - 5 tests
- `TestMarkAsRead` - 3 tests
- `TestMarkAllRead` - 3 tests
- `TestOpenAPISchema` - 3 tests
- `TestIntegrationFlow` - 1 test

**Total: 15 tests**

### ✅ test_projects.py
Tests for project endpoints (`/api/v1/projects`):
- GET `/projects` - List projects
- POST `/projects` - Create project
- GET `/projects/{project_id}` - Get project details
- PATCH `/projects/{project_id}` - Update project
- DELETE `/projects/{project_id}` - Delete project
- Response model validation
- OpenAPI schema generation
- Complete project workflow integration tests

**Test Classes:**
- `TestListProjects` - 4 tests
- `TestCreateProject` - 3 tests
- `TestGetProject` - 3 tests
- `TestUpdateProject` - 3 tests
- `TestDeleteProject` - 2 tests
- `TestOpenAPISchema` - 3 tests
- `TestIntegrationFlow` - 1 test

**Total: 19 tests**

### ✅ test_storage.py
Tests for storage endpoints (`/api/v1/storage`):
- GET `/usage/` - Get storage usage
- GET `/files/` - List storage files
- POST `/cleanup/` - Cleanup old files
- GET `/presigned-url/` - Generate presigned URL
- Response model validation
- OpenAPI schema generation
- Complete storage workflow integration tests

**Test Classes:**
- `TestGetStorageUsage` - 3 tests
- `TestListStorageFiles` - 4 tests
- `TestCleanupOldFiles` - 3 tests
- `TestGetPresignedUrl` - 5 tests
- `TestOpenAPISchema` - 4 tests
- `TestIntegrationFlow` - 1 test

**Total: 20 tests**

## Test Coverage Summary

**Total Test Files:** 5  
**Total Test Classes:** 28  
**Total Tests:** 87

## Test Structure

Each test file follows a consistent structure:

1. **Fixtures**
   - `mock_service` - Mock service for the endpoint
   - `mock_user` - Mock authenticated user
   - `sample_data` - Sample data for testing
   - `override_dependencies` - Override FastAPI dependencies

2. **Test Classes**
   - Organized by endpoint/functionality
   - Clear test names describing what is being tested
   - Comprehensive assertions

3. **Test Categories**
   - Success cases
   - Error cases (404, 400, 422, etc.)
   - Response model validation
   - OpenAPI schema validation
   - Integration flows

## Running Tests

### Run all API v1 tests:
```bash
pytest backend/tests/api/v1/ -v
```

### Run specific test file:
```bash
pytest backend/tests/api/v1/test_auth.py -v
```

### Run specific test class:
```bash
pytest backend/tests/api/v1/test_auth.py::TestGetCurrentUserProfile -v
```

### Run specific test:
```bash
pytest backend/tests/api/v1/test_auth.py::TestGetCurrentUserProfile::test_get_current_user_profile_success -v
```

### Run with coverage:
```bash
pytest backend/tests/api/v1/ --cov=backend/api/v1 --cov-report=html
```

## Test Requirements

The tests require the following dependencies:
- pytest
- pytest-asyncio
- fastapi
- httpx (for TestClient)
- All backend dependencies

## Known Issues

Some tests may require additional setup:
1. Missing optional dependencies (sse-starlette, azure-storage-blob)
2. Database connection for integration tests
3. Redis connection for rate limiting tests

These can be mocked or skipped in CI/CD environments.

## Best Practices

1. **Isolation**: Each test is independent and doesn't rely on other tests
2. **Mocking**: External dependencies are mocked to avoid side effects
3. **Assertions**: Multiple assertions verify different aspects of responses
4. **Documentation**: Clear docstrings explain what each test validates
5. **Organization**: Tests are grouped by functionality using classes
6. **Coverage**: Tests cover success cases, error cases, and edge cases

## Future Enhancements

- Add performance tests for pagination
- Add security tests for authentication bypass attempts
- Add load tests for concurrent requests
- Add tests for rate limiting behavior
- Add tests for WebSocket endpoints (if applicable)
