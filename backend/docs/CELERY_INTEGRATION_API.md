# Celery Integration API Documentation

This document provides comprehensive examples and documentation for the Celery-integrated API endpoints in PixCrawler, including crawl job management and image validation.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Crawl Job Endpoints](#crawl-job-endpoints)
- [Validation Endpoints](#validation-endpoints)
- [Error Handling](#error-handling)
- [Celery Task Integration](#celery-task-integration)

---

## Overview

The PixCrawler API integrates with Celery for distributed task processing, enabling asynchronous image crawling and validation. This document focuses on the endpoints that interact with Celery workers.

### Key Features

- **Asynchronous Processing**: Long-running tasks executed by Celery workers
- **Progress Tracking**: Real-time progress updates with chunk-based tracking
- **Task Management**: Start, stop, and monitor distributed tasks
- **Validation Levels**: Configurable validation (fast, medium, slow)

### Base URL

```
Development: http://localhost:8000/api/v1
Production: https://api.pixcrawler.com/api/v1
```

---

## Authentication

All endpoints require authentication via Bearer token:

```http
Authorization: Bearer <your_jwt_token>
```

### Getting a Token

```bash
# Sign in to get JWT token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "your_password"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## Crawl Job Endpoints

### 1. Start Crawl Job

Start a pending crawl job by dispatching Celery tasks for each keyword-engine combination.

**Endpoint:** `POST /api/v1/jobs/{job_id}/start`

**Rate Limit:** 10 requests per minute

#### cURL Example

```bash
curl -X POST http://localhost:8000/api/v1/jobs/123/start \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

#### Python Example

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "your_jwt_token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Start a crawl job
response = requests.post(
    f"{BASE_URL}/jobs/123/start",
    headers=headers
)

if response.status_code == 200:
    result = response.json()
    print(f"Job started successfully!")
    print(f"Status: {result['status']}")
    print(f"Total chunks: {result['total_chunks']}")
    print(f"Task IDs: {result['task_ids']}")
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

#### JavaScript Example

```javascript
const BASE_URL = 'http://localhost:8000/api/v1';
const TOKEN = 'your_jwt_token';

async function startCrawlJob(jobId) {
  const response = await fetch(`${BASE_URL}/jobs/${jobId}/start`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${TOKEN}`,
      'Content-Type': 'application/json'
    }
  });

  if (response.ok) {
    const result = await response.json();
    console.log('Job started successfully!');
    console.log('Status:', result.status);
    console.log('Total chunks:', result.total_chunks);
    console.log('Task IDs:', result.task_ids);
  } else {
    const error = await response.json();
    console.error('Error:', error);
  }
}

// Usage
startCrawlJob(123);
```

#### Success Response (200 OK)

```json
{
  "job_id": 123,
  "status": "running",
  "task_ids": [
    "task-uuid-1",
    "task-uuid-2",
    "task-uuid-3",
    "task-uuid-4",
    "task-uuid-5",
    "task-uuid-6"
  ],
  "total_chunks": 6,
  "message": "Job started with 6 tasks"
}
```

#### Error Responses

**400 Bad Request** - Job not in pending status:
```json
{
  "detail": "Cannot start job with status 'running'. Only pending jobs can be started."
}
```

**404 Not Found** - Job doesn't exist:
```json
{
  "detail": "Crawl job not found"
}
```

**403 Forbidden** - User doesn't own the job:
```json
{
  "detail": "Access denied to this resource"
}
```

---

### 2. Stop Crawl Job

Cancel a running or pending crawl job by revoking all Celery tasks.

**Endpoint:** `POST /api/v1/jobs/{job_id}/cancel`

#### cURL Example

```bash
curl -X POST http://localhost:8000/api/v1/jobs/123/cancel \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

#### Python Example

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "your_jwt_token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Cancel a crawl job
response = requests.post(
    f"{BASE_URL}/jobs/123/cancel",
    headers=headers
)

if response.status_code == 200:
    result = response.json()
    print(f"Job cancelled successfully!")
    print(f"Status: {result['status']}")
    print(f"Revoked tasks: {result['revoked_tasks']}")
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

#### JavaScript Example

