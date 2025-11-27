# Job Chunking Service - Integration Guide

## Quick Start

### 1. Import the Service

```python
from backend.services.job_chunking import JobChunkingService
from backend.repositories import JobChunkRepository, CrawlJobRepository
```

### 2. Initialize in Your Code

```python
# In your API route or task
chunk_repo = JobChunkRepository(session)
job_repo = CrawlJobRepository(session)
service = JobChunkingService(chunk_repo, job_repo, session)
```

### 3. Use in Existing Services

```python
# In CrawlJobService or other services
class CrawlJobService(BaseService):
    def __init__(self, ..., chunk_repo: JobChunkRepository, job_repo: CrawlJobRepository):
        self.chunking_service = JobChunkingService(chunk_repo, job_repo, session)
    
    async def create_and_chunk_job(self, ...):
        # Create job
        job = await self.crawl_job_repo.create(...)
        
        # Create chunks
        chunks = await self.chunking_service.create_chunks_for_job(
            job_id=job.id,
            max_images=job.max_images,
            priority=5
        )
        
        return job, chunks
```

## Integration Points

### With API Routes

```python
# In backend/api/routes/crawl_jobs.py
from fastapi import APIRouter, Depends
from backend.services.job_chunking import JobChunkingService

router = APIRouter()

@router.post("/jobs/{job_id}/chunks")
async def create_chunks(
    job_id: int,
    max_images: int,
    priority: int = 5,
    service: JobChunkingService = Depends(get_chunking_service)
):
    chunks = await service.create_chunks_for_job(
        job_id=job_id,
        max_images=max_images,
        priority=priority
    )
    return {"chunks": chunks}

@router.get("/jobs/{job_id}/chunks/progress")
async def get_progress(
    job_id: int,
    service: JobChunkingService = Depends(get_chunking_service)
):
    progress = await service.get_job_chunk_progress(job_id=job_id)
    return progress
```

### With Celery Tasks

```python
# In backend/tasks.py or celery_core/tasks.py
from celery import shared_task
from backend.services.job_chunking import JobChunkingService

@shared_task
def process_chunk(chunk_id: int, job_id: int):
    """Process a single chunk."""
    session = AsyncSessionLocal()
    try:
        chunk_repo = JobChunkRepository(session)
        job_repo = CrawlJobRepository(session)
        service = JobChunkingService(chunk_repo, job_repo, session)
        
        # Mark as processing
        await service.mark_chunk_processing(
            chunk_id=chunk_id,
            task_id=process_chunk.request.id
        )
        
        # Process chunk...
        # Get chunk to process
        chunk = await service.get_chunk_by_id(chunk_id)
        start = chunk.image_range['start']
        end = chunk.image_range['end']
        
        # Do processing...
        
        # Mark as completed
        await service.mark_chunk_completed(chunk_id=chunk_id)
        
    except Exception as e:
        await service.mark_chunk_failed(
            chunk_id=chunk_id,
            error_message=str(e)
        )
        raise
    finally:
        session.close()
```

### With Dependency Injection

```python
# In backend/core/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.job_chunking import JobChunkingService
from backend.repositories import JobChunkRepository, CrawlJobRepository
from backend.database.connection import get_session

async def get_chunking_service(
    session: AsyncSession = Depends(get_session)
) -> JobChunkingService:
    chunk_repo = JobChunkRepository(session)
    job_repo = CrawlJobRepository(session)
    return JobChunkingService(chunk_repo, job_repo, session)
```

## Common Workflows

### Workflow 1: Create Job with Chunks

```python
async def create_job_with_chunks(
    project_id: int,
    name: str,
    keywords: List[str],
    max_images: int,
    service: JobChunkingService,
    job_service: CrawlJobService
):
    # Create job
    job = await job_service.create_job(
        project_id=project_id,
        name=name,
        keywords=keywords,
        max_images=max_images
    )
    
    # Create chunks
    chunks = await service.create_chunks_for_job(
        job_id=job.id,
        max_images=max_images,
        priority=5
    )
    
    return {
        'job': job,
        'chunks': chunks,
        'total_chunks': len(chunks)
    }
```

### Workflow 2: Process Chunks

```python
async def process_job_chunks(
    job_id: int,
    service: JobChunkingService
):
    """Process all chunks for a job."""
    
    while True:
        # Get next pending chunk
        chunk = await service.get_next_pending_chunk(job_id=job_id)
        if not chunk:
            break
        
        # Mark as processing
        await service.mark_chunk_processing(chunk_id=chunk.id)
        
        try:
            # Process chunk
            start = chunk.image_range['start']
            end = chunk.image_range['end']
            
            # ... do processing ...
            
            # Mark as completed
            await service.mark_chunk_completed(chunk_id=chunk.id)
            
        except Exception as e:
            # Mark as failed
            await service.mark_chunk_failed(
                chunk_id=chunk.id,
                error_message=str(e)
            )
```

