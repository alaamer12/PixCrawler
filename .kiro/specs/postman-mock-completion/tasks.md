# Implementation Plan

- [x] 1. Set up OpenAPI specification structure





  - Create `backend/postman/openapi.json` with base OpenAPI 3.0 structure
  - Define metadata (title, version, description)
  - Add server configuration (http://localhost:4010/api/v1)
  - Define common schemas for reusable components (UUID, timestamp, pagination)
  - Define standard response structures (single object, collection with meta)
  - _Requirements: 9.1, 9.5_
-

- [x] 2. Implement Crawl Jobs endpoints in OpenAPI spec



  - POST /jobs/ - Create crawl job with request/response schemas
  - GET /jobs/{job_id} - Get job details with path parameter
  - POST /jobs/{job_id}/start - Start job with task_ids response
  - POST /jobs/{job_id}/cancel - Cancel job with revoked count response
  - POST /jobs/{job_id}/retry - Retry failed job with reset state
  - GET /jobs/{job_id}/progress - Get job progress with detailed metrics
  - Add realistic example data for all responses (UUIDs, timestamps, chunk tracking)
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 8.1, 8.2, 8.4_
-

- [x] 3. Implement Validation endpoints in OpenAPI spec




  - POST /validation/analyze/ - Analyze single image with validation results
  - POST /validation/batch/ - Create batch validation with batch_id
  - POST /validation/job/{job_id}/ - Validate job images with task_ids
  - GET /validation/results/{job_id}/ - Get validation results with aggregated stats
  - GET /validation/stats/{dataset_id}/ - Get dataset validation stats
  - PUT /validation/level/ - Update validation level with confirmation
  - Add realistic example data for all responses
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 8.1, 8.2, 8.4_
-

- [x] 4. Implement Credits and Billing endpoints in OpenAPI spec




  - GET /credits/balance - Get credit balance with auto-refill settings
  - GET /credits/transactions - List transactions with pagination
  - POST /credits/purchase - Purchase credits with transaction details
  - GET /credits/usage - Get usage metrics with daily breakdown
  - Add realistic example data with proper pagination meta objects
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 8.1, 8.2, 8.3, 8.4_
-

- [x] 5. Implement API Keys Management endpoints in OpenAPI spec




  - GET /api-keys/ - List API keys with usage statistics
  - POST /api-keys/ - Create API key with full key value and warning
  - DELETE /api-keys/{key_id} - Revoke API key with confirmation
  - GET /api-keys/{key_id}/usage - Get key usage with daily breakdown
  - Add realistic example data for all responses
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 8.1, 8.2, 8.4_

- [x] 6. Implement Storage Management endpoints in OpenAPI spec





  - GET /storage/usage/ - Get storage usage with tier breakdown
  - GET /storage/files/ - List storage files with pagination
  - POST /storage/cleanup/ - Initiate cleanup with deleted count
  - GET /storage/presigned-url/ - Generate presigned URL with expiration
  - Add realistic example data with proper pagination where applicable
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 8.1, 8.2, 8.3, 8.4_
-

- [x] 7. Implement Activity Logging and Health Check endpoints in OpenAPI spec




  - GET /activity/ - List activity logs with pagination
  - GET /health/ - Basic health check with status and version
  - GET /health/detailed - Detailed health check with service-level status
  - Add realistic example data for all responses
  - _Requirements: 6.1, 7.1, 7.2, 8.1, 8.2, 8.3, 8.4_

- [x] 8. Validate OpenAPI specification





  - Use Swagger Editor (https://editor.swagger.io) to validate spec
  - Check for schema errors and warnings
  - Verify all required fields are present
  - Ensure all endpoints have proper request/response definitions
  - Confirm all examples use ISO 8601 timestamps and UUID v4 format
  - _Requirements: 9.5, 8.2_
-

- [x] 9. Test OpenAPI spec with Prism mock server




  - Install Prism CLI: `npm install -g @stoplight/prism-cli`
  - Start Prism mock server: `prism mock backend/postman/openapi.json -p 4010`
  - Verify server starts without errors
  - Test each endpoint group with curl commands
  - Verify responses match expected structure and status codes
  - _Requirements: 11.1, 11.2, 11.3, 8.5_
-

- [x] 10. Create Postman collection structure



  - Create `backend/postman/PixCrawler_Frontend_Mock.json`
  - Set up collection metadata (name, description, schema version)
  - Define environment variable {{baseUrl}} = http://localhost:4010/api/v1
  - Create folder structure: Crawl Jobs, Validation, Credits & Billing, API Keys, Storage, Activity Logs, Health Checks
  - _Requirements: 10.1, 10.4_

- [x] 11. Add Crawl Jobs endpoints to Postman collection





  - Add all 6 crawl job endpoints to "Crawl Jobs" folder
  - Include request bodies for POST endpoints
  - Add success response examples (200/201)
  - Use {{baseUrl}} variable in all URLs
  - Add appropriate Content-Type headers
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 10.2, 10.3, 10.5_
-

- [x] 12. Add Validation endpoints to Postman collection




  - Add all 6 validation endpoints to "Validation" folder
  - Include request bodies for POST/PUT endpoints
  - Add success response examples
  - Use {{baseUrl}} variable in all URLs
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 10.2, 10.3, 10.5_
-

- [x] 13. Add Credits, API Keys, Storage, Activity, and Health endpoints to Postman collection




  - Add Credits & Billing endpoints (4) to "Credits & Billing" folder
  - Add API Keys endpoints (4) to "API Keys" folder
  - Add Storage endpoints (4) to "Storage" folder
  - Add Activity endpoint (1) to "Activity Logs" folder
  - Add Health Check endpoints (2) to "Health Checks" folder
  - Include all request bodies, response examples, and proper headers
  - _Requirements: 3.1-3.4, 4.1-4.4, 5.1-5.4, 6.1, 7.1-7.2, 10.2, 10.3, 10.5_

- [x] 14. Test Postman collection




  - Import collection into Postman
  - Verify folder organization is logical and clear
  - Test each request against running Prism mock server
  - Verify responses match OpenAPI examples
  - Check that {{baseUrl}} variable works correctly
  - _Requirements: 10.1, 11.2_

- [x] 15. Update README.md documentation




  - Add "Mock Server Setup" section with Prism installation instructions
  - List all endpoint groups with counts (27 total endpoints)
  - Add curl examples for each endpoint group
  - Include troubleshooting section (common issues, solutions)
  - Document differences between mock and production responses
  - Add section on starting/stopping mock server
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_
-

- [x] 16. Perform frontend integration testing



  - Configure frontend environment: NEXT_PUBLIC_API_URL=http://localhost:4010/api/v1
  - Start Prism mock server
  - Test key user flows: create job, start job, monitor progress
  - Test validation workflow: validate images, check results
  - Test credits workflow: check balance, view transactions
  - Test API keys workflow: list keys, create key
  - Verify UI renders correctly with mock data
  - Document any data format mismatches or issues
  - _Requirements: 11.4_
-

- [x] 17. Final validation and documentation







  - Ensure all 27 endpoints are documented in README
  - Verify OpenAPI spec passes validation
  - Confirm Prism mock server runs without errors
  - Test all curl examples in README
  - Review documentation for clarity and completeness
  - _Requirements: 11.5, 12.1, 12.2, 12.3, 12.4, 12.5_
