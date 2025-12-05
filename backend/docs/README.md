# Backend Documentation

This directory contains comprehensive documentation for the PixCrawler backend API and its components.

## Documentation Files

### API Documentation

- **[CELERY_INTEGRATION_API.md](./CELERY_INTEGRATION_API.md)** - Comprehensive guide for Celery-integrated endpoints
  - Start/stop crawl jobs
  - Progress tracking with chunk statistics
  - Image validation with multiple levels
  - Complete code examples in Python, JavaScript, and cURL
  - Error handling patterns
  - Celery task architecture and best practices

### Architecture & Design

- **[DATASET_PROCESSING_PIPELINE.md](./DATASET_PROCESSING_PIPELINE.md)** - Dataset generation and processing pipeline
- **[JOB_ORCHESTRATOR.md](./JOB_ORCHESTRATOR.md)** - Job orchestration and task management
- **[ORCHESTRATOR_QUICK_REFERENCE.md](./ORCHESTRATOR_QUICK_REFERENCE.md)** - Quick reference for orchestrator usage

## Quick Links

### Interactive API Documentation

When running the backend server, you can access interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### Related Documentation

- **[Main API Documentation](../../.kiro/steering/API_DOCUMENTATION.md)** - Complete API reference
- **[Architecture Overview](../../.kiro/steering/architecture.md)** - System architecture
- **[Technology Stack](../../.kiro/steering/tech.md)** - Technology choices and stack
- **[Project Structure](../../.kiro/steering/structure.md)** - Repository organization

## Getting Started

### 1. Start the Backend Server

```bash
# From the backend directory
cd backend

# Install dependencies
uv sync

# Run development server
uv run uvicorn backend.main:app --reload
```

The API will be available at http://localhost:8000

### 2. Explore the API

Visit http://localhost:8000/docs to explore the interactive Swagger UI documentation.

### 3. Start Celery Workers

For full functionality, you'll need Celery workers running:

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery worker
celery -A celery_core.app worker --loglevel=info
```

### 4. Test the API

Use the examples in [CELERY_INTEGRATION_API.md](./CELERY_INTEGRATION_API.md) to test the endpoints.

## Key Features

### Asynchronous Processing

The backend uses Celery for distributed task processing:

- **Download Tasks**: Parallel image crawling from multiple search engines
- **Validation Tasks**: Image quality and duplicate detection
- **Progress Tracking**: Real-time updates with chunk-based tracking

### Authentication

All endpoints use Supabase Auth with JWT tokens:

```bash
# Get a token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Use the token
curl -X GET http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Rate Limiting

The API implements rate limiting via Redis:

- **Default**: 100 requests per minute for authenticated users
- **Job Start**: 10 requests per minute
- **Job Retry**: 5 requests per minute

## Common Workflows

### 1. Create and Start a Crawl Job

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "your_jwt_token"
headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

# Create job
response = requests.post(
    f"{BASE_URL}/jobs",
    headers=headers,
    json={
        "project_id": "project-uuid",
        "name": "Cat Images",
        "keywords": ["cats", "kittens"],
        "max_images": 1000
    }
)
job = response.json()

# Start job
response = requests.post(f"{BASE_URL}/jobs/{job['id']}/start", headers=headers)
result = response.json()
print(f"Started job with {result['total_chunks']} chunks")
```

### 2. Monitor Job Progress

```python
import time

def monitor_progress(job_id):
    while True:
        response = requests.get(f"{BASE_URL}/jobs/{job_id}/progress", headers=headers)
        progress = response.json()
        
        print(f"Progress: {progress['progress']}% | Status: {progress['status']}")
        
        if progress['status'] in ['completed', 'failed', 'cancelled']:
            break
        
        time.sleep(5)

monitor_progress(job['id'])
```

### 3. Validate Images

```python
# Validate with medium level
response = requests.post(
    f"{BASE_URL}/validation/job/{job['id']}/",
    headers=headers,
    json={"level": "medium"}
)
validation = response.json()
print(f"Validating {validation['images_count']} images")
```

## Error Handling

All endpoints return consistent error responses:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common status codes:
- `200`: Success
- `400`: Bad request (wrong status, invalid input)
- `401`: Unauthorized (missing/invalid token)
- `403`: Forbidden (insufficient permissions)
- `404`: Not found
- `422`: Validation error
- `429`: Rate limit exceeded
- `500`: Server error

## Support

- **GitHub Issues**: https://github.com/alaamer12/pixcrawler/issues
- **Email**: support@pixcrawler.com
- **Documentation**: See files in this directory

## Contributing

When adding new endpoints or features:

1. Update the OpenAPI documentation in the endpoint file
2. Add examples to [CELERY_INTEGRATION_API.md](./CELERY_INTEGRATION_API.md)
3. Update this README if needed
4. Test with Swagger UI at http://localhost:8000/docs
