# Job Chunking Service - Quick Reference

## Import

```python
from backend.services.job_chunking import JobChunkingService
from backend.repositories import JobChunkRepository, CrawlJobRepository
from backend.schemas.job_chunks import JobChunkStatus
```

## Initialize

```python
chunk_repo = JobChunkRepository(session)
job_repo = CrawlJobRepository(session)
service = JobChunkingService(chunk_repo, job_repo, session)
```

## Create Chunks

```python
chunks = await service.create_chunks_for_job(
    job_id=1,
    max_images=2500,
    priority=7
)
# Returns: 5 chunks (2500 / 500)
```

## Status Management

```python
# Mark as processing
await service.mark_chunk_processing(chunk_id=1, task_id="task-123")

# Mark as completed
await service.mark_chunk_completed(chunk_id=1)

# Mark as failed
await service.mark_chunk_failed(chunk_id=1, error_message="Timeout")

# Retry failed chunk
await service.retry_chunk(chunk_id=1)
```

## Get Chunks

```python
# All chunks for job
chunks = await service.get_chunks_for_job(job_id=1)

# By status
pending = await service.get_pending_chunks(job_id=1)
processing = await service.get_processing_chunks(job_id=1)
completed = await service.get_completed_chunks(job_id=1)
failed = await service.get_failed_chunks(job_id=1)

# Next to process (by priority)
chunk = await service.get_next_pending_chunk(job_id=1)

# Single chunk
chunk = await service.get_chunk_by_id(chunk_id=1)
```

## Progress Tracking

```python
# Statistics
stats = await service.get_chunk_statistics(job_id=1)
# Returns: total, pending, processing, completed, failed

# Detailed progress
progress = await service.get_job_chunk_progress(job_id=1)
# Returns: completion_percentage, success_rate, is_complete, etc.

# Check if complete
is_complete = await service.check_job_completion(job_id=1)
```

## Status Enum

```python
JobChunkStatus.PENDING      # "pending"
JobChunkStatus.PROCESSING   # "processing"
JobChunkStatus.COMPLETED    # "completed"
JobChunkStatus.FAILED       # "failed"
```

## Chunk Structure

```python
chunk = {
    'id': 1,
    'job_id': 1,
    'chunk_index': 0,
    'status': 'pending',
    'priority': 5,
    'image_range': {'start': 0, 'end': 499},
    'error_message': None,
    'retry_count': 0,
    'task_id': None,
    'created_at': datetime,
    'updated_at': datetime,
}
```

## Statistics Structure

```python
stats = {
    'job_id': 1,
    'total': 5,
    'pending': 2,
    'processing': 1,
    'completed': 2,
    'failed': 0,
    'completion_percentage': 40.0,
    'success_rate': 40.0,
}
```

## Progress Structure

```python
progress = {
    'job_id': 1,
    'total_chunks': 5,
    'pending_chunks': 2,
    'processing_chunks': 1,
    'completed_chunks': 2,
    'failed_chunks': 0,
    'completion_percentage': 40.0,
    'success_rate': 40.0,
    'is_complete': False,
    'timestamp': '2024-01-15T10:30:00',
}
```

## Common Patterns

### Process All Chunks

```python
while True:
    chunk = await service.get_next_pending_chunk(job_id=1)
    if not chunk:
        break
    
    await service.mark_chunk_processing(chunk_id=chunk.id)
    try:
        # Process chunk
        await service.mark_chunk_completed(chunk_id=chunk.id)
    except Exception as e:
        await service.mark_chunk_failed(chunk_id=chunk.id, error_message=str(e))
```

### Monitor Progress

```python
while True:
    progress = await service.get_job_chunk_progress(job_id=1)
    print(f"Progress: {progress['completion_percentage']:.1f}%")
    
    if progress['is_complete']:
        break
    
    await asyncio.sleep(5)
```

### Retry Failed Chunks