```javascript
async function cancelCrawlJob(jobId) {
  const response = await fetch(`${BASE_URL}/jobs/${jobId}/cancel`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${TOKEN}`,
      'Content-Type': 'application/json'
    }
  });

  if (response.ok) {
    const result = await response.json();
    console.log('Job cancelled successfully!');
    console.log('Status:', result.status);
    console.log('Revoked tasks:', result.revoked_tasks);
  } else {
    const error = await response.json();
    console.error('Error:', error);
  }
}

// Usage
cancelCrawlJob(123);
```

#### Success Response (200 OK)

```json
{
  "job_id": 123,
  "status": "cancelled",
  "revoked_tasks": 6,
  "message": "Job cancelled successfully. 6 task(s) revoked."
}
```

#### Error Responses

**400 Bad Request** - Job cannot be cancelled:
```json
{
  "detail": "Cannot cancel job with status: completed"
}
```

---

### 3. Get Job Progress

Get real-time progress updates for a crawl job with chunk statistics.

**Endpoint:** `GET /api/v1/jobs/{job_id}/progress`

#### cURL Example

```bash
curl -X GET http://localhost:8000/api/v1/jobs/123/progress \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Python Example

```python
import requests
import time

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "your_jwt_token"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

def monitor_job_progress(job_id, interval=5):
    """Monitor job progress with polling."""
    while True:
        response = requests.get(
            f"{BASE_URL}/jobs/{job_id}/progress",
            headers=headers
        )
        
        if response.status_code == 200:
            progress = response.json()
            print(f"\rProgress: {progress['progress']}% | "
                  f"Status: {progress['status']} | "
                  f"Completed: {progress['completed_chunks']}/{progress['total_chunks']} | "
                  f"Images: {progress['downloaded_images']}", end='')
            
            # Stop monitoring if job is complete
            if progress['status'] in ['completed', 'failed', 'cancelled']:
                print(f"\n\nJob finished with status: {progress['status']}")
                break
        else:
            print(f"\nError: {response.status_code}")
            break
        
        time.sleep(interval)

# Usage
monitor_job_progress(123, interval=5)
```

#### JavaScript Example

```javascript
async function monitorJobProgress(jobId, interval = 5000) {
  const checkProgress = async () => {
    const response = await fetch(`${BASE_URL}/jobs/${jobId}/progress`, {
      headers: {
        'Authorization': `Bearer ${TOKEN}`
      }
    });

    if (response.ok) {
      const progress = await response.json();
      console.log(`Progress: ${progress.progress}%`);
      console.log(`Status: ${progress.status}`);
      console.log(`Completed: ${progress.completed_chunks}/${progress.total_chunks}`);
      console.log(`Images: ${progress.downloaded_images}`);

      // Stop monitoring if job is complete
      if (['completed', 'failed', 'cancelled'].includes(progress.status)) {
        console.log(`\nJob finished with status: ${progress.status}`);
        return;
      }

      // Continue monitoring
      setTimeout(checkProgress, interval);
    } else {
      console.error('Error:', await response.json());
    }
  };

  checkProgress();
}

// Usage
monitorJobProgress(123, 5000);
```

#### Success Response (200 OK)

```json
{
  "job_id": 123,
  "status": "running",
  "progress": 75,
  "total_chunks": 10,
  "active_chunks": 2,
  "completed_chunks": 7,
  "failed_chunks": 1,
  "downloaded_images": 750,
  "estimated_completion": null,
  "started_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:15:00Z"
}
```

---

## Validation Endpoints

### 1. Validate Job Images

Validate all images in a crawl job using Celery validation tasks.

**Endpoint:** `POST /api/v1/validation/job/{job_id}/`

#### Request Body

```json
{
  "level": "medium"
}
```

**Validation Levels:**
- `fast`: Quick validation (1000/min rate limit)
- `medium`: Standard validation (500/min rate limit) - **Default**
- `slow`: Thorough validation (100/min rate limit)

#### cURL Example

```bash
curl -X POST http://localhost:8000/api/v1/validation/job/123/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "level": "medium"
  }'
```

#### Python Example

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "your_jwt_token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Validate job images
response = requests.post(
    f"{BASE_URL}/validation/job/123/",
    headers=headers,
    json={"level": "medium"}
)

if response.status_code == 200:
    result = response.json()
    print(f"Validation started!")
    print(f"Images count: {result['images_count']}")
    print(f"Validation level: {result['validation_level']}")
    print(f"Task IDs: {result['task_ids']}")
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

#### JavaScript Example

