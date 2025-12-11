# PixCrawler API Testing with Newman

This directory contains Postman collections and Newman test results for the PixCrawler API.

## Quick Start

### 1. Generate Test Token

```powershell
uv run python ../scripts/get_test_token.py
```

This creates a test user and generates a valid JWT token saved to `bearer_token.txt`.

### 2. Enhance Postman Collection

```powershell
cd postman
uv run python ../scripts/enhance_postman_collection.py
```

This adds bearer token authentication and creates the environment file.

### 3. Run Newman Tests

```powershell
npx newman run postman_collection_enhanced.json -e postman_environment.json --reporters cli
```

### 4. Analyze Results

```powershell
uv run python ../scripts/analyze_newman_results.py
```

## Files

### Collections
- `postman_collection.json` - Original OpenAPI-generated collection
- `postman_collection_enhanced.json` - Enhanced with auth and variables
- `openapi.json` - OpenAPI specification

### Environment
- `postman_environment.json` - Environment variables (baseUrl, bearerToken)

### Results
- `newman-results.json` - Latest test results in JSON format
- `newman-results-final.json` - Final test results after fixes

### Documentation
- `TEST_REPORT.md` - Detailed test report with all failures
- `TESTING_SUMMARY.md` - Executive summary and recommendations
- `README.md` - This file

## Test Results Summary

**Total Endpoints**: 81  
**Passed**: 76 (93.8%)  
**Failed**: 5 (6.2%)

### Passing Tests ✅

- Authentication (login, signup, logout, refresh, verify)
- User management (list, get, update, delete)
- Project operations (list, get, update, delete, export)
- Dataset operations (list, get, update, delete, download)
- Job operations (list, get, update, cancel, pause, resume)
- Image operations (list, get, update, delete, bulk)
- Storage operations (upload, download, delete, list)
- Validation operations
- Metrics operations
- Policy operations

### Failing Tests ❌

1. **`POST /api/v1/projects/`** - Server crash
2. **`GET /api/v1/datasets/?page=1&size=50`** - Timeout
3. **`GET /api/v1/datasets/{id}/status`** - 500 error
4. **`GET /api/v1/jobs/{id}`** - 500 error
5. **`POST /api/v1/batch/projects/batch-delete`** - Validation error

## Scripts

### `../scripts/get_test_token.py`
Creates test user and generates JWT token.

**Usage**:
```powershell
uv run python ../scripts/get_test_token.py
```

**Output**: `bearer_token.txt`

### `../scripts/enhance_postman_collection.py`
Enhances Postman collection with authentication.

**Usage**:
```powershell
uv run python ../scripts/enhance_postman_collection.py
```

**Output**: 
- `postman_collection_enhanced.json`
- `postman_environment.json`

### `../scripts/analyze_newman_results.py`
Analyzes Newman test results.

**Usage**:
```powershell
uv run python ../scripts/analyze_newman_results.py
```

**Input**: `newman-results.json`

### `../scripts/fix_api_issues.py`
Fixes common API issues (user profiles, credits).

**Usage**:
```powershell
uv run python ../scripts/fix_api_issues.py
```

### `../scripts/test_failing_endpoints.py`
Tests individual failing endpoints for debugging.

**Usage**:
```powershell
uv run python ../scripts/test_failing_endpoints.py
```

## Common Issues

### Double `/api/v1` Prefix

**Problem**: URLs had `/api/v1/api/v1/...`

**Fix**: Changed `baseUrl` to `http://localhost:8000` (without `/api/v1`)

### Missing Bearer Token

**Problem**: 401 Unauthorized errors

**Fix**: Run `get_test_token.py` and update environment file

### User Profile Not Found

**Problem**: 500 errors on user-dependent endpoints

**Fix**: Run `fix_api_issues.py` to ensure profile exists

## Newman Commands

### Basic Test Run
```powershell
npx newman run postman_collection_enhanced.json -e postman_environment.json
```

### With CLI Reporter
```powershell
npx newman run postman_collection_enhanced.json -e postman_environment.json --reporters cli --color on
```

### With JSON Export
```powershell
npx newman run postman_collection_enhanced.json -e postman_environment.json --reporters json --reporter-json-export newman-results.json
```

### With Timeout
```powershell
npx newman run postman_collection_enhanced.json -e postman_environment.json --timeout-request 10000
```

### Stop on First Failure
```powershell
npx newman run postman_collection_enhanced.json -e postman_environment.json --bail
```

## Troubleshooting

### Server Not Running

**Error**: `ECONNREFUSED`

**Fix**: Start the backend server:
```powershell
uv run uvicorn backend.main:app --reload
```

### Invalid Token

**Error**: `401 Unauthorized`

**Fix**: Generate new token:
```powershell
uv run python ../scripts/get_test_token.py
```

### Timeout Errors

**Error**: `ETIMEDOUT`

**Fix**: Increase timeout:
```powershell
npx newman run ... --timeout-request 30000
```

### Server Crashes

**Error**: `Connection aborted`

**Fix**: Check backend logs and restart server

## Next Steps

1. Fix the 5 failing endpoints (see `TESTING_SUMMARY.md`)
2. Add pre-request scripts for test data generation
3. Add test assertions to verify responses
4. Create integration test suite
5. Add load testing for critical endpoints

## References

- [Newman Documentation](https://learning.postman.com/docs/running-collections/using-newman-cli/command-line-integration-with-newman/)
- [Postman Collection Format](https://schema.postman.com/)
- [OpenAPI Specification](https://swagger.io/specification/)

---

**Last Updated**: 2025-12-10  
**Test User**: test@pixcrawler.dev  
**Backend URL**: http://localhost:8000
