# PixCrawler API Documentation

This document provides comprehensive documentation for the PixCrawler REST API, including authentication, endpoints, request/response formats, rate limiting, and error handling.

## Table of Contents

- [Overview](#overview)
- [Base URL](#base-url)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Error Handling](#error-handling)
- [API Endpoints](#api-endpoints)
- [Request Examples](#request-examples)
- [Response Examples](#response-examples)
- [Webhooks](#webhooks)
- [SDKs and Client Libraries](#sdks-and-client-libraries)

---

## Overview

The PixCrawler API is a RESTful API that allows you to programmatically create and manage image datasets, crawl jobs, and user accounts. The API uses JSON for request and response bodies, and follows standard HTTP conventions for methods and status codes.

### Key Features

- **RESTful Design**: Standard HTTP methods (GET, POST, PATCH, DELETE)
- **JSON Format**: All requests and responses use JSON
- **Authentication**: Supabase Auth with JWT tokens
- **Rate Limiting**: Configurable rate limits per endpoint
- **Pagination**: Cursor-based pagination for list endpoints
- **Versioning**: API versioned at `/api/v1`
- **OpenAPI**: Auto-generated OpenAPI 3.0 specification

### Interactive Documentation

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs) (development)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc) (development)
- **OpenAPI Spec**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## Base URL

### Development
```
http://localhost:8000/api/v1
```

### Production
```
https://api.pixcrawler.com/api/v1
```

All API endpoints are prefixed with `/api/v1`.

---

## Authentication

PixCrawler uses **Supabase Auth** for authentication. All authenticated endpoints require a valid JWT token in the `Authorization` header.

### Authentication Flow

1. **Sign Up**: Create account via Supabase Auth
2. **Sign In**: Authenticate and receive JWT token
3. **Use Token**: Include token in API requests
4. **Refresh**: Refresh token before expiration

### Token Format

```http
Authorization: Bearer <jwt_token>
```

### Authentication Endpoints

#### Sign Up
```http
POST /api/v1/auth/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe"
}
```

**Response**:
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "full_name": "John Doe"
  },
  "session": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 3600
  }
}
```

#### Sign In
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

#### Get Profile
```http
GET /api/v1/auth/profile
Authorization: Bearer <token>
```

#### Update Profile
```http
PATCH /api/v1/auth/profile
Authorization: Bearer <token>
Content-Type: application/json

{
  "full_name": "Jane Doe",
  "avatar_url": "https://example.com/avatar.jpg"
}
```

#### Refresh Token
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### API Key Authentication (Alternative)

For programmatic access, you can use API keys instead of JWT tokens:

```http
X-API-Key: your-api-key-here
```

Create API keys via the dashboard or API:

```http
POST /api/v1/api-keys
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Production API Key",
  "permissions": ["read", "write"],
  "rate_limit": 1000
}
```

---

## Rate Limiting

The API implements rate limiting to prevent abuse and ensure fair usage.

### Rate Limit Headers

Every API response includes rate limit information:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1638360000
```

### Default Limits

- **Authenticated Users**: 100 requests per minute
- **API Keys**: Configurable per key
- **Unauthenticated**: 20 requests per minute

### Rate Limit Exceeded

When rate limit is exceeded, you'll receive a `429 Too Many Requests` response:

```json
{
  "message": "Too Many Requests",
  "details": [
    {
      "detail": "Rate limit exceeded. Please try again later.",
      "error_code": "RATE_LIMIT_EXCEEDED"
    }
  ]
}
```

### Handling Rate Limits

1. **Respect Headers**: Check `X-RateLimit-Remaining` before making requests
2. **Implement Backoff**: Use exponential backoff when rate limited
3. **Upgrade Plan**: Contact support for higher rate limits

---

## Error Handling

The API uses standard HTTP status codes and returns consistent error responses.

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 204 | No Content | Request succeeded, no content to return |
| 400 | Bad Request | Invalid request format or parameters |
| 401 | Unauthorized | Authentication required or invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Error Response Format

All errors follow a consistent format:

```json
{
  "message": "Validation Error",
  "details": [
    {
      "detail": "Email address is required",
      "error_code": "VALUE_ERROR_MISSING",
      "field": "email"
    },
    {
      "detail": "Password must be at least 8 characters",
      "error_code": "VALUE_ERROR_TOO_SHORT",
      "field": "password"
    }
  ],
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Error Codes

Common error codes:

- `VALIDATION_ERROR`: Input validation failed
- `NOT_FOUND`: Resource not found
- `UNAUTHORIZED`: Authentication required
- `FORBIDDEN`: Insufficient permissions
- `DUPLICATE_EMAIL`: Email already registered
- `INVALID_CREDENTIALS`: Invalid email or password
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INSUFFICIENT_CREDITS`: Not enough credits

---

## API Endpoints

### Health Check

#### Get Health Status
```http
GET /health
```

Returns system health status including database, Redis, and Celery workers.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-30T12:00:00Z",
  "services": {
    "database": {
      "status": "healthy",
      "message": "Database connection successful"
    },
    "redis": {
      "status": "healthy",
      "message": "Redis connection successful"
    },
    "celery": {
      "status": "healthy",
      "message": "2 worker(s) active",
      "workers": ["worker1@hostname", "worker2@hostname"]
    }
  }
}
```

### Projects

#### List Projects
```http
GET /api/v1/projects
Authorization: Bearer <token>
```

**Query Parameters**:
- `page` (integer): Page number (default: 1)
- `size` (integer): Items per page (default: 20, max: 100)
- `sort` (string): Sort field (default: created_at)
- `order` (string): Sort order (asc, desc)

**Response**:
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "E-commerce Products",
      "description": "Product images for ML model",
      "user_id": "660e8400-e29b-41d4-a716-446655440001",
      "created_at": "2025-11-30T12:00:00Z",
      "updated_at": "2025-11-30T12:00:00Z",
      "job_count": 5,
      "image_count": 1250
    }
  ],
  "total": 10,
  "page": 1,
  "size": 20,
  "pages": 1
}
```

