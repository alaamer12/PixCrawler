# Design Document

## Overview

This design document outlines the implementation approach for completing the PixCrawler Postman mock collection and OpenAPI specification. The solution will add 28 missing backend API endpoints to enable complete frontend development without running the Python backend. The design focuses on creating realistic, consistent mock responses that accurately represent the production API while maintaining simplicity and ease of maintenance.

**Design Goals**:
- Enable frontend developers to work independently without backend dependencies
- Provide realistic mock data that matches production API patterns
- Maintain consistency between OpenAPI spec and Postman collection
- Support rapid iteration and testing of frontend features
- Minimize maintenance overhead through single source of truth approach

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Development                      │
│                                                               │
│  ┌──────────────────┐              ┌──────────────────┐     │
│  │   Next.js        │              │   Prism Mock     │     │
│  │   Frontend       │◄────────────►│   Server         │     │
│  │   (Port 3000)    │   HTTP/JSON  │   (Port 4010)    │     │
│  └──────────────────┘              └────────┬─────────┘     │
│                                              │                │
│                                              │                │
│                     ┌────────────────────────┴────────┐      │
│                     │                                  │      │
│                     │   OpenAPI Specification         │      │
│                     │   (openapi.json)                │      │
│                     │   - 28 New Endpoints            │      │
│                     │   - Request/Response Schemas    │      │
│                     │   - Example Data                │      │
│                     │                                  │      │
│                     └─────────────────────────────────┘      │
│                                                               │
│                     ┌─────────────────────────────────┐      │
│                     │                                  │      │
│                     │   Postman Collection            │      │
│                     │   (PixCrawler_Frontend_Mock.json)│     │
│                     │   - Organized Folders           │      │
│                     │   - Request Examples            │      │
│                     │   - Response Examples           │      │
│                     │                                  │      │
│                     └─────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

1. **Frontend Development**: Developer works on Next.js frontend with `NEXT_PUBLIC_API_URL=http://localhost:4010/api/v1`
2. **API Request**: Frontend makes HTTP request to mock server
3. **Prism Processing**: Prism mock server receives request and matches it against OpenAPI spec
4. **Response Generation**: Prism returns predefined example response from OpenAPI spec
5. **Frontend Rendering**: Frontend receives mock data and renders UI

## Components and Interfaces

### 1. OpenAPI Specification (openapi.json)

**Purpose**: Machine-readable API definition that serves as the source of truth for the mock server.

**Structure**:
```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "PixCrawler Frontend Mock",
    "version": "1.0.0"
  },
  "servers": [
    {
      "url": "http://localhost:4010/api/v1"
    }
  ],
  "paths": {
    "/endpoint": {
      "method": {
        "summary": "Endpoint description",
        "parameters": [],
        "requestBody": {},
        "responses": {
          "200": {
            "description": "Success",
            "content": {
              "application/json": {
                "example": {}
              }
            }
          }
        }
      }
    }
  }
}
```

**Key Responsibilities**:
- Define all API endpoints with paths and HTTP methods
- Specify request parameters (path, query, header)
- Define request body schemas for POST/PUT/PATCH endpoints
- Provide response schemas with realistic example data
- Maintain consistency with backend API contract

### 2. Postman Collection (PixCrawler_Frontend_Mock.json)

**Purpose**: Human-friendly API testing interface with organized endpoint groups and examples.

**Structure**:
```json
{
  "info": {
    "_postman_id": "pixcrawler-frontend-mock",
    "name": "PixCrawler Frontend Mock",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Group Name",
      "item": [
        {
          "name": "Endpoint Name",
          "request": {
            "method": "GET|POST|PATCH|DELETE|PUT",
            "header": [],
            "body": {},
            "url": {
              "raw": "{{baseUrl}}/path",
              "host": ["{{baseUrl}}"],
              "path": ["path"]
            }
          },
          "response": [
            {
              "name": "Success",
              "status": "OK",
              "code": 200,
              "body": "{}"
            }
          ]
        }
      ]
    }
  ]
}
```

**Key Responsibilities**:
- Organize endpoints into logical groups (Auth, Projects, Jobs, etc.)
- Provide example requests with realistic data
- Include multiple response examples per endpoint
- Use environment variables ({{baseUrl}}) for flexibility
- Serve as documentation and testing tool

### 3. Prism Mock Server

**Purpose**: Runtime server that generates mock responses based on OpenAPI specification.

