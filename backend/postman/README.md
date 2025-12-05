# PixCrawler Mock Server Documentation

This directory contains the OpenAPI specification and Postman collection for the PixCrawler Frontend Mock Server. The mock server enables frontend development without requiring the Python backend to be running.

## Table of Contents

- [Overview](#overview)
- [Mock Server Setup](#mock-server-setup)
- [Frontend Integration Testing](#frontend-integration-testing)
- [Available Endpoints](#available-endpoints)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)
- [Mock vs Production Differences](#mock-vs-production-differences)
- [Additional Resources](#additional-resources)

---

## Overview

The PixCrawler mock server provides realistic API responses for frontend development and testing. It uses:

- **OpenAPI 3.0 Specification**: `openapi.json` - Machine-readable API definition
- **Postman Collection**: `PixCrawler_Frontend_Mock.json` - Human-friendly testing interface
- **Prism Mock Server**: Generates mock responses from the OpenAPI spec

### Key Features

- ✅ 27 endpoints covering all major API functionality
- ✅ Realistic mock data with proper UUIDs and timestamps
- ✅ Consistent response structures
- ✅ Success-only responses (200, 201) for positive-path development
- ✅ No backend dependencies required

---

## Mock Server Setup

### Prerequisites

- **Node.js**: Version 18.0.0 or higher
- **npm**: Comes with Node.js

### Installation

Install Prism CLI globally:

```bash
npm install -g @stoplight/prism-cli
```

Verify installation:

```bash
prism --version
```

### Starting the Mock Server

Navigate to the postman directory and start Prism:

```bash
cd backend/postman
prism mock openapi.json -p 4010
```

The mock server will start at `http://localhost:4010/api/v1`

**Expected Output:**
```
[CLI] …  awaiting  Starting Prism…
[CLI] ℹ  info      GET        http://127.0.0.1:4010/api/v1/jobs
[CLI] ℹ  info      POST       http://127.0.0.1:4010/api/v1/jobs
[CLI] ℹ  info      GET        http://127.0.0.1:4010/api/v1/jobs/{job_id}
...
[CLI] ▶  start     Prism is listening on http://127.0.0.1:4010
```

### Stopping the Mock Server

Press `Ctrl+C` in the terminal where Prism is running.

### Alternative: Using npx (No Installation)

Run Prism without installing globally:

```bash
npx @stoplight/prism-cli mock openapi.json -p 4010
```

---

## Frontend Integration Testing

The mock server is designed to work seamlessly with the PixCrawler Next.js frontend for development and testing.

### Quick Setup

Run the automated setup script:

**Linux/macOS**:
```bash
cd backend/postman
./setup-frontend-testing.sh
```

**Windows**:
```cmd
cd backend\postman
setup-frontend-testing.cmd
```

The script will:
1. Check for required tools (Node.js/Bun, Prism)
2. Install Prism if not present
3. Configure frontend environment variables
4. Install frontend dependencies

### Manual Setup

1. **Configure Frontend Environment**

Create or update `frontend/.env.local`:

```env
# Point to Prism mock server
NEXT_PUBLIC_API_URL=http://localhost:4010/api/v1

# Other required variables
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_key
```

2. **Start Mock Server**

```bash
cd backend/postman
prism mock openapi.json -p 4010
```

3. **Start Frontend** (in a new terminal)

```bash
cd frontend
bun dev  # or npm run dev
```

4. **Open Browser**

Navigate to `http://localhost:3000`

### Testing Workflows

Follow the comprehensive testing guide:

📖 **[Frontend Integration Testing Guide](./FRONTEND_INTEGRATION_TESTING.md)**

This guide covers:
- Complete setup instructions
- Step-by-step testing workflows for all features
- UI rendering verification
- Data format validation
- Troubleshooting common issues
- Issue documentation templates

### Quick Test Checklist

Use the quick reference checklist for testing:

✅ **[Integration Test Checklist](./INTEGRATION_TEST_CHECKLIST.md)**

### Test Report Template

Document your testing results:

📝 **[Test Report Template](./FRONTEND_INTEGRATION_TEST_REPORT.md)**

### Key Testing Areas

1. **Crawl Jobs Workflow**
   - Create job
   - Start job
   - Monitor progress
   - Cancel job

2. **Validation Workflow**
   - Validate job images
   - Check validation results
   - Analyze single image

3. **Credits Workflow**
   - Check balance
   - View transactions
   - Purchase credits

4. **API Keys Workflow**
   - List keys
   - Create key
   - Revoke key

### Known Limitations

When testing with the mock server:

- **No Authentication Validation**: Mock server doesn't validate JWT tokens
- **Static Responses**: Data doesn't change between requests
- **No State Management**: Creating/deleting resources doesn't affect lists
- **Success Only**: Only returns success responses (200, 201)
- **No Real-time Updates**: Supabase real-time subscriptions won't work

For complete details, see the [Frontend Integration Testing Guide](./FRONTEND_INTEGRATION_TESTING.md).

---

## Available Endpoints

The mock server provides **27 endpoints** organized into 7 groups:

### 1. Crawl Jobs (6 endpoints)

Manage image crawling jobs with chunk-based processing.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/jobs/` | Create new crawl job |
| GET | `/api/v1/jobs/{job_id}` | Get job details |
| POST | `/api/v1/jobs/{job_id}/start` | Start job execution |
| POST | `/api/v1/jobs/{job_id}/cancel` | Cancel running job |
| POST | `/api/v1/jobs/{job_id}/retry` | Retry failed job |
| GET | `/api/v1/jobs/{job_id}/progress` | Get job progress |

### 2. Validation (6 endpoints)

Image validation and quality assurance operations.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/validation/analyze/` | Analyze single image |
| POST | `/api/v1/validation/batch/` | Create batch validation |
| POST | `/api/v1/validation/job/{job_id}/` | Validate job images |
| GET | `/api/v1/validation/results/{job_id}/` | Get validation results |
| GET | `/api/v1/validation/stats/{dataset_id}/` | Get dataset stats |
| PUT | `/api/v1/validation/level/` | Update validation level |

### 3. Credits & Billing (4 endpoints)

Credit management and billing operations.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/credits/balance` | Get credit balance |
| GET | `/api/v1/credits/transactions` | List transactions |
| POST | `/api/v1/credits/purchase` | Purchase credits |
| GET | `/api/v1/credits/usage` | Get usage metrics |

### 4. API Keys (4 endpoints)

Programmatic access key management.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/api-keys/` | List API keys |
| POST | `/api/v1/api-keys/` | Create API key |
| DELETE | `/api/v1/api-keys/{key_id}` | Revoke API key |
| GET | `/api/v1/api-keys/{key_id}/usage` | Get key usage |

### 5. Storage (4 endpoints)

Storage management and file operations.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/storage/usage/` | Get storage usage |
| GET | `/api/v1/storage/files/` | List storage files |
| POST | `/api/v1/storage/cleanup/` | Initiate cleanup |
| GET | `/api/v1/storage/presigned-url/` | Generate presigned URL |

### 6. Activity Logs (1 endpoint)

User activity tracking and audit trail.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/activity/` | List activity logs |

### 7. Health Checks (2 endpoints)

System health and status monitoring.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health/` | Basic health check |
| GET | `/api/v1/health/detailed` | Detailed health check |

---

## Usage Examples

### Using curl

#### 1. Health Check

```bash
curl http://localhost:4010/api/v1/health/
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-05T10:00:00Z",
  "version": "1.0.0"
}
```

#### 2. Create Crawl Job

```bash
curl -X POST http://localhost:4010/api/v1/jobs/ \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Product Images",
    "keywords": ["laptop", "computer"],
    "max_images": 1000,
    "engines": ["google", "bing"]
  }'
```

**Response:**
```json
{
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Product Images",
    "keywords": ["laptop", "computer"],
    "max_images": 1000,
    "status": "pending",
    "progress": 0,
    "total_chunks": 10,
    "active_chunks": 0,
    "completed_chunks": 0,
    "failed_chunks": 0,
    "created_at": "2025-12-05T10:00:00Z",
    "updated_at": "2025-12-05T10:00:00Z"
  }
}
```

#### 3. Get Job Progress

```bash
curl http://localhost:4010/api/v1/jobs/770e8400-e29b-41d4-a716-446655440002/progress
```

**Response:**
```json
{
  "data": {
    "job_id": "770e8400-e29b-41d4-a716-446655440002",
    "status": "running",
    "progress": 45,
    "total_chunks": 10,
    "active_chunks": 3,
    "completed_chunks": 4,
    "failed_chunks": 1,
    "images_downloaded": 450,
    "images_validated": 420,
    "images_failed": 30,
    "estimated_completion": "2025-12-05T11:00:00Z"
  }
}
```

#### 4. Validate Job Images

```bash
curl -X POST http://localhost:4010/api/v1/validation/job/770e8400-e29b-41d4-a716-446655440002/ \
  -H "Content-Type: application/json" \
  -d '{
    "validation_level": "medium"
  }'
```

**Response:**
```json
{
  "data": {
    "job_id": "770e8400-e29b-41d4-a716-446655440002",
    "task_ids": ["task_123_0", "task_123_1"],
    "images_count": 450,
    "validation_level": "medium",
    "message": "Validation started for 450 images"
  }
}
```

#### 5. Get Credit Balance

```bash
curl http://localhost:4010/api/v1/credits/balance
```

**Response:**
```json
{
  "data": {
    "current_balance": 1000,
    "monthly_usage": 250,
    "monthly_limit": 5000,
    "average_daily_usage": 8.33,
    "auto_refill_enabled": true,
    "refill_threshold": 100,
    "refill_amount": 500
  }
}
```

#### 6. List API Keys

```bash
curl http://localhost:4010/api/v1/api-keys/
```

**Response:**
```json
{
  "data": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "name": "Production API Key",
      "key_prefix": "pk_live_",
      "status": "active",
      "permissions": ["read", "write"],
      "rate_limit": 1000,
      "usage_count": 1250,
      "last_used_at": "2025-12-05T09:30:00Z",
      "created_at": "2025-11-01T10:00:00Z",
      "expires_at": "2026-11-01T10:00:00Z"
    }
  ],
  "meta": {
    "total": 3,
    "page": 1,
    "limit": 20
  }
}
```

#### 7. Get Storage Usage

```bash
curl http://localhost:4010/api/v1/storage/usage/
```

**Response:**
```json
{
  "data": {
    "total_storage_bytes": 5368709120,
    "total_storage_gb": 5.0,
    "storage_limit_gb": 100.0,
    "usage_percentage": 5.0,
    "file_count": 1250,
    "tier_breakdown": {
      "hot": {
        "storage_bytes": 2147483648,
        "storage_gb": 2.0,
        "file_count": 500
      },
      "warm": {
        "storage_bytes": 3221225472,
        "storage_gb": 3.0,
        "file_count": 750
      }
    }
  }
}
```

### Using Postman

1. **Import Collection**:
   - Open Postman
   - Click **Import**
   - Select `PixCrawler_Frontend_Mock.json`
   - Click **Import**

2. **Set Base URL**:
   - Create environment variable: `baseUrl = http://localhost:4010/api/v1`
   - Or update the variable in existing requests