```javascript
async function validateJobImages(jobId, level = 'medium') {
  const response = await fetch(`${BASE_URL}/validation/job/${jobId}/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${TOKEN}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ level })
  });

  if (response.ok) {
    const result = await response.json();
    console.log('Validation started!');
    console.log('Images count:', result.images_count);
    console.log('Validation level:', result.validation_level);
    console.log('Task IDs:', result.task_ids);
  } else {
    const error = await response.json();
    console.error('Error:', error);
  }
}

// Usage
validateJobImages(123, 'medium');
```

#### Success Response (200 OK)

```json
{
  "job_id": 123,
  "images_count": 100,
  "validation_level": "medium",
  "task_ids": [
    "task_123_0",
    "task_123_1",
    "task_123_2"
  ],
  "message": "Validation started for 100 images"
}
```

#### Error Responses

**404 Not Found** - No images found:
```json
{
  "detail": "No images found for job 123"
}
```

**422 Unprocessable Entity** - Invalid validation level:
```json
{
  "detail": [
    {
      "loc": ["body", "level"],
      "msg": "value is not a valid enumeration member; permitted: 'fast', 'medium', 'slow'",
      "type": "type_error.enum"
    }
  ]
}
```

---

## Error Handling

### Standard Error Response Format

All errors follow a consistent format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request (wrong status, etc.) |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

### Error Handling Examples

#### Python Error Handling

```python
import requests
from requests.exceptions import RequestException

def start_job_with_error_handling(job_id):
    """Start job with comprehensive error handling."""
    try:
        response = requests.post(
            f"{BASE_URL}/jobs/{job_id}/start",
            headers=headers,
            timeout=30
        )
        
        # Raise exception for bad status codes
        response.raise_for_status()
        
        return response.json()
        
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        error_detail = e.response.json().get('detail', 'Unknown error')
        
        if status_code == 400:
            print(f"Bad Request: {error_detail}")
        elif status_code == 401:
            print("Unauthorized: Please check your token")
        elif status_code == 403:
            print("Forbidden: You don't have access to this job")
        elif status_code == 404:
            print("Not Found: Job doesn't exist")
        elif status_code == 429:
            print("Rate Limit Exceeded: Please wait before retrying")
        elif status_code == 500:
            print(f"Server Error: {error_detail}")
        else:
            print(f"HTTP Error {status_code}: {error_detail}")
            
    except requests.exceptions.Timeout:
        print("Request timed out")
        
    except requests.exceptions.ConnectionError:
        print("Connection error: Could not reach the server")
        
    except RequestException as e:
        print(f"Request failed: {str(e)}")
        
    return None
```

#### JavaScript Error Handling

```javascript
async function startJobWithErrorHandling(jobId) {
  try {
    const response = await fetch(`${BASE_URL}/jobs/${jobId}/start`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${TOKEN}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      const error = await response.json();
      
      switch (response.status) {
        case 400:
          console.error('Bad Request:', error.detail);
          break;
        case 401:
          console.error('Unauthorized: Please check your token');
          break;
        case 403:
          console.error('Forbidden: You don\'t have access to this job');
          break;
        case 404:
          console.error('Not Found: Job doesn\'t exist');
          break;
        case 429:
          console.error('Rate Limit Exceeded: Please wait before retrying');
          break;
        case 500:
          console.error('Server Error:', error.detail);
          break;
        default:
          console.error(`HTTP Error ${response.status}:`, error.detail);
      }
      
      return null;
    }

    return await response.json();
    
  } catch (error) {
    console.error('Request failed:', error.message);
    return null;
  }
}
```

---

## Celery Task Integration

### Task Architecture

The API dispatches tasks to Celery workers for distributed processing:

```
API Endpoint → Service Layer → Celery Task Dispatch → Redis Broker → Celery Workers
                                                                            ↓
                                                                    Task Execution
                                                                            ↓
                                                                    Result Callback
                                                                            ↓
                                                                    Database Update
```

### Task Types

#### 1. Download Tasks

Dispatched when starting a crawl job:

```python
# Task dispatch (internal)
from builder.tasks import download_images_task

task = download_images_task.delay(
    keyword="laptop",
    engine="google",
    max_images=100,
    job_id=123
)
```

**Task ID Format:** `uuid4` (e.g., `550e8400-e29b-41d4-a716-446655440000`)

**Rate Limit:** 10 tasks per minute per engine

#### 2. Validation Tasks

Dispatched when validating images:

```python
# Task dispatch (internal)
from validator.tasks import validate_image_medium_task