```python
failed = await service.get_failed_chunks(job_id=1)
for chunk in failed:
    if chunk.retry_count < 3:
        await service.retry_chunk(chunk_id=chunk.id)
```

## Error Handling

```python
from backend.core.exceptions import NotFoundError, ValidationError

try:
    chunks = await service.create_chunks_for_job(job_id=1, max_images=1000)
except NotFoundError:
    print("Job not found")
except ValidationError as e:
    print(f"Invalid input: {e}")
```

## Configuration

### Chunk Size
Edit `backend/services/job_chunking.py`:
```python
CHUNK_SIZE = 500  # Change to desired size
```

### Priority Range
Edit `backend/services/job_chunking.py`:
```python
if priority < 0 or priority > 10:  # Adjust range
    raise ValidationError("priority must be between 0 and 10")
```

## Database

### Table: job_chunks
- id: PRIMARY KEY
- job_id: FOREIGN KEY → crawl_jobs
- chunk_index: INTEGER
- status: VARCHAR(20) - pending, processing, completed, failed
- priority: INTEGER (0-10)
- image_range: JSONB - {"start": int, "end": int}
- error_message: TEXT
- retry_count: INTEGER
- task_id: VARCHAR(255)
- created_at: TIMESTAMP
- updated_at: TIMESTAMP

### Indexes
- ix_job_chunks_job_id
- ix_job_chunks_status
- ix_job_chunks_job_status
- ix_job_chunks_priority_created
- ix_job_chunks_task_id

## Testing

```bash
# Run all tests
pytest backend/tests/test_job_chunking_service.py -v

# Run specific test
pytest backend/tests/test_job_chunking_service.py::TestJobChunkingService::test_create_chunks_for_job_multiple_chunks -v

# Run with coverage
pytest backend/tests/test_job_chunking_service.py --cov=backend.services.job_chunking
```

## Files

- **Service**: `backend/services/job_chunking.py`
- **Repository**: `backend/repositories/job_chunk_repository.py`
- **Schemas**: `backend/schemas/job_chunks.py`
- **Model**: `backend/models/chunks.py`
- **Tests**: `backend/tests/test_job_chunking_service.py`
- **Docs**: `backend/JOB_CHUNKING_SERVICE.md`

## Examples

### Example 1: Create and Process Job

```python
# Create chunks
chunks = await service.create_chunks_for_job(
    job_id=1,
    max_images=2500,
    priority=7
)

# Process each chunk
for chunk in chunks:
    await service.mark_chunk_processing(chunk_id=chunk.id)
    # ... process chunk ...
    await service.mark_chunk_completed(chunk_id=chunk.id)

# Check completion
is_complete = await service.check_job_completion(job_id=1)
```

### Example 2: Get Job Progress

```python
progress = await service.get_job_chunk_progress(job_id=1)

print(f"Job {progress['job_id']}:")
print(f"  Total: {progress['total_chunks']}")
print(f"  Completed: {progress['completed_chunks']}")
print(f"  Failed: {progress['failed_chunks']}")
print(f"  Progress: {progress['completion_percentage']:.1f}%")
```

### Example 3: Handle Failures

```python
# Get failed chunks
failed = await service.get_failed_chunks(job_id=1)

# Retry each failed chunk
for chunk in failed:
    if chunk.retry_count < 3:
        await service.retry_chunk(chunk_id=chunk.id)
        print(f"Retrying chunk {chunk.id}")
    else:
        print(f"Chunk {chunk.id} exceeded max retries")
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Chunks not created | Check job exists and max_images > 0 |
| Status not updating | Ensure session.commit() is called |
| Slow queries | Check database indexes are created |
| Job not found | Verify job_id exists in database |
| Invalid priority | Use 0-10 range |
| Invalid status | Use JobChunkStatus enum |

## Support

- API Docs: `backend/JOB_CHUNKING_SERVICE.md`
- Integration: `INTEGRATION_GUIDE.md`
- Examples: `backend/tests/test_job_chunking_service.py`