3. **Test Endpoints**:
   - Navigate through folders (Crawl Jobs, Validation, Credits, etc.)
   - Click on any request
   - Click **Send**
   - View the mock response

### Frontend Integration

Configure your Next.js frontend to use the mock server:

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:4010/api/v1
```

Then start your frontend:

```bash
cd frontend
bun dev
```

The frontend will now make API calls to the mock server instead of the real backend.

---

## Troubleshooting

### Issue: "Command not found: prism"

**Cause**: Prism CLI is not installed or not in PATH.

**Solution**:
```bash
# Install globally
npm install -g @stoplight/prism-cli

# Or use npx (no installation needed)
npx @stoplight/prism-cli mock openapi.json -p 4010
```

### Issue: "Port 4010 is already in use"

**Cause**: Another process is using port 4010.

**Solution 1** - Use a different port:
```bash
prism mock openapi.json -p 4011
```

**Solution 2** - Kill the process using port 4010:
```bash
# Windows
netstat -ano | findstr :4010
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:4010 | xargs kill -9
```

### Issue: "Cannot read file openapi.json"

**Cause**: Running Prism from wrong directory.

**Solution**: Navigate to the postman directory:
```bash
cd backend/postman
prism mock openapi.json -p 4010
```

### Issue: "CORS error in browser"

**Cause**: Browser blocking cross-origin requests.

**Solution**: Prism automatically handles CORS. Ensure:
1. Mock server is running
2. Frontend is configured with correct `NEXT_PUBLIC_API_URL`
3. No browser extensions blocking requests

### Issue: "404 Not Found for endpoint"

**Cause**: Endpoint path doesn't match OpenAPI spec.

**Solution**: Check the endpoint path:
```bash
# List all available endpoints
prism mock openapi.json -p 4010
# Look for the endpoint in the startup output
```

### Issue: "Response doesn't match expected format"

**Cause**: OpenAPI spec example may differ from production.

**Solution**: 
1. Check the `openapi.json` file for the endpoint's example response
2. Refer to [Mock vs Production Differences](#mock-vs-production-differences) section
3. Update frontend code to handle mock data format

### Issue: "Mock server crashes or hangs"

**Cause**: Invalid OpenAPI specification.

**Solution**: Validate the OpenAPI spec:
```bash
# Using online validator
# Visit: https://editor.swagger.io
# Paste contents of openapi.json