task = validate_image_medium_task.delay(
    image_id=456,
    job_id=123
)
```

**Task ID Format:** `task_{job_id}_{index}` (e.g., `task_123_0`)

**Rate Limits:**
- Fast: 1000 tasks per minute
- Medium: 500 tasks per minute
- Slow: 100 tasks per minute

### Chunk-Based Processing

Jobs are divided into chunks for parallel processing:

```
Total Chunks = Number of Keywords × Number of Engines

Example:
- Keywords: ["laptop", "computer", "notebook"] (3)
- Engines: ["google", "bing"] (2)
- Total Chunks: 3 × 2 = 6
```

Each chunk is processed by a separate Celery task.

### Progress Tracking

Progress is calculated based on completed chunks:

```
Progress = (completed_chunks / total_chunks) × 100

Example:
- Total Chunks: 10
- Completed Chunks: 7
- Failed Chunks: 1
- Active Chunks: 2
- Progress: (7 / 10) × 100 = 70%
```

### Task States

| State | Description |
|-------|-------------|
| `pending` | Task queued but not started |
| `running` | Task currently executing |
| `completed` | Task finished successfully |
| `failed` | Task failed with error |
| `cancelled` | Task revoked before completion |

### Monitoring Tasks

#### Check Celery Worker Status

```bash
# List active workers
celery -A celery_core.app inspect active

# Check task stats
celery -A celery_core.app inspect stats

# Monitor with Flower (if installed)
celery -A celery_core.app flower
```

#### Task Revocation

When a job is cancelled, all associated tasks are revoked:

```python
# Internal implementation
from celery_core.app import app

for task_id in job.task_ids:
    app.control.revoke(task_id, terminate=True)
```

### Best Practices

1. **Polling Interval**: Poll progress every 5-10 seconds to avoid overwhelming the API
2. **Timeout Handling**: Set reasonable timeouts for API requests (30-60 seconds)
3. **Error Retry**: Implement exponential backoff for failed requests
4. **Rate Limiting**: Respect rate limits to avoid 429 errors
5. **Task Monitoring**: Use the progress endpoint to track long-running jobs

### Complete Workflow Example

```python
import requests
import time

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "your_jwt_token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def complete_crawl_workflow(job_id):
    """Complete workflow: start → monitor → validate."""
    
    # 1. Start the job
    print("Starting crawl job...")
    response = requests.post(f"{BASE_URL}/jobs/{job_id}/start", headers=headers)
    if response.status_code != 200:
        print(f"Failed to start job: {response.json()}")
        return
    
    start_result = response.json()
    print(f"Job started with {start_result['total_chunks']} chunks")
    
    # 2. Monitor progress
    print("\nMonitoring progress...")
    while True:
        response = requests.get(f"{BASE_URL}/jobs/{job_id}/progress", headers=headers)
        if response.status_code != 200:
            print(f"Failed to get progress: {response.json()}")
            break
        
        progress = response.json()
        print(f"Progress: {progress['progress']}% | "
              f"Status: {progress['status']} | "
              f"Images: {progress['downloaded_images']}")
        
        if progress['status'] in ['completed', 'failed', 'cancelled']:
            print(f"\nJob finished with status: {progress['status']}")
            break
        
        time.sleep(5)
    
    # 3. Validate images (if job completed successfully)
    if progress['status'] == 'completed':
        print("\nStarting image validation...")
        response = requests.post(
            f"{BASE_URL}/validation/job/{job_id}/",
            headers=headers,
            json={"level": "medium"}
        )
        
        if response.status_code == 200:
            validation = response.json()
            print(f"Validation started for {validation['images_count']} images")
        else:
            print(f"Failed to start validation: {response.json()}")

# Usage
complete_crawl_workflow(123)
```

---

## Additional Resources

- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **GitHub Repository**: https://github.com/alaamer12/pixcrawler
- **Support**: support@pixcrawler.com

---

## Changelog

### Version 1.0.0 (2024-01-01)

- Initial release with Celery integration
- Start/stop crawl job endpoints
- Progress tracking with chunk statistics
- Image validation endpoints
- Comprehensive error handling
- Rate limiting support