#### Create Project
```http
POST /api/v1/projects
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "E-commerce Products",
  "description": "Product images for ML model"
}
```

#### Get Project
```http
GET /api/v1/projects/{project_id}
Authorization: Bearer <token>
```

#### Update Project
```http
PATCH /api/v1/projects/{project_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Updated Project Name",
  "description": "Updated description"
}
```

#### Delete Project
```http
DELETE /api/v1/projects/{project_id}
Authorization: Bearer <token>
```

### Crawl Jobs

#### List Crawl Jobs
```http
GET /api/v1/jobs
Authorization: Bearer <token>
```

**Query Parameters**:
- `project_id` (uuid): Filter by project
- `status` (string): Filter by status (pending, running, completed, failed)
- `page` (integer): Page number
- `size` (integer): Items per page

#### Create Crawl Job
```http
POST /api/v1/jobs
Authorization: Bearer <token>
Content-Type: application/json

{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "keywords": ["laptop", "computer", "notebook"],
  "max_images": 1000,
  "engines": ["google", "bing", "duckduckgo"],
  "quality_filters": {
    "min_resolution": [224, 224],
    "formats": ["jpg", "png", "webp"]
  }
}
```

**Response**:
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "keywords": ["laptop", "computer", "notebook"],
  "max_images": 1000,
  "status": "pending",
  "progress": 0,
  "total_chunks": 10,
  "active_chunks": 0,
  "completed_chunks": 0,
  "failed_chunks": 0,
  "created_at": "2025-11-30T12:00:00Z"
}
```

#### Get Job Status
```http
GET /api/v1/jobs/{job_id}
Authorization: Bearer <token>
```

#### Start Job
```http
POST /api/v1/jobs/{job_id}/start
Authorization: Bearer <token>
```

#### Stop Job
```http
POST /api/v1/jobs/{job_id}/stop
Authorization: Bearer <token>
```

#### Retry Failed Job
```http
POST /api/v1/jobs/{job_id}/retry
Authorization: Bearer <token>
```

#### Get Job Progress
```http
GET /api/v1/jobs/{job_id}/progress
Authorization: Bearer <token>
```

**Response**:
```json
{
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
  "estimated_completion": "2025-11-30T13:00:00Z"
}
```

### Images

#### List Job Images
```http
GET /api/v1/jobs/{job_id}/images
Authorization: Bearer <token>
```

**Query Parameters**:
- `page` (integer): Page number
- `size` (integer): Items per page
- `is_valid` (boolean): Filter by validation status
- `is_duplicate` (boolean): Filter by duplicate status

#### Get Image Details
```http
GET /api/v1/images/{image_id}
Authorization: Bearer <token>
```

#### Delete Image
```http
DELETE /api/v1/images/{image_id}
Authorization: Bearer <token>
```

#### Download Image
```http
GET /api/v1/images/{image_id}/download
Authorization: Bearer <token>
```

### Notifications

#### List Notifications
```http
GET /api/v1/notifications
Authorization: Bearer <token>
```

**Query Parameters**:
- `is_read` (boolean): Filter by read status
- `category` (string): Filter by category
- `page` (integer): Page number
- `size` (integer): Items per page

#### Mark as Read
```http
PATCH /api/v1/notifications/{notification_id}/read
Authorization: Bearer <token>
```

#### Mark All as Read
```http
PATCH /api/v1/notifications/read-all
Authorization: Bearer <token>
```

#### Get Notification Preferences
```http
GET /api/v1/notifications/preferences
Authorization: Bearer <token>
```

#### Update Notification Preferences
```http
PATCH /api/v1/notifications/preferences
Authorization: Bearer <token>
Content-Type: application/json