# Or use validation script
python validate_openapi.py
```

### Issue: "Slow response times"

**Cause**: Prism may be slow on first request.

**Solution**: 
- First request to each endpoint may take 1-2 seconds (Prism initialization)
- Subsequent requests are fast (<100ms)
- This is normal behavior for Prism

---

## Mock vs Production Differences

The mock server is designed for frontend development and differs from production in several ways:

### 1. Success-Only Responses

**Mock**: Only returns success status codes (200, 201)
```json
{
  "data": { "id": "123", "status": "completed" }
}
```

**Production**: Returns error responses (400, 401, 404, 422, 500)
```json
{
  "message": "Validation Error",
  "details": [
    {
      "detail": "Field is required",
      "error_code": "VALUE_ERROR_MISSING",
      "field": "name"
    }
  ]
}
```

**Impact**: Frontend error handling cannot be fully tested with mock server.

### 2. Static Data

**Mock**: Returns the same example data for every request
```json
{
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "name": "Product Images"
  }
}
```

**Production**: Returns dynamic data based on database state
```json
{
  "data": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "name": "User's Actual Project Name"
  }
}
```

**Impact**: Cannot test data persistence or state changes.

### 3. No Authentication

**Mock**: Accepts all requests without authentication
```bash
curl http://localhost:4010/api/v1/jobs/
# Works without Authorization header
```

**Production**: Requires valid JWT token
```bash
curl http://localhost:8000/api/v1/jobs/ \
  -H "Authorization: Bearer <token>"
