# Job Chunking Service

## Overview

The Job Chunking Service is a backend component that splits large crawl jobs into manageable 500-image chunks for distributed processing. It provides comprehensive chunk management, status tracking, and progress monitoring.

## Architecture

### Components

1. **JobChunkingService** (`backend/services/job_chunking.py`)
   - Main service for chunk operations
   - Handles chunk creation, status management, and progress tracking
   - Inherits from BaseService for logging and error handling

2. **JobChunkRepository** (`backend/repositories/job_chunk_repository.py`)
   - Data access layer for JobChunk model
   - Provides CRUD operations and specialized queries
   - Handles bulk operations and statistics

3. **JobChunk Model** (`backend/models/chunks.py`)
   - SQLAlchemy ORM model for job chunks
   - Tracks chunk metadata, status, and processing information
   - Supports Celery task ID tracking

4. **Schemas** (`backend/schemas/job_chunks.py`)
   - Pydantic models for request/response validation
   - JobChunkStatus enum for status management
   - Statistics schema for progress tracking

## Core Functionality

### Chunk Size

- **Chunk Size**: 500 images per chunk
- **Configurable**: Set via `CHUNK_SIZE` constant in `job_chunking.py`

### Status Tracking

Chunks support four statuses:

- **PENDING**: Chunk waiting to be processed
- **PROCESSING**: Chunk currently being processed
- **COMPLETED**: Chunk successfully completed
- **FAILED**: Chunk failed during processing

### Priority System

- **Range**: 0-10 (higher = more urgent)
- **Inheritance**: Chunks inherit priority from parent job
- **Default**: 5 (medium priority)

## API Reference

### Creating Chunks

```python
chunks = await service.create_chunks_for_job(
    job_id=1,
    max_images=2500,
    priority=7
)
```

**Parameters:**
- `job_id` (int): Parent job ID
- `max_images` (int): Total images for the job
- `priority` (int): Priority level (0-10)

**Returns:** List of created JobChunk records

**Example:**
- 2500 images → 5 chunks (0-499, 500-999, 1000-1499, 1500-1999, 2000-2499)
- 250 images → 1 chunk (0-249)
- 1000 images → 2 chunks (0-499, 500-999)

### Status Management

#### Mark as Processing
```python
chunk = await service.mark_chunk_processing(
    chunk_id=1,
    task_id="celery-task-id"
)
```

#### Mark as Completed
```python
chunk = await service.mark_chunk_completed(chunk_id=1)
```

#### Mark as Failed
```python
chunk = await service.mark_chunk_failed(
    chunk_id=1,
    error_message="Connection timeout"
)
```

#### Retry Failed Chunk
```python
chunk = await service.retry_chunk(chunk_id=1)
```

### Progress Tracking

#### Get Statistics
```python
stats = await service.get_chunk_statistics(job_id=1)
# Returns: JobChunkStatistics with counts by status
```

#### Get Progress Details
```python
progress = await service.get_job_chunk_progress(job_id=1)
# Returns: {
#   'job_id': 1,
#   'total_chunks': 5,
#   'pending_chunks': 2,
#   'processing_chunks': 1,
#   'completed_chunks': 2,
#   'failed_chunks': 0,
#   'completion_percentage': 40.0,
#   'is_complete': False,
#   'timestamp': '2024-01-15T10:30:00'
# }
```

#### Check Job Completion
```python
is_complete = await service.check_job_completion(job_id=1)
```

### Querying Chunks

#### Get All Chunks for Job
```python
chunks = await service.get_chunks_for_job(job_id=1)
```

#### Get Chunks by Status
```python
pending = await service.get_pending_chunks(job_id=1)
processing = await service.get_processing_chunks(job_id=1)
completed = await service.get_completed_chunks(job_id=1)
failed = await service.get_failed_chunks(job_id=1)
```

#### Get Next Pending Chunk
```python
next_chunk = await service.get_next_pending_chunk(job_id=1)
# Returns highest priority pending chunk
```

## Database Schema

### job_chunks Table

```sql
CREATE TABLE job_chunks (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES crawl_jobs(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    priority INTEGER NOT NULL DEFAULT 5,
    image_range JSONB NOT NULL,
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    task_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT ck_job_chunks_status_valid 
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    CONSTRAINT ck_job_chunks_priority_range 
        CHECK (priority >= 0 AND priority <= 10),
    CONSTRAINT ck_job_chunks_retry_count_positive 
        CHECK (retry_count >= 0),
    
    INDEX ix_job_chunks_job_id (job_id),
    INDEX ix_job_chunks_status (status),
    INDEX ix_job_chunks_job_status (job_id, status),
    INDEX ix_job_chunks_priority_created (priority, created_at),
    INDEX ix_job_chunks_task_id (task_id)
);
```

## Integration with CrawlJob

