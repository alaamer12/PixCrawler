# Requirements Document

## Introduction

This specification defines the requirements for completing the PixCrawler Postman mock collection and OpenAPI specification. The goal is to add all missing backend API endpoints to enable complete frontend development without running the Python backend. This will accelerate frontend development velocity by providing realistic mock responses for all API endpoints.

## Glossary

- **Postman Collection**: A JSON file containing API endpoint definitions, request examples, and mock responses used for API testing and development
- **OpenAPI Specification**: A standard format (formerly Swagger) for describing RESTful APIs in a machine-readable format
- **Prism Mock Server**: A tool that generates a mock API server from an OpenAPI specification
- **Mock Response**: A predefined response returned by a mock server without executing actual backend logic
- **Success Case**: An API response with 200-level HTTP status codes indicating successful operation
- **Frontend**: The Next.js 15 web application that consumes the backend API
- **Backend**: The FastAPI Python service that provides the actual API implementation

## Requirements

### Requirement 1: Crawl Jobs Endpoints

**User Story:** As a frontend developer, I want complete mock endpoints for crawl job management, so that I can develop and test the job creation, monitoring, and control features without running the backend.

#### Acceptance Criteria

1. WHEN a frontend developer requests to create a crawl job via POST /jobs/, THE mock server SHALL return a 201 Created response with a complete job object including id, project_id, name, keywords, status, progress, and chunk tracking fields
2. WHEN a frontend developer requests a specific job via GET /jobs/{job_id}, THE mock server SHALL return a 200 OK response with detailed job information including current status and progress metrics
3. WHEN a frontend developer starts a job via POST /jobs/{job_id}/start, THE mock server SHALL return a 200 OK response with task_ids array and confirmation message
4. WHEN a frontend developer cancels a job via POST /jobs/{job_id}/cancel, THE mock server SHALL return a 200 OK response with revoked task count and status update
5. WHEN a frontend developer retries a failed job via POST /jobs/{job_id}/retry, THE mock server SHALL return a 200 OK response with reset job state
6. WHEN a frontend developer checks job progress via GET /jobs/{job_id}/progress, THE mock server SHALL return a 200 OK response with detailed progress metrics including chunk status and image counts

### Requirement 2: Validation Endpoints

**User Story:** As a frontend developer, I want complete mock endpoints for image validation operations, so that I can develop and test the validation workflow features without running the backend.

#### Acceptance Criteria

1. WHEN a frontend developer analyzes a single image via POST /validation/analyze/, THE mock server SHALL return a 200 OK response with validation results including is_valid, is_duplicate, dimensions, and format
2. WHEN a frontend developer creates a batch validation via POST /validation/batch/, THE mock server SHALL return a 201 Created response with batch_id and processing status
3. WHEN a frontend developer validates job images via POST /validation/job/{job_id}/, THE mock server SHALL return a 200 OK response with task_ids array and images count
4. WHEN a frontend developer retrieves validation results via GET /validation/results/{job_id}/, THE mock server SHALL return a 200 OK response with aggregated validation statistics
5. WHEN a frontend developer requests dataset validation stats via GET /validation/stats/{dataset_id}/, THE mock server SHALL return a 200 OK response with comprehensive validation coverage metrics
6. WHEN a frontend developer updates validation level via PUT /validation/level/, THE mock server SHALL return a 200 OK response confirming the level change

### Requirement 3: Credits and Billing Endpoints

**User Story:** As a frontend developer, I want complete mock endpoints for credits and billing operations, so that I can develop and test the payment and usage tracking features without running the backend.

#### Acceptance Criteria

1. WHEN a frontend developer requests credit balance via GET /credits/balance, THE mock server SHALL return a 200 OK response with current_balance, monthly_usage, limits, and auto-refill settings
2. WHEN a frontend developer lists transactions via GET /credits/transactions, THE mock server SHALL return a 200 OK response with paginated transaction history including type, amount, and status
3. WHEN a frontend developer purchases credits via POST /credits/purchase, THE mock server SHALL return a 201 Created response with transaction details and updated balance
4. WHEN a frontend developer requests usage metrics via GET /credits/usage, THE mock server SHALL return a 200 OK response with daily usage breakdown and totals

### Requirement 4: API Keys Management Endpoints

**User Story:** As a frontend developer, I want complete mock endpoints for API key management, so that I can develop and test the programmatic access features without running the backend.

#### Acceptance Criteria

1. WHEN a frontend developer lists API keys via GET /api-keys/, THE mock server SHALL return a 200 OK response with array of API keys including name, prefix, permissions, rate_limit, and usage statistics
2. WHEN a frontend developer creates an API key via POST /api-keys/, THE mock server SHALL return a 201 Created response with the full key value and warning message about secure storage
3. WHEN a frontend developer revokes an API key via DELETE /api-keys/{key_id}, THE mock server SHALL return a 200 OK response with revocation confirmation
4. WHEN a frontend developer requests key usage via GET /api-keys/{key_id}/usage, THE mock server SHALL return a 200 OK response with usage statistics and daily breakdown

### Requirement 5: Storage Management Endpoints

**User Story:** As a frontend developer, I want complete mock endpoints for storage operations, so that I can develop and test the file management and download features without running the backend.