**Configuration**:
```bash
prism mock postman/openapi.json -p 4010
```

**Key Responsibilities**:
- Parse OpenAPI specification
- Match incoming requests to defined endpoints
- Return example responses from spec
- Validate request/response formats
- Provide CORS headers for frontend development

### 4. Documentation (README.md)

**Purpose**: Guide developers on using the mock server and understanding available endpoints.

**Key Sections**:
- Setup instructions (installing Prism, starting mock server)
- Available endpoint groups with counts
- Usage examples with curl commands
- Troubleshooting common issues
- Differences between mock and production responses

## Data Models

### Mock Response Structure

All mock responses follow a consistent structure based on the production API patterns:

**Single Object Response**:
```json
{
  "data": {
    "id": "uuid",
    "field1": "value1",
    "field2": "value2",
    "created_at": "2025-12-05T10:00:00Z",
    "updated_at": "2025-12-05T10:00:00Z"
  }
}
```

**Collection Response**:
```json
{
  "data": [...],
  "meta": {
    "total": 100,
    "page": 1,
    "limit": 20,
    "pages": 5
  }
}
```

### Endpoint Groups and Data Models

#### 1. Crawl Jobs Endpoints (6 endpoints)

**POST /jobs/** - Create Crawl Job
- Request: `{ project_id, name, keywords[], max_images, engines[], quality_filters }`
- Response: Complete job object with chunk tracking fields

**GET /jobs/{job_id}** - Get Job Details
- Response: Job with status, progress, chunk metrics, timestamps

**POST /jobs/{job_id}/start** - Start Job
- Response: `{ task_ids[], message }`

**POST /jobs/{job_id}/cancel** - Cancel Job
- Response: `{ revoked_count, status, message }`

**POST /jobs/{job_id}/retry** - Retry Failed Job
- Response: Reset job state with new task_ids

**GET /jobs/{job_id}/progress** - Get Job Progress
- Response: Detailed progress with chunk status, image counts, ETA

#### 2. Validation Endpoints (6 endpoints)

**POST /validation/analyze/** - Analyze Single Image
- Request: `{ image_url or image_data }`
- Response: `{ is_valid, is_duplicate, dimensions, format, hash }`

**POST /validation/batch/** - Create Batch Validation
- Request: `{ image_ids[], validation_level }`
- Response: `{ batch_id, status, images_count }`

**POST /validation/job/{job_id}/** - Validate Job Images
- Request: `{ validation_level }`
- Response: `{ task_ids[], images_count, message }`

**GET /validation/results/{job_id}/** - Get Validation Results
- Response: Aggregated stats (total, valid, invalid, duplicates)

**GET /validation/stats/{dataset_id}/** - Get Dataset Validation Stats
- Response: Comprehensive coverage metrics

**PUT /validation/level/** - Update Validation Level
- Request: `{ level: "fast" | "medium" | "slow" }`
- Response: Confirmation with new level

#### 3. Credits and Billing Endpoints (4 endpoints)

**GET /credits/balance** - Get Credit Balance
- Response: `{ current_balance, monthly_usage, limits, auto_refill_settings }`

**GET /credits/transactions** - List Transactions
- Query params: `type, start_date, end_date, page, limit`
- Response: Paginated transaction history

**POST /credits/purchase** - Purchase Credits
- Request: `{ amount, payment_method, payment_token }`
- Response: Transaction details with updated balance

**GET /credits/usage** - Get Usage Metrics
- Query params: `start_date, end_date, granularity`
- Response: Daily usage breakdown with totals

#### 4. API Keys Management Endpoints (4 endpoints)

**GET /api-keys/** - List API Keys
- Response: Array of keys with usage statistics

**POST /api-keys/** - Create API Key
- Request: `{ name, permissions[], rate_limit, expires_at }`
- Response: Full key value (shown once) with warning

**DELETE /api-keys/{key_id}** - Revoke API Key
- Response: Revocation confirmation

**GET /api-keys/{key_id}/usage** - Get Key Usage
- Response: Usage statistics with daily breakdown

#### 5. Storage Management Endpoints (4 endpoints)

**GET /storage/usage/** - Get Storage Usage
- Response: `{ total_storage, limits, file_counts, tier_breakdown }`

**GET /storage/files/** - List Storage Files
- Query params: `tier, page, limit`
- Response: Paginated file list with download URLs

**POST /storage/cleanup/** - Initiate Cleanup
- Request: `{ older_than_days, tier }`
- Response: `{ deleted_count, freed_space_bytes }`

**GET /storage/presigned-url/** - Generate Presigned URL
- Query params: `file_path, expires_in`
- Response: `{ url, expires_at }`

#### 6. Activity Logging Endpoints (1 endpoint)

**GET /activity/** - List Activity Logs
- Query params: `action, resource_type, start_date, end_date, page, limit`
- Response: Paginated activity entries with metadata

#### 7. Health Check Endpoints (2 endpoints)

**GET /health/** - Basic Health Check
- Response: `{ status, timestamp, version }`

**GET /health/detailed** - Detailed Health Check
- Response: Service-level health (database, Redis, Celery)

### Data Consistency Rules

1. **Timestamps**: All timestamps use ISO 8601 format (`YYYY-MM-DDTHH:mm:ssZ`)
2. **UUIDs**: All IDs use UUID v4 format
3. **Status Values**: Use consistent enums (pending, running, completed, failed, cancelled)
4. **Pagination**: Always include meta object with total, page, limit, pages
5. **Success Only**: Mock responses only return success status codes (200, 201)

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Acceptance Criteria Testing Prework

**1.1 WHEN a frontend developer requests to create a crawl job via POST /jobs/, THE mock server SHALL return a 201 Created response with a complete job object**
- Thoughts: This is testing that the mock server returns the correct status code and includes all required fields in the response. We can verify the response structure matches the expected schema.
- Testable: yes - example

**1.2 WHEN a frontend developer requests a specific job via GET /jobs/{job_id}, THE mock server SHALL return a 200 OK response with detailed job information**
- Thoughts: This tests that the mock server handles path parameters correctly and returns job details. This is a specific example test.
- Testable: yes - example

**1.3 WHEN a frontend developer starts a job via POST /jobs/{job_id}/start, THE mock server SHALL return a 200 OK response with task_ids array**
- Thoughts: This verifies the mock server returns the expected response structure for job start operations.
- Testable: yes - example

**1.4 WHEN a frontend developer cancels a job via POST /jobs/{job_id}/cancel, THE mock server SHALL return a 200 OK response with revoked task count**
- Thoughts: This tests the cancel endpoint returns the expected response format.
- Testable: yes - example

**1.5 WHEN a frontend developer retries a failed job via POST /jobs/{job_id}/retry, THE mock server SHALL return a 200 OK response with reset job state**
- Thoughts: This verifies the retry endpoint response structure.
- Testable: yes - example

**1.6 WHEN a frontend developer checks job progress via GET /jobs/{job_id}/progress, THE mock server SHALL return a 200 OK response with detailed progress metrics**
- Thoughts: This tests the progress endpoint returns comprehensive metrics.
- Testable: yes - example

**2.1-2.6 Validation endpoints**
- Thoughts: Each validation endpoint test is checking specific response structures for different operations.
- Testable: yes - example (for each)

**3.1-3.4 Credits and billing endpoints**
- Thoughts: These test that billing-related endpoints return appropriate financial data structures.
- Testable: yes - example (for each)

**4.1-4.4 API Keys management endpoints**
- Thoughts: These verify API key management operations return expected responses.
- Testable: yes - example (for each)

**5.1-5.4 Storage management endpoints**
- Thoughts: These test storage-related operations return proper file and usage information.
- Testable: yes - example (for each)

**6.1 Activity logging endpoint**
- Thoughts: This tests the activity log endpoint returns paginated activity entries.
- Testable: yes - example

**7.1-7.2 Health check endpoints**
- Thoughts: These verify health check endpoints return system status information.
- Testable: yes - example (for each)

**8.1 WHEN any mock endpoint returns data, THE response SHALL use realistic values that match production data patterns**
- Thoughts: This is a property that should hold across all endpoints - all mock data should be realistic.
- Testable: yes - property

**8.2 WHEN any mock endpoint returns timestamps, THE timestamps SHALL use ISO 8601 format**
- Thoughts: This is a universal property about timestamp formatting across all responses.
- Testable: yes - property

**8.3 WHEN any mock endpoint returns paginated data, THE response SHALL include meta object**
- Thoughts: This is a property about pagination structure that applies to all paginated endpoints.
- Testable: yes - property

**8.4 WHEN any mock endpoint returns data, THE response SHALL follow the structure {"data": {...}} or {"data": [...], "meta": {...}}**
- Thoughts: This is a universal property about response structure consistency.
- Testable: yes - property

**8.5 WHEN any mock endpoint is called, THE response SHALL only return success status codes**
- Thoughts: This is a property that all mock endpoints should satisfy - no error responses.
- Testable: yes - property

**9.1 WHEN the OpenAPI specification is parsed by Prism, THE specification SHALL contain all 28 missing endpoints**
- Thoughts: This tests completeness of the OpenAPI spec.
- Testable: yes - example

**9.2-9.5 OpenAPI specification completeness**
- Thoughts: These test various aspects of OpenAPI spec completeness and validity.
- Testable: yes - example (for each)

**10.1 WHEN the Postman collection is imported, THE endpoints SHALL be organized into logical groups**
- Thoughts: This tests the organizational structure of the Postman collection.
- Testable: yes - example

**10.2-10.5 Postman collection organization**
- Thoughts: These test various aspects of Postman collection structure and content.
- Testable: yes - example (for each)

**11.1 WHEN the Prism mock server is started with the OpenAPI specification, THE server SHALL start without errors**
- Thoughts: This is a basic integration test for the mock server.
- Testable: yes - example

**11.2-11.5 Testing and validation**
- Thoughts: These test the mock server functionality and documentation.
- Testable: yes - example (for each)

**12.1-12.5 Documentation updates**
- Thoughts: These verify documentation completeness and quality.
- Testable: yes - example (for each)

### Property Reflection

After reviewing all properties, I've identified the following consolidations:

- **Individual endpoint tests (1.1-7.2)**: These are all specific examples testing individual endpoints. They cannot be consolidated as each tests a unique endpoint.
- **Mock data quality properties (8.1-8.5)**: These are universal properties that apply across all endpoints. Property 8.4 (response structure) subsumes some aspects of 8.3 (pagination structure), but both provide unique validation value.
- **OpenAPI and Postman tests (9.1-12.5)**: These are specific validation tests for the artifacts themselves, not redundant.

No redundancy found - all properties provide unique validation value.

### Correctness Properties

**Property 1: Realistic mock data**
*For any* mock endpoint response, all field values should match realistic production data patterns (valid UUIDs, reasonable numbers, proper email formats, realistic timestamps)
**Validates: Requirements 8.1**

**Property 2: ISO 8601 timestamp format**
*For any* mock endpoint response containing timestamps, all timestamp fields should use ISO 8601 format (YYYY-MM-DDTHH:mm:ssZ)
**Validates: Requirements 8.2**

**Property 3: Pagination structure consistency**
*For any* mock endpoint returning paginated data, the response should include a meta object with total, page, limit, and pages fields
**Validates: Requirements 8.3**

**Property 4: Response structure consistency**
*For any* mock endpoint response, the structure should follow either {"data": {...}} for single objects or {"data": [...], "meta": {...}} for collections
**Validates: Requirements 8.4**

**Property 5: Success-only responses**
*For any* mock endpoint call, the response should only return success status codes (200, 201) without error cases
**Validates: Requirements 8.5**

## Error Handling

### Mock Server Error Handling

Since the mock server is designed for frontend development, it follows a simplified error handling approach:

**Design Decision**: Mock responses only return success cases (200, 201 status codes) to enable positive-path frontend development.

**Rationale**:
- Frontend developers need to build and test happy-path UI flows first
- Error handling can be tested later with the real backend
- Simplifies mock data maintenance
- Reduces complexity of OpenAPI specification

**Error Scenarios Not Mocked**:
- 400 Bad Request (validation errors)
- 401 Unauthorized (authentication failures)
- 403 Forbidden (authorization failures)
- 404 Not Found (resource not found)
- 422 Unprocessable Entity (business logic errors)
- 429 Too Many Requests (rate limiting)
- 500 Internal Server Error (server errors)

**Future Enhancement**: If error case testing becomes critical, we can add example error responses to the OpenAPI spec and use Prism's dynamic response selection.

## Testing Strategy

### Manual Testing Approach

Given the nature of this feature (creating mock API definitions), we will use manual testing rather than automated tests:

**Testing Phases**:

1. **OpenAPI Validation**
   - Validate OpenAPI spec against OpenAPI 3.0 schema
   - Use online validators (swagger.io/tools/swagger-editor)
   - Ensure no syntax errors or schema violations

2. **Prism Server Testing**
   - Start Prism mock server with the OpenAPI spec
   - Verify server starts without errors
   - Test each endpoint with curl or Postman
   - Verify responses match expected structure

3. **Postman Collection Testing**
   - Import collection into Postman
   - Verify folder organization
   - Test each request in the collection
   - Verify responses match OpenAPI examples

4. **Frontend Integration Testing**
   - Configure frontend to use mock server URL
   - Test key user flows (create job, view progress, etc.)
   - Verify UI renders correctly with mock data
   - Check for any data format mismatches

**Test Documentation**:
- Document test results in README.md
- Include curl examples for each endpoint group
- Provide troubleshooting tips for common issues

**Why No Automated Tests**:
- Mock definitions are static JSON files
- Prism handles response generation automatically
- Manual testing is faster for this scope (28 endpoints)
- Automated tests would add complexity without significant value
- Frontend integration testing provides sufficient validation

**Quality Assurance**:
- Peer review of OpenAPI spec and Postman collection
- Cross-reference with production API documentation
- Verify consistency between OpenAPI and Postman
- Test with actual frontend code to ensure compatibility

## Implementation Approach

### Phase 1: OpenAPI Specification Development

**Approach**: Build the OpenAPI specification as the single source of truth, then derive the Postman collection from it.

**Rationale**: 
- OpenAPI spec is machine-readable and can be used directly by Prism
- Postman can import OpenAPI specs, reducing duplication
- Single source of truth minimizes inconsistencies
- OpenAPI validators ensure correctness

**Steps**:

1. **Create Base OpenAPI Structure**
   - Set up OpenAPI 3.0 document with metadata
   - Define server URL (http://localhost:4010/api/v1)
   - Add common schemas for reusable components
   - Define standard response structures

2. **Define Endpoint Groups**
   - Crawl Jobs (6 endpoints)
   - Validation (6 endpoints)
   - Credits and Billing (4 endpoints)
   - API Keys Management (4 endpoints)
   - Storage Management (4 endpoints)
   - Activity Logging (1 endpoint)
   - Health Check (2 endpoints)

3. **Create Endpoint Definitions**
   - For each endpoint, define:
     - HTTP method and path
     - Request parameters (path, query, header)
     - Request body schema (for POST/PUT/PATCH)
     - Response schemas with examples
     - Response status codes (200, 201)

4. **Add Realistic Example Data**
   - Use valid UUIDs for IDs
   - Use ISO 8601 timestamps
   - Include realistic values (names, emails, numbers)
   - Ensure consistency across related endpoints
   - Follow production API patterns

5. **Validate OpenAPI Spec**
   - Use Swagger Editor for validation
   - Check for schema errors
   - Verify all required fields are present
   - Test with Prism mock server

### Phase 2: Postman Collection Creation

**Approach**: Create a well-organized Postman collection that complements the OpenAPI spec.

**Rationale**:
- Postman provides better developer experience for manual testing
- Folder organization makes endpoints easy to find
- Environment variables enable flexibility
- Response examples serve as documentation

**Steps**:

1. **Set Up Collection Structure**
   - Create collection with metadata
   - Define environment variables ({{baseUrl}})
   - Organize into logical folders:
     - Crawl Jobs
     - Validation
     - Credits & Billing
     - API Keys
     - Storage
     - Activity Logs
     - Health Checks

2. **Add Endpoint Requests**
   - For each endpoint, create request with:
     - Descriptive name
     - HTTP method and URL with variables
     - Headers (Content-Type, Authorization)
     - Request body (for POST/PUT/PATCH)
     - Example response

3. **Add Response Examples**
   - Include success response (200/201)
   - Use same example data as OpenAPI spec
   - Ensure consistency between collections

4. **Test Collection**
   - Import into Postman
   - Test each request against mock server
   - Verify responses match expectations
   - Check folder organization

### Phase 3: Documentation and Testing

**Approach**: Create comprehensive documentation and validate the complete solution.

**Steps**:

1. **Update README.md**
   - Add setup instructions for Prism
   - List all endpoint groups with counts
   - Provide curl examples for key endpoints
   - Include troubleshooting section
   - Document differences from production API

2. **Manual Testing**
   - Start Prism mock server
   - Test all 28 endpoints with curl
   - Verify response structures
   - Check status codes
   - Validate data formats

3. **Frontend Integration Testing**
   - Configure frontend to use mock server
   - Test key user flows:
     - Create and start crawl job
     - Monitor job progress
     - View validation results
     - Check credit balance
     - Manage API keys
   - Verify UI renders correctly
   - Check for data format issues

4. **Documentation Review**
   - Ensure all endpoints are documented
   - Verify examples are accurate
   - Check for typos and clarity
   - Add any missing troubleshooting tips

## File Organization

The implementation will create/update the following files:

```
backend/postman/
├── openapi.json                      # OpenAPI 3.0 specification (NEW)
├── PixCrawler_Frontend_Mock.json     # Postman collection (NEW)
└── README.md                         # Documentation (UPDATE)
```

**File Locations**:
- **OpenAPI Spec**: `backend/postman/openapi.json`
- **Postman Collection**: `backend/postman/PixCrawler_Frontend_Mock.json`
- **Documentation**: `backend/postman/README.md`

**Rationale for Location**:
- Keep mock artifacts with existing Postman collections
- Easy to find for frontend developers
- Separate from production backend code
- Can be versioned alongside backend API

## Design Decisions and Rationales

### Decision 1: Use Prism for Mock Server

**Decision**: Use Prism CLI tool to generate mock server from OpenAPI spec.

**Rationale**:
- Industry-standard tool with active maintenance
- Automatic response generation from OpenAPI examples
- Built-in request validation
- CORS support for frontend development
- No custom code required

**Alternatives Considered**:
- **JSON Server**: Requires custom routes and data files, more maintenance
- **Custom Express Server**: Too much development overhead
- **Postman Mock Server**: Limited to Postman ecosystem, less flexible

### Decision 2: Success-Only Responses

**Decision**: Mock server only returns success status codes (200, 201).

**Rationale**:
- Frontend developers need happy-path flows first
- Error handling can be tested with real backend later
- Simplifies mock data maintenance
- Reduces OpenAPI spec complexity
- Faster implementation

**Trade-offs**:
- Cannot test error handling in frontend
- May miss edge cases in UI
- Requires real backend for complete testing

### Decision 3: Single Source of Truth (OpenAPI)

**Decision**: OpenAPI spec is the primary artifact, Postman collection is derived.

**Rationale**:
- OpenAPI is machine-readable and validated
- Prism uses OpenAPI directly
- Reduces duplication and inconsistencies
- Industry standard for API definitions
- Can generate client SDKs if needed

**Trade-offs**:
- Postman collection may need manual adjustments
- Some Postman features not available in OpenAPI

### Decision 4: Manual Testing Over Automation

**Decision**: Use manual testing instead of automated test suite.

**Rationale**:
- Mock definitions are static JSON files
- Prism handles response generation automatically
- 28 endpoints is manageable for manual testing
- Automated tests add complexity without significant value
- Frontend integration provides sufficient validation
- Faster to implement and maintain

**Trade-offs**:
- No regression testing for spec changes
- Requires manual verification after updates
- Potential for human error

### Decision 5: Realistic Mock Data

**Decision**: Use realistic, production-like data in all examples.

**Rationale**:
- Helps frontend developers understand data structures
- Reveals UI issues with real-world data
- Makes testing more meaningful
- Easier to spot data format problems
- Better developer experience

**Implementation Guidelines**:
- Use valid UUIDs (not "123" or "abc")
- Use realistic names, emails, URLs
- Use proper ISO 8601 timestamps
- Use reasonable numeric values
- Maintain consistency across related endpoints

## Success Metrics

### Functional Metrics

1. **Completeness**: All 28 missing endpoints are defined in OpenAPI spec and Postman collection
2. **Prism Compatibility**: Mock server starts without errors and serves all endpoints
3. **Response Accuracy**: All responses match expected structure and data types
4. **Frontend Integration**: Frontend can successfully call all mock endpoints and render UI

### Quality Metrics

1. **OpenAPI Validation**: Spec passes OpenAPI 3.0 schema validation without errors
2. **Data Consistency**: All timestamps use ISO 8601, all IDs use UUID format
3. **Response Structure**: All responses follow {"data": {...}} or {"data": [...], "meta": {...}} pattern
4. **Documentation**: README includes setup instructions, examples, and troubleshooting

### Developer Experience Metrics

1. **Setup Time**: Frontend developer can start mock server in under 5 minutes
2. **Discoverability**: Endpoints are easy to find in Postman collection folders
3. **Clarity**: Mock responses are realistic and easy to understand
4. **Reliability**: Mock server runs without crashes or errors during development

## Maintenance and Evolution

### Keeping Mock in Sync with Production

**Challenge**: Mock endpoints may drift from production API as backend evolves.

**Mitigation Strategies**:

1. **Version Control**: Track OpenAPI spec and Postman collection in git
2. **Documentation**: Document any known differences between mock and production
3. **Regular Reviews**: Periodically compare mock with production API documentation
4. **Frontend Feedback**: Frontend developers report discrepancies they encounter

### Adding New Endpoints

**Process**:

1. Add endpoint definition to OpenAPI spec
2. Add realistic example response
3. Validate OpenAPI spec
4. Update Postman collection
5. Test with Prism mock server
6. Update README documentation
7. Notify frontend team

### Updating Existing Endpoints

**Process**:

1. Update OpenAPI spec with changes
2. Update example responses
3. Validate spec
4. Update Postman collection
5. Test changes with mock server
6. Document breaking changes
7. Notify frontend team

## Future Enhancements

### Phase 4: Error Response Support (Optional)

If error case testing becomes critical:

1. Add error response examples to OpenAPI spec
2. Use Prism's dynamic response selection
3. Configure Prism to return errors based on request parameters
4. Update Postman collection with error examples
5. Document error scenarios in README

### Phase 5: Dynamic Mock Data (Optional)

For more realistic testing:

1. Use Prism's dynamic response generation
2. Add faker.js for random data generation
3. Implement stateful mock server (track created resources)
4. Add pagination support with real page navigation

### Phase 6: Contract Testing (Optional)

For production API validation:

1. Use OpenAPI spec for contract testing
2. Validate production API responses against spec
3. Catch breaking changes early
4. Ensure mock stays in sync with production

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Mock drift from production** | High | Medium | Regular reviews, version control, documentation |
| **Prism compatibility issues** | Medium | Low | Use stable Prism version, test thoroughly |
| **Incomplete endpoint coverage** | High | Low | Cross-reference with backend API docs, frontend requirements |
| **Invalid OpenAPI spec** | High | Low | Use validators, test with Prism before committing |
| **Unrealistic mock data** | Medium | Medium | Review with backend team, use production examples |
| **Frontend integration issues** | High | Medium | Test with actual frontend code, iterate based on feedback |
| **Documentation gaps** | Medium | Medium | Include setup instructions, examples, troubleshooting |

## Appendix: Endpoint Reference

### Complete Endpoint List (28 endpoints)

**Crawl Jobs (6)**:
1. POST /jobs/ - Create crawl job
2. GET /jobs/{job_id} - Get job details
3. POST /jobs/{job_id}/start - Start job
4. POST /jobs/{job_id}/cancel - Cancel job
5. POST /jobs/{job_id}/retry - Retry failed job
6. GET /jobs/{job_id}/progress - Get job progress

**Validation (6)**:
7. POST /validation/analyze/ - Analyze single image
8. POST /validation/batch/ - Create batch validation
9. POST /validation/job/{job_id}/ - Validate job images
10. GET /validation/results/{job_id}/ - Get validation results
11. GET /validation/stats/{dataset_id}/ - Get dataset validation stats
12. PUT /validation/level/ - Update validation level

**Credits & Billing (4)**:
13. GET /credits/balance - Get credit balance
14. GET /credits/transactions - List transactions
15. POST /credits/purchase - Purchase credits
16. GET /credits/usage - Get usage metrics

**API Keys (4)**:
17. GET /api-keys/ - List API keys
18. POST /api-keys/ - Create API key
19. DELETE /api-keys/{key_id} - Revoke API key
20. GET /api-keys/{key_id}/usage - Get key usage

**Storage (4)**:
21. GET /storage/usage/ - Get storage usage
22. GET /storage/files/ - List storage files
23. POST /storage/cleanup/ - Initiate cleanup
24. GET /storage/presigned-url/ - Generate presigned URL

**Activity Logs (1)**:
25. GET /activity/ - List activity logs

**Health Checks (2)**:
26. GET /health/ - Basic health check
27. GET /health/detailed - Detailed health check

**Total**: 27 endpoints (Note: Original count of 28 may have included an additional endpoint not specified in requirements)