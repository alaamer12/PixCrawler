# PixCrawler API Postman Collections

This directory contains Postman collections for testing the PixCrawler backend API.

## Collections

### Main Collection
- **PixCrawler.postman_collection.json** - Complete API collection with all endpoints

### Module-Specific Collections
- **PixCrawler.Authentication.postman_collection.json** - Authentication endpoints
- **PixCrawler.CrawlJobs.postman_collection.json** - Crawl job management
- **PixCrawler.Datasets.postman_collection.json** - Dataset operations (legacy)
- **PixCrawler.Exports.postman_collection.json** - Export functionality
- **PixCrawler.Health.postman_collection.json** - Health check endpoints
- **PixCrawler.Storage.postman_collection.json** - Storage operations
- **PixCrawler.Users.postman_collection.json** - User management
- **PixCrawler.Validation.postman_collection.json** - Validation services

### Environments
- **PixCrawler_Dev.postman_environment.json** - Development environment variables

## Setup

### 1. Import Collections

1. Open Postman
2. Click **Import** button
3. Select all `.postman_collection.json` files
4. Click **Import**

### 2. Import Environment

1. Click **Import** button
2. Select `PixCrawler_Dev.postman_environment.json`
3. Click **Import**
4. Select the environment from the dropdown in top-right corner

### 3. Configure Environment Variables

Update the following variables in the environment:

```json
{
  "base_url": "http://localhost:8000",
  "api_version": "v1",
  "supabase_url": "https://your-project.supabase.co",
  "supabase_anon_key": "your-anon-key",
  "access_token": "",  // Will be set automatically after login
  "user_id": "",       // Will be set automatically after login
  "project_id": "",    // Set after creating a project
  "job_id": ""         // Set after creating a job
}
```

## Authentication

### Supabase Auth Flow

PixCrawler uses **Supabase Auth exclusively** - there are no custom login/signup endpoints.

#### Option 1: Get Token from Frontend

1. Log in through the frontend application
2. Open browser DevTools → Application → Local Storage
3. Find the Supabase session token
4. Copy the `access_token` value
5. Set it in Postman environment variable `access_token`

#### Option 2: Use Supabase API Directly

```bash
# Sign up (if needed)
curl -X POST 'https://your-project.supabase.co/auth/v1/signup' \
  -H 'apikey: YOUR_ANON_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "test@example.com",
    "password": "your-password"
  }'

# Sign in
curl -X POST 'https://your-project.supabase.co/auth/v1/token?grant_type=password' \
  -H 'apikey: YOUR_ANON_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "test@example.com",
    "password": "your-password"
  }'
```

Copy the `access_token` from the response and set it in Postman.

### Using the Token

All authenticated endpoints require the token in the Authorization header:

```
Authorization: Bearer {{access_token}}
```

This is automatically configured in the collections using the `{{access_token}}` variable.

## API Endpoints

### Authentication

- **GET** `/api/v1/auth/me` - Get current user profile
- **POST** `/api/v1/auth/verify-token` - Verify Supabase JWT token
- **POST** `/api/v1/auth/sync-profile` - Sync user profile from Supabase Auth

### Projects

- **POST** `/api/v1/projects/` - Create project
- **GET** `/api/v1/projects/` - List user projects
- **GET** `/api/v1/projects/{id}` - Get project details
- **PUT** `/api/v1/projects/{id}` - Update project
- **DELETE** `/api/v1/projects/{id}` - Delete project

### Crawl Jobs

- **POST** `/api/v1/jobs/` - Create and start crawl job
- **GET** `/api/v1/jobs/` - List crawl jobs (paginated)
- **GET** `/api/v1/jobs/{id}` - Get crawl job details
- **POST** `/api/v1/jobs/{id}/cancel` - Cancel running job
- **POST** `/api/v1/jobs/{id}/retry` - Retry failed job
- **GET** `/api/v1/jobs/{id}/logs` - Get job logs
- **GET** `/api/v1/jobs/{id}/progress` - Get real-time progress

### Notifications

- **GET** `/api/v1/notifications/` - List notifications
- **POST** `/api/v1/notifications/{id}/read` - Mark as read
- **POST** `/api/v1/notifications/read-all` - Mark all as read

