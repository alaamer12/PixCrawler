# Chunk Orchestration Guide for PixCrawler

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Hybrid Chunk Tracking](#hybrid-chunk-tracking)
4. [Configuration](#configuration)
5. [Usage Examples](#usage-examples)
6. [API Integration](#api-integration)
7. [Monitoring & Debugging](#monitoring--debugging)
8. [Troubleshooting](#troubleshooting)

---

## Overview

PixCrawler uses a **hybrid chunk orchestration** system that combines:
- **Celery tasks** for distributed processing
- **Database tracking** for job state
- **Configuration-based limits** for capacity management

### Key Concepts

**Processing Chunks**: Temporary work units (500 images each) executed by Celery workers
**Storage Chunks**: Permanent dataset files saved to Blob Storage (separate concern)
**Hybrid Tracking**: Simple counters in database + Celery task IDs for detailed queries

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│ USER REQUEST                                        │
│ "Download 2000 cat images"                          │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 1. CREATE JOB (FastAPI Endpoint)                    │
│    CrawlJob(id=123, max_images=2000, status="pending") │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 2. CHUNK ORCHESTRATOR                               │
│    - Calculate chunks: 2000 / 500 = 4 chunks        │
│    - Check capacity: 35 max, 25 active = 10 available │
│    - Split job into 4 processing chunks             │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 3. QUEUE TO CELERY                                  │
│    Task 1: Download images 0-499   → task_abc123   │
│    Task 2: Download images 500-999 → task_def456   │
│    Task 3: Download images 1000-1499 → task_ghi789 │
│    Task 4: Download images 1500-1999 → task_jkl012 │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 4. UPDATE DATABASE                                  │
│    job.status = "running"                           │
│    job.total_chunks = 4                             │
│    job.active_chunks = 4                            │
│    job.task_ids = ["abc123", "def456", ...]         │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 5. CELERY WORKERS PROCESS (Parallel)               │
│    Worker 1: Chunk 1 → Download 500 images         │
│    Worker 2: Chunk 2 → Download 500 images         │
│    Worker 3: Chunk 3 → Download 500 images         │
│    Worker 4: Chunk 4 → Download 500 images         │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 6. CHUNK COMPLETION CALLBACKS                       │
│    on_chunk_complete(job_id=123, task_id="abc123")  │
│    - job.active_chunks -= 1                         │
│    - job.completed_chunks += 1                      │
│    - Update progress                                │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 7. JOB COMPLETION                                   │
│    When all_chunks_completed:                       │
│    - Validate images                                │
│    - Upload to Blob Storage                         │
│    - Generate metadata                              │
│    - job.status = "completed"                       │
└─────────────────────────────────────────────────────┘
```

---

## Hybrid Chunk Tracking

### Database Fields (CrawlJob Model)

```python
class CrawlJob(Base):
    # Original fields
    id: int
    project_id: int
    max_images: int
    status: str  # pending, running, completed, failed
    
    # Hybrid chunk tracking
    total_chunks: int = 0        # Total chunks for this job
    active_chunks: int = 0       # Currently processing
    completed_chunks: int = 0    # Successfully completed
    failed_chunks: int = 0       # Failed chunks
    task_ids: list[str] = []     # Celery task IDs
    
    @property
    def chunk_progress(self) -> float:
        """Returns 0-100 progress based on chunks."""
        return (completed_chunks / total_chunks * 100) if total_chunks > 0 else 0
```

### Why This Approach?

**✅ Advantages:**
- No separate ProcessingChunk table needed
- Simple to query and update
- Celery handles task distribution
- Database tracks high-level state
- Can query Celery for detailed task status

**❌ What We DON'T Do:**
- Create a separate chunk table (unnecessary)
- Use psutil for runtime metrics (unreliable on cloud)
- Store full task results in database (Celery handles this)

---

## Configuration

### Environment Variables

```bash
# .env.local (Development)
PIXCRAWLER_RESOURCE_ENVIRONMENT=local
PIXCRAWLER_RESOURCE_MAX_CONCURRENT_CHUNKS=35
PIXCRAWLER_RESOURCE_MAX_TEMP_STORAGE_MB=20000  # 20GB
PIXCRAWLER_RESOURCE_CHUNK_SIZE_IMAGES=500
PIXCRAWLER_RESOURCE_ESTIMATED_IMAGE_SIZE_MB=0.5

# .env.azure (Production)
PIXCRAWLER_RESOURCE_ENVIRONMENT=azure
PIXCRAWLER_RESOURCE_MAX_CONCURRENT_CHUNKS=35
PIXCRAWLER_RESOURCE_MAX_TEMP_STORAGE_MB=8000   # 8GB (safe margin from 10GB limit)
PIXCRAWLER_RESOURCE_CHUNK_SIZE_IMAGES=500
PIXCRAWLER_RESOURCE_ESTIMATED_IMAGE_SIZE_MB=0.5
```

### ResourceSettings

```python
from backend.core.settings.resources import get_resource_settings

settings = get_resource_settings()
print(settings.effective_max_chunks)  # 35
print(settings.chunk_size_images)     # 500
print(settings.max_temp_storage_mb)   # 8000
```

---

## Usage Examples

### 1. Start a Job (Orchestrator)

```python
from backend.services.chunk_orchestrator import ChunkOrchestrator

# In your endpoint
orchestrator = ChunkOrchestrator(session)

result = await orchestrator.start_job(
    job_id=123,
    sources=["google", "bing"]
)

if result['success']:
    print(f"Started {result['total_chunks']} chunks")
    print(f"Task IDs: {result['task_ids']}")
else:
    print(f"Error: {result['error']}")
```

### 2. Check Capacity

```python
from backend.services.resource_monitor import ResourceMonitor

monitor = ResourceMonitor(session)

# Check if we can start 5 chunks
can_start = await monitor.can_start_chunk(required_chunks=5)

if can_start:
    # Start chunks
    pass
else:
    available = await monitor.get_available_capacity()
    print(f"Only {available} slots available")
```

### 3. Get Capacity Info

```python
info = await monitor.get_capacity_info()
print(info)
# {
#     'active_chunks': 25,
#     'max_chunks': 35,
#     'available': 10,
#     'utilization': 71.4,
#     'environment': 'azure'
# }
```

### 4. Handle Chunk Completion

```python
# Called by Celery task on completion
await orchestrator.on_chunk_complete(
    job_id=123,
    task_id="task_abc123",
    success=True
)
```

### 5. Query Celery for Task Status

```python
from celery_core.app import get_celery_app

app = get_celery_app()
inspect = app.control.inspect()

# Get active tasks
active = inspect.active()
# {'worker1': [{'id': 'task_abc123', 'name': 'builder.download_google'}]}

# Get task result
result = app.AsyncResult('task_abc123')
print(result.state)  # PENDING, STARTED, SUCCESS, FAILURE
print(result.result)  # Task return value
```

---

## API Integration

### Endpoint: Start Job

```python
# backend/api/v1/endpoints/crawl_jobs.py

@router.post("/{job_id}/start")
async def start_crawl_job(
    job_id: int,
    sources: list[str],
    current_user: CurrentUser,
    session: DBSession,
) -> dict:
    """Start a crawl job by splitting into chunks."""
    
    orchestrator = ChunkOrchestrator(session)
    result = await orchestrator.start_job(job_id, sources)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result
```

### Endpoint: Get Job Progress

```python
@router.get("/{job_id}/progress")
async def get_job_progress(
    job_id: int,
    current_user: CurrentUser,
    session: DBSession,
) -> dict:
    """Get job progress including chunk status."""
    
    job = await session.get(CrawlJob, job_id)
    
    return {
        'job_id': job.id,
        'status': job.status,
        'progress': job.progress,
        'chunk_progress': job.chunk_progress,
        'total_chunks': job.total_chunks,
        'active_chunks': job.active_chunks,
        'completed_chunks': job.completed_chunks,
        'failed_chunks': job.failed_chunks,
    }
```

---

## Monitoring & Debugging

### 1. Check Active Chunks

```python
# Get total active chunks across all jobs
monitor = ResourceMonitor(session)
active = await monitor.get_active_chunk_count()
print(f"Active chunks: {active}")
```

### 2. Query Specific Job

```python
# Get chunks for specific job
job_chunks = await monitor.get_job_active_chunks(job_id=123)
print(f"Job 123 has {job_chunks} active chunks")
```

### 3. Celery Flower (Web UI)

```bash
# Install Flower
uv add flower --optional monitoring

# Start Flower
celery -A celery_core flower --port=5555

# Open browser: http://localhost:5555
```

### 4. Check Celery Task Status

```python
# Get task info
app = get_celery_app()
task = app.AsyncResult('task_abc123')

print(f"State: {task.state}")
print(f"Result: {task.result}")
print(f"Traceback: {task.traceback}")
```

---

## Troubleshooting

### Problem: "Insufficient capacity" error

**Cause**: Too many active chunks

**Solution**:
```python
# Check capacity
info = await monitor.get_capacity_info()
print(f"Active: {info['active_chunks']}/{info['max_chunks']}")

# Wait for capacity or increase limit
# Option 1: Wait for chunks to complete
# Option 2: Increase PIXCRAWLER_RESOURCE_MAX_CONCURRENT_CHUNKS
```

### Problem: Chunks stuck in "active" state

**Cause**: Worker crashed or task failed without callback

**Solution**:
```python
# Query Celery for actual task state
app = get_celery_app()
for task_id in job.task_ids:
    result = app.AsyncResult(task_id)
    if result.state in ['SUCCESS', 'FAILURE']:
        # Update database manually
        await orchestrator.on_chunk_complete(
            job_id=job.id,
            task_id=task_id,
            success=(result.state == 'SUCCESS')
        )
```

### Problem: Job never completes

**Cause**: Chunk counters out of sync

**Solution**:
```python
# Reconcile with Celery
app = get_celery_app()
completed = 0
failed = 0

for task_id in job.task_ids:
    result = app.AsyncResult(task_id)
    if result.state == 'SUCCESS':
        completed += 1
    elif result.state == 'FAILURE':
        failed += 1

# Update job
job.completed_chunks = completed
job.failed_chunks = failed
job.active_chunks = job.total_chunks - completed - failed
await session.commit()
```

---

## Best Practices

1. **Always check capacity** before starting jobs
2. **Use callbacks** to update chunk status
3. **Monitor Celery** with Flower in production
4. **Set conservative limits** (use safety margins)
5. **Log chunk events** for debugging
6. **Handle failures gracefully** with retries
7. **Clean up temp storage** after job completion

---

## Related Documentation

- [Tech Stack & Orchestration Tools Guide](./Tech%20Stack%20&%20Orchestration%20Tools%20Guide%2029e461aa27058042a9aee549be105c22.md)
- [Logging Strategy & Azure Monitor Guide](./Logging%20Strategy%20&%20Azure%20Monitor%20Guide%2029e461aa27058005b792d1592d3b79c0.md)
- [Azure Monitoring Guide](./Azure%20Monitoring%20Guide%20for%20Cloud%20Applications%2029e461aa270580c0b2d3e114f97287d2.md)