{
  "email_enabled": true,
  "push_enabled": true,
  "crawl_jobs_enabled": true,
  "datasets_enabled": true,
  "billing_enabled": true,
  "digest_frequency": "daily"
}
```

### Credits & Billing

#### Get Credit Balance
```http
GET /api/v1/credits/balance
Authorization: Bearer <token>
```

**Response**:
```json
{
  "current_balance": 1000,
  "monthly_usage": 250,
  "monthly_limit": 5000,
  "auto_refill_enabled": true,
  "refill_threshold": 100,
  "refill_amount": 500
}
```

#### List Transactions
```http
GET /api/v1/credits/transactions
Authorization: Bearer <token>
```

**Query Parameters**:
- `type` (string): Filter by type (purchase, usage, refund, bonus)
- `start_date` (date): Start date filter
- `end_date` (date): End date filter
- `page` (integer): Page number
- `size` (integer): Items per page

#### Purchase Credits
```http
POST /api/v1/credits/purchase
Authorization: Bearer <token>
Content-Type: application/json

{
  "amount": 1000,
  "payment_method": "lemonsqueezy",
  "payment_token": "order_123"
}
```

#### Get Usage Metrics
```http
GET /api/v1/credits/usage
Authorization: Bearer <token>
```

**Query Parameters**:
- `start_date` (date): Start date
- `end_date` (date): End date
- `granularity` (string): daily, weekly, monthly

### API Keys

#### List API Keys
```http
GET /api/v1/api-keys
Authorization: Bearer <token>
```

#### Create API Key
```http
POST /api/v1/api-keys
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Production API Key",
  "permissions": ["read", "write"],
  "rate_limit": 1000,
  "expires_at": "2026-11-30T12:00:00Z"
}
```

**Response**:
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440003",
  "name": "Production API Key",
  "key": "pk_live_1234567890abcdef",
  "key_prefix": "pk_live_",
  "permissions": ["read", "write"],
  "rate_limit": 1000,
  "created_at": "2025-11-30T12:00:00Z",
  "expires_at": "2026-11-30T12:00:00Z"
}
```

**Important**: The full API key is only shown once during creation. Store it securely.

#### Revoke API Key
```http
DELETE /api/v1/api-keys/{key_id}
Authorization: Bearer <token>
```

#### Get API Key Usage
```http
GET /api/v1/api-keys/{key_id}/usage
Authorization: Bearer <token>
```

### Activity Logs

#### List Activity Logs
```http
GET /api/v1/activity
Authorization: Bearer <token>
```

**Query Parameters**:
- `action` (string): Filter by action type
- `resource_type` (string): Filter by resource type
- `start_date` (date): Start date filter
- `end_date` (date): End date filter
- `page` (integer): Page number
- `size` (integer): Items per page

**Response**:
```json
{
  "items": [
    {
      "id": "990e8400-e29b-41d4-a716-446655440004",
      "user_id": "660e8400-e29b-41d4-a716-446655440001",
      "action": "create",
      "resource_type": "crawl_job",
      "resource_id": "770e8400-e29b-41d4-a716-446655440002",
      "metadata": {
        "keywords": ["laptop", "computer"],
        "max_images": 1000
      },
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0...",
      "created_at": "2025-11-30T12:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "size": 20
}
```

---

## Request Examples

### cURL Examples

#### Create Project
```bash
curl -X POST https://api.pixcrawler.com/api/v1/projects \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "E-commerce Products",
    "description": "Product images for ML model"
  }'
```

#### Start Crawl Job
```bash
curl -X POST https://api.pixcrawler.com/api/v1/jobs \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "keywords": ["laptop", "computer"],
    "max_images": 1000
  }'
```

### Python Examples