# Returns 401 without valid token
```

**Impact**: Cannot test authentication flows or permission checks.

### 4. No Side Effects

**Mock**: POST/PUT/DELETE requests don't modify any data
```bash
# Create job
curl -X POST http://localhost:4010/api/v1/jobs/ -d '{...}'

# List jobs - won't include the created job
curl http://localhost:4010/api/v1/jobs/
```

**Production**: Requests modify database state
```bash
# Create job
curl -X POST http://localhost:8000/api/v1/jobs/ -d '{...}'

# List jobs - includes the newly created job
curl http://localhost:8000/api/v1/jobs/
```

**Impact**: Cannot test CRUD workflows end-to-end.

### 5. No Real-Time Updates

**Mock**: No WebSocket or Server-Sent Events support
```javascript
// This won't work with mock server
const subscription = supabase
  .from('crawl_jobs')
  .on('UPDATE', payload => {
    console.log('Job updated:', payload);
  })
  .subscribe();
```

**Production**: Supports Supabase real-time subscriptions
```javascript
// Works with production backend
const subscription = supabase
  .from('crawl_jobs')
  .on('UPDATE', payload => {
    console.log('Job updated:', payload);
  })
  .subscribe();
```

**Impact**: Cannot test real-time progress updates or notifications.

### 6. Simplified Pagination

**Mock**: Returns fixed pagination metadata
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

**Production**: Returns actual pagination based on query parameters
```json
{
  "data": [...],
  "meta": {
    "total": 1247,
    "page": 3,
    "limit": 50,
    "pages": 25
  }
}
```

**Impact**: Cannot test pagination edge cases (last page, empty results, etc.).

### 7. No Rate Limiting

**Mock**: Accepts unlimited requests
```bash
# Can make 1000 requests instantly
for i in {1..1000}; do
  curl http://localhost:4010/api/v1/health/