### Storage

- **GET** `/api/v1/storage/usage` - Get storage usage
- **GET** `/api/v1/storage/presigned-url` - Get presigned download URL

### Exports

- **POST** `/api/v1/exports/json` - Export as JSON
- **POST** `/api/v1/exports/csv` - Export as CSV
- **POST** `/api/v1/exports/zip` - Export as ZIP

### Validation

- **POST** `/api/v1/validation/batch` - Create batch validation
- **GET** `/api/v1/validation/{id}` - Get validation status

### Health

- **GET** `/api/v1/health/` - Service health check
- **GET** `/health` - Root health check

## Response Formats

### Success Response (List)

```json
{
  "data": [
    {
      "id": 1,
      "name": "Example",
      "status": "active"
    }
  ],
  "meta": {
    "total": 10,
    "skip": 0,
    "limit": 50
  }
}
```

### Success Response (Single)

```json
{
  "id": 1,
  "name": "Example",
  "status": "active",
  "created_at": "2024-01-27T10:30:00Z"
}
```

### Error Response

```json
{
  "detail": "Error message",
  "status_code": 400
}
```

## Common Error Codes

- **400 Bad Request** - Invalid input data
- **401 Unauthorized** - Missing or invalid authentication token
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Resource not found
- **422 Unprocessable Entity** - Validation error
- **429 Too Many Requests** - Rate limit exceeded
- **500 Internal Server Error** - Server error

## Testing Workflow

### 1. Health Check

```
GET /health
```

Verify the API is running.

### 2. Authenticate

Get your Supabase access token (see Authentication section above) and set it in the environment.

### 3. Verify Authentication

```
GET /api/v1/auth/me
Authorization: Bearer {{access_token}}
```

Verify your token is valid and get your user profile.

### 4. Create Project

```
POST /api/v1/projects/
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
  "name": "My Test Project",
  "description": "Testing the API"
}
```

Save the returned `project_id` in the environment.

### 5. Create Crawl Job

```
POST /api/v1/jobs/
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
  "project_id": {{project_id}},
  "name": "Test Crawl Job",
  "keywords": ["cats", "dogs"],
  "max_images": 100,
  "search_engine": "duckduckgo"
}
```

Save the returned `job_id` in the environment.

### 6. Monitor Job Progress

```
GET /api/v1/jobs/{{job_id}}/progress
Authorization: Bearer {{access_token}}
```

Check the job status and progress.

### 7. Get Notifications

```
GET /api/v1/notifications/
Authorization: Bearer {{access_token}}
```

View notifications about job completion.

## Rate Limiting

The API implements rate limiting using Redis:

- **Default**: 100 requests per minute per user
- **Specific endpoints**: May have stricter limits (e.g., 10 requests/minute for job creation)

When rate limited, you'll receive a `429 Too Many Requests` response with a `Retry-After` header.

## OpenAPI Documentation

For complete API documentation with request/response schemas:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Troubleshooting

### "401 Unauthorized" Error

- Verify your `access_token` is set in the environment
- Check that the token hasn't expired (Supabase tokens expire after 1 hour by default)
- Get a fresh token from Supabase

### "404 Not Found" Error

- Verify the resource ID exists
- Check that you have permission to access the resource
- Ensure you're using the correct endpoint URL

### "422 Validation Error" Error

- Check the request body matches the expected schema
- Verify all required fields are provided
- Check field types and constraints (e.g., min/max values)

### Connection Refused

- Verify the backend server is running
- Check the `base_url` in your environment matches your server
- Ensure no firewall is blocking the connection

## Contributing

When adding new endpoints:

1. Update the appropriate collection file
2. Follow the existing request naming convention
3. Include example request bodies
4. Add tests for success and error cases
5. Update this README with the new endpoint

## Additional Resources

- [Backend README](../README.md)
- [Architecture Documentation](../ARCHITECTURE.md)
- [Endpoint Style Guide](../api/v1/ENDPOINT_STYLE_GUIDE.md)
- [Migration Guide](../../docs/MIGRATION_GUIDE.md)

---

**Last Updated:** January 2025  
**Version:** 1.0.0