```python
import requests

# Configuration
BASE_URL = "https://api.pixcrawler.com/api/v1"
TOKEN = "your_jwt_token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Create project
response = requests.post(
    f"{BASE_URL}/projects",
    headers=headers,
    json={
        "name": "E-commerce Products",
        "description": "Product images for ML model"
    }
)
project = response.json()
print(f"Created project: {project['id']}")

# Create crawl job
response = requests.post(
    f"{BASE_URL}/jobs",
    headers=headers,
    json={
        "project_id": project["id"],
        "keywords": ["laptop", "computer"],
        "max_images": 1000
    }
)
job = response.json()
print(f"Created job: {job['id']}")

# Check job status
response = requests.get(
    f"{BASE_URL}/jobs/{job['id']}",
    headers=headers
)
status = response.json()
print(f"Job status: {status['status']}, Progress: {status['progress']}%")
```

### JavaScript Examples

```javascript
const BASE_URL = 'https://api.pixcrawler.com/api/v1';
const TOKEN = 'your_jwt_token';

const headers = {
  'Authorization': `Bearer ${TOKEN}`,
  'Content-Type': 'application/json'
};

// Create project
const createProject = async () => {
  const response = await fetch(`${BASE_URL}/projects`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      name: 'E-commerce Products',
      description: 'Product images for ML model'
    })
  });
  const project = await response.json();
  console.log('Created project:', project.id);
  return project;
};

// Create crawl job
const createJob = async (projectId) => {
  const response = await fetch(`${BASE_URL}/jobs`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      project_id: projectId,
      keywords: ['laptop', 'computer'],
      max_images: 1000
    })
  });
  const job = await response.json();
  console.log('Created job:', job.id);
  return job;
};

// Check job status
const checkJobStatus = async (jobId) => {
  const response = await fetch(`${BASE_URL}/jobs/${jobId}`, {
    headers
  });
  const status = await response.json();
  console.log(`Job status: ${status.status}, Progress: ${status.progress}%`);
  return status;
};

// Usage
(async () => {
  const project = await createProject();
  const job = await createJob(project.id);
  const status = await checkJobStatus(job.id);
})();
```

---

## Response Examples

### Successful Response

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "E-commerce Products",
  "description": "Product images for ML model",
  "created_at": "2025-11-30T12:00:00Z",
  "updated_at": "2025-11-30T12:00:00Z"
}
```

### Paginated Response

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "size": 20,
  "pages": 5
}
```

### Error Response

```json
{
  "message": "Validation Error",
  "details": [
    {
      "detail": "Field is required",
      "error_code": "VALUE_ERROR_MISSING",
      "field": "name"
    }
  ],
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## Webhooks

Webhooks allow you to receive real-time notifications about events in your account.

### Supported Events

- `job.started`: Crawl job started
- `job.completed`: Crawl job completed
- `job.failed`: Crawl job failed
- `dataset.ready`: Dataset ready for download
- `credits.low`: Credit balance below threshold
- `credits.depleted`: Credit balance exhausted

### Webhook Configuration

Configure webhooks in your account settings or via API:

```http
POST /api/v1/webhooks
Authorization: Bearer <token>
Content-Type: application/json

{
  "url": "https://your-app.com/webhooks/pixcrawler",
  "events": ["job.completed", "dataset.ready"],
  "secret": "your_webhook_secret"
}
```

### Webhook Payload

```json
{
  "event": "job.completed",
  "timestamp": "2025-11-30T12:00:00Z",
  "data": {
    "job_id": "770e8400-e29b-41d4-a716-446655440002",
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "images_downloaded": 1000,
    "images_validated": 950
  }
}
```

### Webhook Verification

Verify webhook signatures to ensure authenticity:

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
```

---

## SDKs and Client Libraries

### Official SDKs (Planned)

- **Python SDK**: `pip install pixcrawler`
- **JavaScript SDK**: `npm install @pixcrawler/sdk`
- **Go SDK**: `go get github.com/pixcrawler/go-sdk`

### Community Libraries

Check our [GitHub organization](https://github.com/pixcrawler) for community-contributed libraries.

---

## Support

- **Documentation**: [https://docs.pixcrawler.com](https://docs.pixcrawler.com)
- **API Status**: [https://status.pixcrawler.com](https://status.pixcrawler.com)
- **Support Email**: support@pixcrawler.com
- **GitHub Issues**: [https://github.com/pixcrawler/pixcrawler/issues](https://github.com/pixcrawler/pixcrawler/issues)

---

## Changelog

### v1.0.0 (2025-11-30)

- Initial API release
- Authentication endpoints
- Project management
- Crawl job management
- Image management
- Notifications
- Credits and billing
- API keys
- Activity logs
- Rate limiting
- Comprehensive error handling