done
```

**Production**: Enforces rate limits (e.g., 100 requests/minute)
```bash
# Will return 429 after limit exceeded
for i in {1..1000}; do
  curl http://localhost:8000/api/v1/health/
done
```

**Impact**: Cannot test rate limit handling or backoff strategies.

### When to Use Mock vs Production

**Use Mock Server For**:
- ✅ UI development and styling
- ✅ Component integration testing
- ✅ Rapid prototyping
- ✅ Frontend development without backend dependencies
- ✅ Testing happy-path user flows

**Use Production Backend For**:
- ✅ End-to-end testing
- ✅ Error handling validation
- ✅ Authentication and authorization testing
- ✅ Real-time feature testing
- ✅ Performance testing
- ✅ Data persistence validation

---

## Additional Resources

### Documentation Files

- **[PRISM_TESTING_GUIDE.md](./PRISM_TESTING_GUIDE.md)**: Detailed Prism testing instructions
- **[QUICK_TEST_GUIDE.md](./QUICK_TEST_GUIDE.md)**: Quick reference for testing endpoints
- **[POSTMAN_COLLECTION_TEST_REPORT.md](./POSTMAN_COLLECTION_TEST_REPORT.md)**: Test results and validation
- **[README_POSTMAN.md](./README_POSTMAN.md)**: Production API Postman collections

### Specification Files

- **[openapi.json](./openapi.json)**: OpenAPI 3.0 specification (source of truth)
- **[PixCrawler_Frontend_Mock.json](./PixCrawler_Frontend_Mock.json)**: Postman collection

### Validation Scripts

- **[validate_openapi.py](./validate_openapi.py)**: Validate OpenAPI spec
- **[validate_collection.py](./validate_collection.py)**: Validate Postman collection

### External Resources

- **Prism Documentation**: https://docs.stoplight.io/docs/prism
- **OpenAPI Specification**: https://swagger.io/specification/
- **Swagger Editor**: https://editor.swagger.io (validate OpenAPI specs)
- **Postman Learning Center**: https://learning.postman.com

---

## Contributing

When updating the mock server:

1. **Update OpenAPI Spec**: Modify `openapi.json` (source of truth)
2. **Update Postman Collection**: Sync `PixCrawler_Frontend_Mock.json`
3. **Validate Changes**: Run validation scripts
4. **Test with Prism**: Start mock server and test endpoints
5. **Update Documentation**: Update this README if needed

---

## Support

For issues or questions:

- **GitHub Issues**: [PixCrawler Issues](https://github.com/pixcrawler/pixcrawler/issues)
- **Documentation**: [PixCrawler Docs](https://docs.pixcrawler.com)
- **Email**: support@pixcrawler.com

---

**Last Updated**: December 5, 2025  
**Version**: 1.0.0  
**Total Endpoints**: 27