The JobChunkingService integrates with CrawlJob through the ChunkTrackingMixin:

```python
class CrawlJob(Base, TimestampMixin, ChunkTrackingMixin):
    # Mixin provides:
    total_chunks: int          # Total chunks for this job
    active_chunks: int         # Currently processing chunks
    completed_chunks: int      # Successfully completed chunks
    failed_chunks: int         # Failed chunks
    task_ids: list            # Celery task IDs
```

### Updating Job Chunk Tracking

```python
job = await service.update_job_chunk_tracking(
    job_id=1,
    active_delta=-1,           # Decrease active by 1
    completed_delta=1,         # Increase completed by 1
    failed_delta=0
)
```

## Usage Examples

### Complete Workflow

```python
# 1. Create chunks for a job
chunks = await service.create_chunks_for_job(
    job_id=1,
    max_images=2500,
    priority=7
)

# 2. Get next pending chunk
chunk = await service.get_next_pending_chunk(job_id=1)

# 3. Mark as processing
await service.mark_chunk_processing(
    chunk_id=chunk.id,
    task_id="celery-task-123"
)

# 4. Process chunk...

# 5. Mark as completed
await service.mark_chunk_completed(chunk_id=chunk.id)

# 6. Update job tracking
await service.update_job_chunk_tracking(
    job_id=1,
    active_delta=-1,
    completed_delta=1
)

# 7. Check if job is complete
is_complete = await service.check_job_completion(job_id=1)

# 8. Get progress
progress = await service.get_job_chunk_progress(job_id=1)
```

### Error Handling

```python
try:
    chunks = await service.create_chunks_for_job(
        job_id=999,
        max_images=1000
    )
except NotFoundError:
    # Handle job not found
    pass
except ValidationError as e:
    # Handle validation errors (invalid max_images, priority)
    print(f"Validation error: {e}")
```

## Testing

Run tests with pytest:

```bash
pytest backend/tests/test_job_chunking_service.py -v
```

### Test Coverage

- Chunk creation with various sizes
- Single chunk creation (< 500 images)
- Multiple chunk creation (> 500 images)
- Exact boundary cases (1000, 1500, 2000 images)
- Status management (pending, processing, completed, failed)
- Retry logic
- Statistics and progress tracking
- Error handling and validation

## Performance Considerations

### Indexing

The job_chunks table includes strategic indexes:

- `ix_job_chunks_job_id`: Fast lookup by job
- `ix_job_chunks_status`: Fast filtering by status
- `ix_job_chunks_job_status`: Combined index for job + status queries
- `ix_job_chunks_priority_created`: Priority-based ordering
- `ix_job_chunks_task_id`: Celery task tracking

### Bulk Operations

Use `bulk_create()` for creating multiple chunks:

```python
chunks = await chunk_repo.bulk_create(chunks_data)
```

This is more efficient than creating chunks individually.

### Statistics Caching

For frequently accessed statistics, consider caching:

```python
stats = await service.get_chunk_statistics(job_id=1)
# Cache for 30 seconds
```

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| NotFoundError | Job doesn't exist | Verify job_id exists |
| ValidationError | Invalid max_images or priority | Check input ranges |
| ValidationError | Invalid status | Use JobChunkStatus enum |
| DatabaseError | Constraint violation | Check data integrity |

## Future Enhancements

1. **Chunk Retry Policy**: Configurable max retries per chunk
2. **Chunk Timeout**: Automatic failure after timeout
3. **Chunk Rebalancing**: Redistribute failed chunks
4. **Chunk Prioritization**: Dynamic priority adjustment
5. **Chunk Metrics**: Performance metrics per chunk
6. **Chunk Caching**: Cache frequently accessed chunks

## Related Components

- **CrawlJobService**: Parent service for job management
- **CrawlJob Model**: Parent job model
- **Celery Tasks**: Chunk processing tasks
- **ActivityLog**: Audit trail for chunk operations

## Configuration

### Chunk Size

Edit `CHUNK_SIZE` in `backend/services/job_chunking.py`:

```python
CHUNK_SIZE = 500  # Change to desired size
```

### Priority Range

Modify priority validation in `JobChunkingService.create_chunks_for_job()`:

```python
if priority < 0 or priority > 10:  # Adjust range
    raise ValidationError("priority must be between 0 and 10")
```

## Troubleshooting

### Chunks Not Created

1. Verify job exists: `await job_repo.get_by_id(job_id)`
2. Check max_images > 0
3. Verify database connection
4. Check logs for exceptions

### Status Updates Not Persisting

1. Ensure session is committed
2. Check database constraints
3. Verify chunk_id exists
4. Check for concurrent updates

### Performance Issues

1. Check indexes are created
2. Monitor query performance
3. Consider pagination for large result sets
4. Use bulk operations for multiple creates