#### Acceptance Criteria

1. WHEN a frontend developer requests storage usage via GET /storage/usage/, THE mock server SHALL return a 200 OK response with total storage, limits, file counts, and tier breakdown
2. WHEN a frontend developer lists storage files via GET /storage/files/, THE mock server SHALL return a 200 OK response with array of files including filename, size, tier, and download URLs
3. WHEN a frontend developer initiates cleanup via POST /storage/cleanup/, THE mock server SHALL return a 200 OK response with deleted file count and freed space amount
4. WHEN a frontend developer generates a presigned URL via GET /storage/presigned-url/, THE mock server SHALL return a 200 OK response with temporary URL and expiration details

### Requirement 6: Activity Logging Endpoints

**User Story:** As a frontend developer, I want complete mock endpoints for activity logs, so that I can develop and test the audit trail and monitoring features without running the backend.

#### Acceptance Criteria

1. WHEN a frontend developer lists activity logs via GET /activity/, THE mock server SHALL return a 200 OK response with paginated activity entries including action, resource_type, resource_id, metadata, and timestamp

### Requirement 7: Health Check Endpoints

**User Story:** As a frontend developer, I want complete mock endpoints for health checks, so that I can develop and test the system monitoring features without running the backend.

#### Acceptance Criteria

1. WHEN a frontend developer requests basic health via GET /health/, THE mock server SHALL return a 200 OK response with status, timestamp, and version
2. WHEN a frontend developer requests detailed health via GET /health/detailed, THE mock server SHALL return a 200 OK response with service-level health status for database, Redis, and Celery workers

### Requirement 8: Mock Data Quality

**User Story:** As a frontend developer, I want realistic and consistent mock data, so that I can accurately test UI components and user workflows.

#### Acceptance Criteria

1. WHEN any mock endpoint returns data, THE response SHALL use realistic values that match production data patterns
2. WHEN any mock endpoint returns timestamps, THE timestamps SHALL use ISO 8601 format
3. WHEN any mock endpoint returns paginated data, THE response SHALL include meta object with total, page, and limit fields
4. WHEN any mock endpoint returns data, THE response SHALL follow the structure {"data": {...}} for single objects or {"data": [...], "meta": {...}} for collections
5. WHEN any mock endpoint is called, THE response SHALL only return success status codes (200, 201) without error cases

### Requirement 9: OpenAPI Specification Completeness

**User Story:** As a frontend developer, I want a complete OpenAPI specification, so that I can use automated tools like Prism to generate mock servers and validate API contracts.

#### Acceptance Criteria

1. WHEN the OpenAPI specification is parsed by Prism, THE specification SHALL contain all 28 missing endpoints with complete path definitions
2. WHEN each endpoint is defined in OpenAPI, THE definition SHALL include request body schemas where applicable
3. WHEN each endpoint is defined in OpenAPI, THE definition SHALL include response schemas with example data
4. WHEN each endpoint is defined in OpenAPI, THE definition SHALL include parameter definitions for path and query parameters
5. WHEN the OpenAPI specification is validated, THE specification SHALL conform to OpenAPI 3.0 standards without errors

### Requirement 10: Postman Collection Organization

**User Story:** As a frontend developer, I want a well-organized Postman collection, so that I can easily find and test specific endpoints during development.

#### Acceptance Criteria

1. WHEN the Postman collection is imported, THE endpoints SHALL be organized into logical groups: Auth, Projects, Datasets, Crawl Jobs, Validation, Credits, API Keys, Storage, Activity, Health, and Notifications
2. WHEN each endpoint is defined in the collection, THE endpoint SHALL include example request bodies where applicable
3. WHEN each endpoint is defined in the collection, THE endpoint SHALL include at least one success response example
4. WHEN each endpoint uses URLs, THE URLs SHALL use the {{baseUrl}} variable for environment flexibility
5. WHEN each endpoint includes headers, THE headers SHALL include appropriate Content-Type values

### Requirement 11: Testing and Validation

**User Story:** As a frontend developer, I want verified mock endpoints, so that I can trust the mock server to accurately represent the backend API.

#### Acceptance Criteria

1. WHEN the Prism mock server is started with the OpenAPI specification, THE server SHALL start without errors
2. WHEN each endpoint is tested via curl or Postman, THE endpoint SHALL return the expected mock response
3. WHEN the mock server is running, THE server SHALL be accessible at http://localhost:4010
4. WHEN all endpoints are tested, THE test results SHALL be documented in the README.md file
5. WHEN the implementation is complete, THE README.md SHALL include usage examples for each endpoint group

### Requirement 12: Documentation Updates

**User Story:** As a frontend developer, I want updated documentation, so that I can quickly understand how to use the mock server and what endpoints are available.

#### Acceptance Criteria

1. WHEN the README.md is updated, THE document SHALL list all new endpoint groups with endpoint counts
2. WHEN the README.md is updated, THE document SHALL include curl examples for testing key endpoints
3. WHEN the README.md is updated, THE document SHALL include instructions for starting the Prism mock server
4. WHEN the README.md is updated, THE document SHALL include troubleshooting tips for common issues
5. WHEN the README.md is updated, THE document SHALL include a section on the difference between mock and production responses