### Workflow 3: Monitor Progress

```python
async def monitor_job_progress(
    job_id: int,
    service: JobChunkingService
):
    """Monitor job progress and return updates."""
    
    while True:
        progress = await service.get_job_chunk_progress(job_id=job_id)
        
        print(f"Job {job_id} Progress:")
        print(f"  Total: {progress['total_chunks']}")
        print(f"  Completed: {progress['completed_chunks']}")
        print(f"  Failed: {progress['failed_chunks']}")
        print(f"  Percentage: {progress['completion_percentage']:.1f}%")
        
        if progress['is_complete']:
            break
        
        await asyncio.sleep(5)  # Check every 5 seconds
```

### Workflow 4: Handle Failures

```python
async def handle_failed_chunks(
    job_id: int,
    service: JobChunkingService,
    max_retries: int = 3
):
    """Retry failed chunks."""
    
    failed_chunks = await service.get_failed_chunks(job_id=job_id)
    
    for chunk in failed_chunks:
        if chunk.retry_count < max_retries:
            # Retry the chunk
            await service.retry_chunk(chunk_id=chunk.id)
            print(f"Retrying chunk {chunk.id} (attempt {chunk.retry_count + 1})")
        else:
            print(f"Chunk {chunk.id} exceeded max retries")
```

## Database Migration

If not already done, run migrations to create the `job_chunks` table:

```bash
# Using Alembic
alembic upgrade head
```

The migration should create:
- `job_chunks` table
- Foreign key to `crawl_jobs`
- All indexes
- Constraints

## Testing Integration

```python
# In your test file
import pytest
from backend.services.job_chunking import JobChunkingService

@pytest.mark.asyncio
async def test_integration_with_crawl_job(session):
    # Create job
    job = CrawlJob(
        project_id=1,
        name="Test",
        keywords={"keywords": ["test"]},
        max_images=1500
    )
    session.add(job)
    await session.commit()
    
    # Create service
    chunk_repo = JobChunkRepository(session)
    job_repo = CrawlJobRepository(session)
    service = JobChunkingService(chunk_repo, job_repo, session)
    
    # Create chunks
    chunks = await service.create_chunks_for_job(
        job_id=job.id,
        max_images=1500
    )
    
    assert len(chunks) == 3
    assert chunks[0].image_range['start'] == 0
    assert chunks[0].image_range['end'] == 499
```

## Configuration

### Chunk Size

To change chunk size, edit `backend/services/job_chunking.py`:

```python
CHUNK_SIZE = 1000  # Change from 500 to 1000
```

### Priority Range

To change priority range, edit the validation in `create_chunks_for_job()`:

```python
if priority < 0 or priority > 20:  # Change from 10 to 20
    raise ValidationError("priority must be between 0 and 20")
```

## Troubleshooting

### Issue: Chunks not created

**Solution**: Check that job exists and max_images > 0

```python
job = await job_repo.get_by_id(job_id)
assert job is not None
assert job.max_images > 0
```

### Issue: Status not updating

**Solution**: Ensure session is committed

```python
await service.mark_chunk_completed(chunk_id=chunk.id)
await session.commit()  # Don't forget!
```

### Issue: Performance slow

**Solution**: Check indexes are created

```sql
SELECT * FROM pg_indexes WHERE tablename = 'job_chunks';
```

## Best Practices

1. **Always use transactions**: Wrap chunk operations in transactions
2. **Handle errors gracefully**: Catch and log exceptions
3. **Monitor progress**: Periodically check job progress
4. **Retry failed chunks**: Implement retry logic
5. **Clean up**: Delete chunks when job is deleted
6. **Log operations**: Use service logging for debugging
7. **Test thoroughly**: Write tests for your integration

## Next Steps

1. Review the API documentation: `backend/JOB_CHUNKING_SERVICE.md`
2. Run the test suite: `pytest backend/tests/test_job_chunking_service.py`
3. Integrate into your API routes
4. Add to your Celery tasks
5. Monitor in production

## Support

For issues or questions:
1. Check the documentation: `backend/JOB_CHUNKING_SERVICE.md`
2. Review test examples: `backend/tests/test_job_chunking_service.py`
3. Check logs for errors
4. Review database constraints
