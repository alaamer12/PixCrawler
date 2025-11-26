# Design Document: Checkpoint Management System

## Overview

This document describes the design for a batch-based checkpoint management system that enables resumability for PixCrawler crawl jobs. The system integrates with Celery tasks, chunk orchestration, and tracks comprehensive metadata including keywords, search engine offsets, variations, and download statistics.

## Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                     Job Checkpoint                          │
│  - job_id, keywords, max_images, project_id                │
│  - total_chunks, active_chunks, completed_chunks            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ├─────────────────────────────────┐
                            │                                 │
                            ▼                                 ▼
┌──────────────────────────────────┐  ┌──────────────────────────────────┐
│    Chunk Batch Checkpoint #1     │  │    Chunk Batch Checkpoint #2     │
│  - task_id, chunk_index          │  │  - task_id, chunk_index          │
│  - keyword, engines_queue        │  │  - keyword, engines_queue        │
│  - target_images, worker_metadata│  │  - target_images, worker_metadata│
└──────────────────────────────────┘  └──────────────────────────────────┘
                │                                     │
                ├──────────────┬──────────────┐      │
                ▼              ▼              ▼      ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │ Engine Batch    │ │ Engine Batch    │ │ Engine Batch    │
    │ (Google)        │ │ (Bing)          │ │ (Baidu)         │
    │ - variations    │ │ - variations    │ │ - variations    │
    │ - offset_ranges │ │ - offset_ranges │ │ - offset_ranges │
    └─────────────────┘ └─────────────────┘ └─────────────────┘
            │                   │                   │
            ▼                   ▼                   ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │ Download Batch  │ │ Download Batch  │ │ Download Batch  │
    │ - urls_list     │ │ - urls_list     │ │ - urls_list     │
    │ - attempts      │ │ - attempts      │ │ - attempts      │
    │ - results       │ │ - results       │ │ - results       │
    └─────────────────┘ └─────────────────┘ └─────────────────┘
```



### Dual Persistence Strategy

**Design Rationale**: The dual-layer approach balances performance (Redis) with durability (PostgreSQL). Redis provides sub-100ms reads for active jobs while PostgreSQL ensures data survives system restarts and enables historical analytics.

**Redis (Fast Access Layer)**
- TTL: 24 hours for active checkpoints, 1 hour for completed, 7 days for failed
- Purpose: Real-time progress queries, active job tracking, worker coordination
- Key Pattern: `checkpoint:{job_id}:{chunk_id}:{type}`
- Compression: Enabled for batches >100KB using zstandard
- Fallback: Automatic PostgreSQL fallback if Redis unavailable

**PostgreSQL (Durability Layer)**
- Purpose: Long-term storage, recovery, analytics, audit trail
- Tables: `job_checkpoints`, `chunk_checkpoints`, `engine_checkpoints`, `download_checkpoints`
- Indexes: job_id, task_id, keyword, engine_name, status, created_at
- Partitioning: By created_at (monthly partitions) for scalability
- Retention: 30 days hot storage, 90 days total before archival to Azure Blob cold tier



## Components and Interfaces

### 1. CheckpointManager (Core Orchestrator)

**Location**: `builder/checkpoint_manager.py`

**Responsibilities**:
- Create, update, and query checkpoints at all levels
- Coordinate between Redis and PostgreSQL
- Handle checkpoint recovery and resumption
- Manage checkpoint lifecycle (create → update → archive → cleanup)

**Key Methods**:
```python
class CheckpointManager:
    def create_job_checkpoint(self, job_id: int, metadata: dict) -> JobCheckpoint
    def create_chunk_checkpoint(self, job_id: int, task_id: str, metadata: dict) -> ChunkCheckpoint
    def create_engine_checkpoint(self, chunk_id: str, engine: str, metadata: dict) -> EngineCheckpoint
    def create_download_checkpoint(self, engine_id: str, urls: list, metadata: dict) -> DownloadCheckpoint
    
    def update_checkpoint(self, checkpoint_id: str, updates: dict) -> bool
    def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]
    def resume_from_checkpoint(self, job_id: int) -> ResumeContext
```



### 2. Checkpoint Data Models

**Location**: `builder/checkpoint_models.py`

**Base Checkpoint Model**:
```python
class BaseCheckpoint(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: CheckpointType  # JOB, CHUNK, ENGINE, DOWNLOAD
    status: CheckpointStatus  # PENDING, IN_PROGRESS, COMPLETED, FAILED
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

**Job Checkpoint**:
```python
class JobCheckpoint(BaseCheckpoint):
    job_id: int
    project_id: int
    keywords: List[str]
    max_images: int
    total_chunks: int
    active_chunks: int
    completed_chunks: int
    failed_chunks: int
    task_ids: List[str]
```

**Chunk Batch Checkpoint**:
```python
class ChunkCheckpoint(BaseCheckpoint):
    job_id: int
    task_id: str
    chunk_index: int
    keyword: str
    engines_queue: List[str]  # ['google', 'bing', 'baidu', 'duckduckgo']
    target_images: int
    current_engine: Optional[str]
    images_downloaded: int
    images_discovered_per_engine: Dict[str, int]  # {'google': 150, 'bing': 120}
    images_downloaded_per_engine: Dict[str, int]  # {'google': 145, 'bing': 118}
    variations_tried: List[str]  # Track all variations attempted
    current_offset_ranges: Dict[str, Tuple[int, int]]  # {'google': (0, 100)}
    progress_percentage: float
    worker_metadata: Dict[str, Any]  # worker_id, queue_name, priority, hostname
    chunk_metadata: Dict[str, Any]  # Additional context for debugging
```



**Engine Batch Checkpoint**:
```python
class EngineCheckpoint(BaseCheckpoint):
    chunk_id: str
    engine_name: str  # google, bing, baidu, duckduckgo
    keyword: str
    engine_config: Dict[str, Any]  # offset_range, variation_step
    variations_queue: List[str]  # ["{keyword} photo", "{keyword} HD", ...]
    variations_attempted: List[VariationAttempt]
    current_variation: Optional[str]
    current_offset: int
    images_discovered: int
    images_downloaded: int
    processing_metadata: Dict[str, Any]

class VariationAttempt(BaseModel):
    variation_template: str
    formatted_query: str
    retry_count: int
    offset_start: int
    offset_end: int
    images_found: int
    images_downloaded: int
    processing_time: float
    status: str  # success, failed, partial
    error_type: Optional[str]
    error_message: Optional[str]
    retry_strategy: Optional[str]  # From AlternativeKeyTermGenerator
    next_variation_to_try: Optional[str]
    attempt_metadata: Dict[str, Any]  # Additional context
```

**Download Batch Checkpoint**:
```python
class DownloadCheckpoint(BaseCheckpoint):
    engine_id: str
    keyword: str
    variation: str
    offset_range: Tuple[int, int]
    urls_discovered: List[URLMetadata]
    urls_attempted: List[str]
    urls_completed: List[str]
    urls_failed: List[str]
    successful_downloads: List[DownloadResult]
    failed_downloads: List[DownloadFailure]
    duplicates_found: List[DuplicateInfo]
    validation_results: List[ValidationResult]
    batch_statistics: Dict[str, Any]

class URLMetadata(BaseModel):
    url: str
    search_rank: int
    thumbnail_url: Optional[str]
    source_page: Optional[str]
    discovery_time: datetime

class DownloadResult(BaseModel):
    url: str
    filename: str
    file_size: int
    download_duration: float
    final_path: str
    hash_value: Optional[str]
    dimensions: Optional[Tuple[int, int]]
    format: Optional[str]

class DownloadFailure(BaseModel):
    url: str
    error_type: str
    error_message: str
    attempt_count: int
    last_attempt_time: datetime
    retry_scheduled: bool

class DuplicateInfo(BaseModel):
    url: str
    duplicate_of_filename: str
    hash_value: str
    detection_method: str  # perceptual, content
    similarity_score: Optional[float]

class ValidationResult(BaseModel):
    filename: str
    is_valid: bool
    validation_errors: List[str]
    dimensions: Optional[Tuple[int, int]]
    format: Optional[str]
    file_size: int
```



### 3. Persistence Layer

**Location**: `builder/checkpoint_persistence.py`

**Design Rationale**: Separate adapters for Redis and PostgreSQL enable independent testing, easy mocking, and graceful degradation. The abstraction layer allows switching storage backends without affecting business logic.

**Redis Adapter**:
```python
class RedisCheckpointStore:
    def __init__(self, redis_client: Redis, ttl: int = 86400, compression_threshold: int = 102400):
        self.redis = redis_client
        self.ttl = ttl
        self.compression_threshold = compression_threshold  # 100KB
    
    async def save(self, checkpoint: BaseCheckpoint) -> bool
        """Save checkpoint with automatic compression if size > threshold"""
    
    async def get(self, checkpoint_id: str) -> Optional[dict]
        """Get checkpoint with automatic decompression"""
    
    async def update(self, checkpoint_id: str, updates: dict) -> bool
        """Update checkpoint fields atomically"""
    
    async def delete(self, checkpoint_id: str) -> bool
        """Delete checkpoint from Redis"""
    
    async def get_by_job(self, job_id: int) -> List[dict]
        """Get all checkpoints for a job using index key"""
    
    async def batch_update(self, updates: List[Tuple[str, dict]]) -> int
        """Batch update multiple checkpoints for performance"""
    
    async def set_ttl(self, checkpoint_id: str, ttl: int) -> bool
        """Update TTL for checkpoint (e.g., extend for failed jobs)"""
```

**PostgreSQL Adapter**:
```python
class PostgreSQLCheckpointStore:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save(self, checkpoint: BaseCheckpoint) -> bool
        """Save checkpoint to PostgreSQL with retry logic"""
    
    async def get(self, checkpoint_id: str) -> Optional[BaseCheckpoint]
        """Get checkpoint by ID"""
    
    async def update(self, checkpoint_id: str, updates: dict) -> bool
        """Update checkpoint with optimistic locking"""
    
    async def query(self, filters: dict) -> List[BaseCheckpoint]
        """Query checkpoints with filters (job_id, status, created_at range)"""
    
    async def archive(self, checkpoint_id: str) -> bool
        """Mark checkpoint as archived and compress data"""
    
    async def batch_save(self, checkpoints: List[BaseCheckpoint]) -> int
        """Batch insert for performance"""
    
    async def cleanup_old(self, days: int = 30) -> int
        """Delete checkpoints older than specified days"""
```

**Unified Persistence Manager**:
```python
class CheckpointPersistence:
    """Coordinates between Redis and PostgreSQL with fallback logic"""
    
    def __init__(self, redis_store: RedisCheckpointStore, pg_store: PostgreSQLCheckpointStore):
        self.redis = redis_store
        self.postgres = pg_store
        self.write_queue = asyncio.Queue()  # For queued writes during outages
    
    async def save(self, checkpoint: BaseCheckpoint) -> bool:
        """Write to both Redis and PostgreSQL with fallback"""
        redis_success = await self._safe_redis_write(checkpoint)
        pg_success = await self._safe_postgres_write(checkpoint)
        
        if not redis_success and not pg_success:
            # Queue for retry
            await self.write_queue.put(checkpoint)
            raise PersistenceError("Both Redis and PostgreSQL unavailable")
        
        return True
    
    async def get(self, checkpoint_id: str) -> Optional[BaseCheckpoint]:
        """Read from Redis first, fallback to PostgreSQL"""
        checkpoint = await self.redis.get(checkpoint_id)
        if checkpoint:
            return checkpoint
        
        # Cache miss - query PostgreSQL and populate Redis
        checkpoint = await self.postgres.get(checkpoint_id)
        if checkpoint:
            await self.redis.save(checkpoint)
        
        return checkpoint
```



### 4. Integration with Celery Tasks

**Location**: `builder/tasks.py` (modifications)

**Task Checkpoint Hooks**:
```python
@app.task(bind=True, base=BaseTask, name='builder.download_google')
def task_download_google(self, keyword: str, output_dir: str, max_images: int, 
                         checkpoint_context: Optional[dict] = None):
    # Create chunk checkpoint at task start
    checkpoint_mgr = CheckpointManager()
    chunk_checkpoint = checkpoint_mgr.create_chunk_checkpoint(
        job_id=checkpoint_context['job_id'],
        task_id=self.request.id,
        metadata={
            'keyword': keyword,
            'engines_queue': ['google'],
            'target_images': max_images,
            'worker_id': self.request.hostname
        }
    )
    
    try:
        # Create engine checkpoint
        engine_checkpoint = checkpoint_mgr.create_engine_checkpoint(
            chunk_id=chunk_checkpoint.id,
            engine='google',
            metadata={
                'keyword': keyword,
                'engine_config': get_engines()[0],  # Google config
                'variations_queue': get_search_variations()[:5]
            }
        )
        
        # Download with checkpoint updates
        result = download_google_images_with_checkpoints(
            keyword, output_dir, max_images, engine_checkpoint
        )
        
        # Update checkpoints on completion
        checkpoint_mgr.update_checkpoint(engine_checkpoint.id, {
            'status': 'COMPLETED',
            'images_downloaded': result.total_downloaded
        })
        checkpoint_mgr.update_checkpoint(chunk_checkpoint.id, {
            'status': 'COMPLETED'
        })
        
        return result
    except Exception as e:
        # Update checkpoints on failure
        checkpoint_mgr.update_checkpoint(chunk_checkpoint.id, {
            'status': 'FAILED',
            'error': str(e)
        })
        raise
```



### 5. Resume Logic

**Location**: `builder/checkpoint_resume.py`

**Design Rationale**: Resume logic must reconcile three sources of truth: database state, Celery task state, and checkpoint data. The reconciliation process handles edge cases like stuck tasks, completed-but-not-updated tasks, and corrupted checkpoints.

**Resume Flow**:
```python
class CheckpointResume:
    def __init__(self, checkpoint_mgr: CheckpointManager, celery_app):
        self.checkpoint_mgr = checkpoint_mgr
        self.celery_app = celery_app
    
    async def resume_job(self, job_id: int) -> ResumeContext:
        """Main entry point for job resumption"""
        # 1. Load job checkpoint
        job_checkpoint = await self.checkpoint_mgr.get_job_checkpoint(job_id)
        if not job_checkpoint:
            raise CheckpointNotFoundError(f"No checkpoint found for job {job_id}")
        
        # 2. Reconcile with Celery
        celery_status = await self._reconcile_with_celery(job_checkpoint)
        
        # 3. Identify work to resume
        resume_context = self._build_resume_context(job_checkpoint, celery_status)
        
        # 4. Send notification to user
        await self._notify_user_resume(job_id, resume_context)
        
        return resume_context
    
    async def _reconcile_with_celery(self, job_checkpoint: JobCheckpoint) -> CeleryReconciliation:
        """Query Celery for each task_id and reconcile with checkpoint state"""
        reconciliation = CeleryReconciliation()
        
        for task_id in job_checkpoint.task_ids:
            # Query Celery task state
            celery_result = self.celery_app.AsyncResult(task_id)
            chunk_checkpoint = await self.checkpoint_mgr.get_chunk_checkpoint(task_id)
            
            if celery_result.state == 'SUCCESS' and chunk_checkpoint.status != 'COMPLETED':
                # Task completed but checkpoint not updated
                await self.checkpoint_mgr.update_checkpoint(chunk_checkpoint.id, {
                    'status': 'COMPLETED',
                    'reconciled': True,
                    'reconciliation_time': datetime.utcnow()
                })
                reconciliation.completed_tasks.append(task_id)
            
            elif celery_result.state == 'FAILURE':
                reconciliation.failed_tasks.append(task_id)
            
            elif celery_result.state == 'PENDING' and self._is_stale(chunk_checkpoint):
                # Task stuck - mark for retry
                reconciliation.stale_tasks.append(task_id)
            
            elif celery_result.state in ['STARTED', 'RETRY']:
                reconciliation.active_tasks.append(task_id)
        
        return reconciliation
    
    def _is_stale(self, chunk_checkpoint: ChunkCheckpoint) -> bool:
        """Check if checkpoint is stale (no update for 30 minutes)"""
        if not chunk_checkpoint.updated_at:
            return False
        
        time_since_update = datetime.utcnow() - chunk_checkpoint.updated_at
        return time_since_update.total_seconds() > 1800  # 30 minutes
    
    def _build_resume_context(self, job_checkpoint: JobCheckpoint, celery_status: CeleryReconciliation) -> ResumeContext:
        """Calculate remaining work and build resume context"""
        chunks_to_retry = []
        chunks_to_skip = []
        
        # Identify chunks to retry (failed or stale)
        for task_id in celery_status.failed_tasks + celery_status.stale_tasks:
            chunk_checkpoint = await self.checkpoint_mgr.get_chunk_checkpoint(task_id)
            if chunk_checkpoint.retry_count < MAX_RETRIES:
                chunks_to_retry.append({
                    'task_id': task_id,
                    'chunk_index': chunk_checkpoint.chunk_index,
                    'keyword': chunk_checkpoint.keyword,
                    'resume_from': self._calculate_resume_point(chunk_checkpoint)
                })
            else:
                chunks_to_skip.append(task_id)
        
        # Calculate estimated remaining time
        remaining_images = job_checkpoint.max_images - sum(
            c.images_downloaded for c in await self.checkpoint_mgr.get_all_chunk_checkpoints(job_checkpoint.id)
        )
        estimated_time = self._estimate_completion_time(remaining_images, job_checkpoint)
        
        return ResumeContext(
            job_id=job_checkpoint.job_id,
            chunks_to_retry=chunks_to_retry,
            chunks_to_skip=chunks_to_skip,
            chunks_completed=len(celery_status.completed_tasks),
            chunks_active=len(celery_status.active_tasks),
            estimated_remaining_time=estimated_time,
            resume_strategy='incremental'  # or 'full' if too many failures
        )
    
    def _calculate_resume_point(self, chunk_checkpoint: ChunkCheckpoint) -> dict:
        """Determine where to resume within a chunk"""
        return {
            'engine': chunk_checkpoint.current_engine,
            'variation': chunk_checkpoint.variations_tried[-1] if chunk_checkpoint.variations_tried else None,
            'offset_ranges': chunk_checkpoint.current_offset_ranges,
            'images_downloaded': chunk_checkpoint.images_downloaded
        }
    
    async def _notify_user_resume(self, job_id: int, resume_context: ResumeContext):
        """Send notification to user about job resumption"""
        # Integration with notification system
        pass

class ResumeContext(BaseModel):
    job_id: int
    chunks_to_retry: List[dict]
    chunks_to_skip: List[str]
    chunks_completed: int
    chunks_active: int
    estimated_remaining_time: float
    resume_strategy: str

class CeleryReconciliation(BaseModel):
    completed_tasks: List[str] = []
    failed_tasks: List[str] = []
    stale_tasks: List[str] = []
    active_tasks: List[str] = []
```



## Data Models

### Database Schema (PostgreSQL)

**Table: job_checkpoints**
```sql
CREATE TABLE job_checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id INTEGER NOT NULL REFERENCES crawl_jobs(id),
    keywords JSONB NOT NULL,
    max_images INTEGER NOT NULL,
    total_chunks INTEGER NOT NULL,
    active_chunks INTEGER NOT NULL,
    completed_chunks INTEGER NOT NULL,
    failed_chunks INTEGER NOT NULL,
    task_ids JSONB NOT NULL DEFAULT '[]',
    status VARCHAR(20) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_job_checkpoints_job_id ON job_checkpoints(job_id);
CREATE INDEX idx_job_checkpoints_status ON job_checkpoints(status);
```

**Table: chunk_checkpoints**
```sql
CREATE TABLE chunk_checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_checkpoint_id UUID NOT NULL REFERENCES job_checkpoints(id),
    task_id VARCHAR(100) NOT NULL,
    chunk_index INTEGER NOT NULL,
    keyword VARCHAR(200) NOT NULL,
    engines_queue JSONB NOT NULL,
    target_images INTEGER NOT NULL,
    current_engine VARCHAR(50),
    images_downloaded INTEGER DEFAULT 0,
    images_discovered_per_engine JSONB NOT NULL DEFAULT '{}',
    images_downloaded_per_engine JSONB NOT NULL DEFAULT '{}',
    variations_tried JSONB NOT NULL DEFAULT '[]',
    current_offset_ranges JSONB NOT NULL DEFAULT '{}',
    progress_percentage DECIMAL(5,2) DEFAULT 0.00,
    worker_metadata JSONB NOT NULL DEFAULT '{}',
    chunk_metadata JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(20) NOT NULL,
    error_type VARCHAR(100),
    error_message TEXT,
    traceback TEXT,
    failed_engine VARCHAR(50),
    failed_variation VARCHAR(500),
    last_successful_offset INTEGER,
    retry_count INTEGER DEFAULT 0,
    previous_checkpoint_id UUID REFERENCES chunk_checkpoints(id),
    reconciled BOOLEAN DEFAULT FALSE,
    reconciliation_time TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chunk_checkpoints_job ON chunk_checkpoints(job_checkpoint_id);
CREATE INDEX idx_chunk_checkpoints_task ON chunk_checkpoints(task_id);
CREATE INDEX idx_chunk_checkpoints_status ON chunk_checkpoints(status);
CREATE INDEX idx_chunk_checkpoints_keyword ON chunk_checkpoints(keyword);
CREATE INDEX idx_chunk_checkpoints_updated ON chunk_checkpoints(updated_at);
```



**Table: engine_checkpoints**
```sql
CREATE TABLE engine_checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_checkpoint_id UUID NOT NULL REFERENCES chunk_checkpoints(id),
    engine_name VARCHAR(50) NOT NULL,
    keyword VARCHAR(200) NOT NULL,
    engine_config JSONB NOT NULL,
    variations_queue JSONB NOT NULL,
    variations_attempted JSONB NOT NULL DEFAULT '[]',
    current_variation VARCHAR(500),
    current_offset INTEGER DEFAULT 0,
    images_discovered INTEGER DEFAULT 0,
    images_downloaded INTEGER DEFAULT 0,
    processing_metadata JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_engine_checkpoints_chunk ON engine_checkpoints(chunk_checkpoint_id);
CREATE INDEX idx_engine_checkpoints_engine ON engine_checkpoints(engine_name);
CREATE INDEX idx_engine_checkpoints_keyword ON engine_checkpoints(keyword);
```

**Table: download_checkpoints**
```sql
CREATE TABLE download_checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    engine_checkpoint_id UUID NOT NULL REFERENCES engine_checkpoints(id),
    keyword VARCHAR(200) NOT NULL,
    variation VARCHAR(500) NOT NULL,
    offset_range JSONB NOT NULL,
    urls_discovered JSONB NOT NULL DEFAULT '[]',
    urls_attempted JSONB NOT NULL DEFAULT '[]',
    urls_completed JSONB NOT NULL DEFAULT '[]',
    urls_failed JSONB NOT NULL DEFAULT '[]',
    successful_downloads JSONB NOT NULL DEFAULT '[]',
    failed_downloads JSONB NOT NULL DEFAULT '[]',
    duplicates_found JSONB NOT NULL DEFAULT '[]',
    validation_results JSONB NOT NULL DEFAULT '[]',
    batch_statistics JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_download_checkpoints_engine ON download_checkpoints(engine_checkpoint_id);
CREATE INDEX idx_download_checkpoints_keyword ON download_checkpoints(keyword);
```



### Redis Data Structure

**Key Patterns**:
```
checkpoint:job:{job_id}                          → JobCheckpoint (JSON)
checkpoint:chunk:{task_id}                       → ChunkCheckpoint (JSON)
checkpoint:engine:{chunk_id}:{engine_name}       → EngineCheckpoint (JSON)
checkpoint:download:{engine_id}:{batch_index}    → DownloadCheckpoint (JSON)
checkpoint:index:job:{job_id}:chunks             → Set of chunk_ids
checkpoint:index:chunk:{chunk_id}:engines        → Set of engine_ids
```

**TTL Strategy**:
- Active checkpoints: 24 hours
- Completed checkpoints: 1 hour (then archived to PostgreSQL)
- Failed checkpoints: 7 days (for debugging)



## Error Handling

**Design Rationale**: Error handling follows the principle of graceful degradation - the system should continue operating even when components fail. All errors are logged with structured context for debugging and monitoring.

### Checkpoint Write Failures

1. **Redis Unavailable**: 
   - Immediately fall back to PostgreSQL
   - Log warning with Redis connection details
   - Continue operation without caching layer
   - Retry Redis connection every 60 seconds

2. **PostgreSQL Unavailable**: 
   - Queue writes to Redis with extended TTL (7 days)
   - Add to retry queue with exponential backoff (1s, 2s, 4s, 8s, 16s, max 60s)
   - Alert administrators if outage exceeds 5 minutes
   - Persist retry queue to disk to survive restarts

3. **Both Unavailable**: 
   - Log critical error with full context (job_id, chunk_id, checkpoint_type)
   - Continue processing but mark checkpoint as "pending_write"
   - Retry on next checkpoint update
   - If persistent failure (>10 attempts), fail task gracefully

4. **Partial Write**: 
   - Implement two-phase commit pattern for consistency
   - Write to Redis first (fast), then PostgreSQL (durable)
   - If PostgreSQL write fails, mark Redis checkpoint as "unconfirmed"
   - Background job reconciles unconfirmed checkpoints every 5 minutes

### Checkpoint Read Failures

1. **Cache Miss**: 
   - Query PostgreSQL and populate Redis cache
   - Log cache miss rate for monitoring
   - If cache miss rate >50%, investigate Redis capacity

2. **Data Corruption**: 
   - Validate JSON schema using Pydantic models
   - Log validation errors with checkpoint_id and corrupted fields
   - Attempt repair by filling missing fields with defaults
   - If repair fails, fall back to previous checkpoint (using previous_checkpoint_id)
   - Alert administrators for manual investigation

3. **Missing Checkpoint**: 
   - Check if job is new (no checkpoint expected)
   - Check if checkpoint was deleted (archived)
   - If archived, retrieve from Azure Blob cold storage (5-minute SLA)
   - If truly missing, log error and start from beginning

### Recovery Scenarios

1. **Worker Crash**: 
   - Detect via Celery task timeout (default: 30 minutes)
   - Mark chunk checkpoint as "stale" with stale_detection_time
   - Trigger reconciliation process
   - Retry chunk with incremented retry_count
   - If retry_count >= MAX_RETRIES (3), mark as failed and skip

2. **System Restart**: 
   - On startup, scan for jobs with status "running"
   - Query Celery for task status of all task_ids
   - Reconcile database state with Celery state
   - Offer resume to user via notification
   - Auto-resume if user has auto_resume_enabled preference

3. **Database Failover**: 
   - Retry with exponential backoff (1s, 2s, 4s, 8s, 16s, max 60s)
   - Use Redis cache for reads during outage
   - Queue writes to Redis with extended TTL
   - Once database recovers, flush write queue to PostgreSQL

4. **Checkpoint Corruption**: 
   - Validate checksums on read (if enabled)
   - Attempt recovery using Pydantic validation with defaults
   - Fall back to previous checkpoint (linked via previous_checkpoint_id)
   - If no valid checkpoint found, restart chunk from beginning
   - Log corruption details for post-mortem analysis

### Error Logging Strategy

All errors are logged with structured context using Loguru:
```python
logger.error(
    "Checkpoint write failed",
    extra={
        "job_id": job_id,
        "checkpoint_id": checkpoint_id,
        "checkpoint_type": "chunk",
        "error_type": "redis_unavailable",
        "retry_count": retry_count,
        "fallback_used": "postgresql"
    }
)
```

### Monitoring and Alerts

- **Write Failure Rate**: Alert if >5% of writes fail
- **Read Latency**: Alert if p95 latency >500ms
- **Cache Miss Rate**: Alert if >50% cache misses
- **Stale Checkpoints**: Alert if >10 stale checkpoints detected
- **Corruption Rate**: Alert if >0.1% checkpoints corrupted



## Checkpoint API Integration

**Location**: `backend/api/v1/endpoints/checkpoints.py`

**Design Rationale**: REST API endpoints provide real-time checkpoint visibility to frontend and external integrations. All endpoints require authentication and respect user permissions.

### API Endpoints

```python
@router.get("/jobs/{job_id}/checkpoint", response_model=JobCheckpointResponse)
async def get_job_checkpoint(
    job_id: int,
    current_user: User = Depends(get_current_user),
    checkpoint_mgr: CheckpointManager = Depends(get_checkpoint_manager)
):
    """Get job-level checkpoint with chunk progress breakdown"""
    # Verify user owns job
    # Return job checkpoint with aggregated statistics
    pass

@router.get("/jobs/{job_id}/checkpoints/chunks", response_model=List[ChunkCheckpointResponse])
async def get_chunk_checkpoints(
    job_id: int,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    checkpoint_mgr: CheckpointManager = Depends(get_checkpoint_manager)
):
    """Get all chunk checkpoints for a job with optional status filter"""
    # Support filtering by status: pending, in_progress, completed, failed
    pass

@router.get("/jobs/{job_id}/checkpoints/keywords", response_model=List[KeywordProgressResponse])
async def get_keyword_progress(
    job_id: int,
    current_user: User = Depends(get_current_user),
    checkpoint_mgr: CheckpointManager = Depends(get_checkpoint_manager)
):
    """Get keyword-level progress with engine breakdown"""
    # Aggregate engine checkpoints by keyword
    # Return images_discovered, images_downloaded per engine
    pass

@router.post("/jobs/{job_id}/resume", response_model=ResumeResponse)
async def resume_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    checkpoint_mgr: CheckpointManager = Depends(get_checkpoint_manager),
    resume_service: CheckpointResume = Depends(get_resume_service)
):
    """Validate checkpoint and resume job from last successful state"""
    # Validate checkpoint exists and is resumable
    # Calculate resume context
    # Trigger job resumption
    # Return estimated completion time and chunks to retry
    pass

@router.delete("/jobs/{job_id}/checkpoint", status_code=204)
async def clear_checkpoint(
    job_id: int,
    current_user: User = Depends(get_current_admin),  # Admin only
    checkpoint_mgr: CheckpointManager = Depends(get_checkpoint_manager)
):
    """Clear checkpoint data for a job (admin only)"""
    # Archive to cold storage before deletion
    # Clear from Redis and PostgreSQL
    pass

@router.get("/checkpoints/stats", response_model=CheckpointStatsResponse)
async def get_checkpoint_stats(
    current_user: User = Depends(get_current_admin),  # Admin only
    checkpoint_mgr: CheckpointManager = Depends(get_checkpoint_manager)
):
    """Get system-wide checkpoint statistics (admin only)"""
    # Return total checkpoints, active checkpoints, storage usage
    # Cache miss rate, write failure rate, average latency
    pass
```

### Response Models

```python
class JobCheckpointResponse(BaseModel):
    job_id: int
    status: str
    total_chunks: int
    completed_chunks: int
    active_chunks: int
    failed_chunks: int
    progress_percentage: float
    estimated_completion_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class ChunkCheckpointResponse(BaseModel):
    chunk_id: str
    task_id: str
    chunk_index: int
    keyword: str
    status: str
    progress_percentage: float
    images_downloaded: int
    target_images: int
    current_engine: Optional[str]
    engines_queue: List[str]
    created_at: datetime
    updated_at: datetime

class KeywordProgressResponse(BaseModel):
    keyword: str
    total_images_discovered: int
    total_images_downloaded: int
    engines_used: List[str]
    engine_breakdown: Dict[str, EngineProgress]

class EngineProgress(BaseModel):
    engine_name: str
    images_discovered: int
    images_downloaded: int
    variations_attempted: int
    status: str

class ResumeResponse(BaseModel):
    job_id: int
    resume_strategy: str
    chunks_to_retry: int
    chunks_to_skip: int
    estimated_remaining_time: float
    resume_started_at: datetime

class CheckpointStatsResponse(BaseModel):
    total_checkpoints: int
    active_checkpoints: int
    storage_usage_mb: float
    cache_hit_rate: float
    write_success_rate: float
    average_read_latency_ms: float
    average_write_latency_ms: float
```

## Testing Strategy

**Design Rationale**: Comprehensive testing ensures checkpoint reliability across all failure scenarios. Tests are organized by scope (unit, integration, end-to-end) and cover both happy paths and edge cases.

### Unit Tests

**Location**: `builder/tests/test_checkpoint_*.py`

1. **Checkpoint Models** (`test_checkpoint_models.py`):
   - Validate Pydantic models with valid and invalid data
   - Test serialization to JSON and deserialization
   - Test model inheritance and type validation
   - Test default values and optional fields
   - Coverage target: 100%

2. **Persistence Layer** (`test_checkpoint_persistence.py`):
   - Test Redis adapter with fakeredis
   - Test PostgreSQL adapter with SQLite in-memory
   - Test compression/decompression logic
   - Test TTL management
   - Test batch operations
   - Mock external dependencies
   - Coverage target: 95%

3. **CheckpointManager** (`test_checkpoint_manager.py`):
   - Test CRUD operations for all checkpoint types
   - Test error handling and fallback logic
   - Test concurrent updates with race conditions
   - Test checkpoint lifecycle (create → update → archive → cleanup)
   - Mock persistence layer
   - Coverage target: 90%

4. **Resume Logic** (`test_checkpoint_resume.py`):
   - Test context building with various job states
   - Test Celery reconciliation with mocked Celery results
   - Test work calculation and estimation
   - Test stale checkpoint detection
   - Test resume point calculation
   - Coverage target: 90%

### Integration Tests

**Location**: `tests/integration/test_checkpoint_*.py`

1. **End-to-End Flow** (`test_checkpoint_e2e.py`):
   - Create job → process chunks → checkpoint updates → resume
   - Test with real Redis and PostgreSQL (Docker containers)
   - Verify checkpoint consistency across layers
   - Test job completion and archival
   - Duration: ~5 minutes per test

2. **Celery Integration** (`test_checkpoint_celery.py`):
   - Test checkpoint updates from actual Celery tasks
   - Test task retry with checkpoint recovery
   - Test worker crash simulation
   - Test distributed processing with multiple workers
   - Requires Celery worker and Redis broker
   - Duration: ~10 minutes per test

3. **Database Integration** (`test_checkpoint_database.py`):
   - Test PostgreSQL schema creation and migrations
   - Test indexes and query performance
   - Test partitioning strategy
   - Test concurrent writes and reads
   - Test transaction rollback and recovery
   - Duration: ~3 minutes per test

4. **Redis Integration** (`test_checkpoint_redis.py`):
   - Test caching behavior with real Redis
   - Test TTL expiration and eviction
   - Test compression for large checkpoints
   - Test connection failure and recovery
   - Duration: ~2 minutes per test

### Failure Scenarios

**Location**: `tests/failure/test_checkpoint_*.py`

1. **Redis Failure** (`test_redis_failure.py`):
   - Simulate Redis unavailability
   - Verify fallback to PostgreSQL
   - Verify write queuing and retry
   - Verify cache miss handling
   - Test Redis recovery and cache repopulation

2. **PostgreSQL Failure** (`test_postgres_failure.py`):
   - Simulate PostgreSQL unavailability
   - Verify queuing to Redis with extended TTL
   - Verify retry logic with exponential backoff
   - Test database recovery and queue flush

3. **Worker Crash** (`test_worker_crash.py`):
   - Simulate worker crash mid-task
   - Verify checkpoint recovery
   - Verify task retry with resume context
   - Test stale checkpoint detection
   - Test reconciliation process

4. **Checkpoint Corruption** (`test_checkpoint_corruption.py`):
   - Inject corrupted checkpoint data
   - Verify validation and error detection
   - Verify recovery from previous checkpoint
   - Test fallback to job restart

5. **Network Partition** (`test_network_partition.py`):
   - Simulate network partition between services
   - Verify graceful degradation
   - Verify eventual consistency after recovery

### Performance Tests

**Location**: `tests/performance/test_checkpoint_*.py`

1. **Write Performance** (`test_checkpoint_write_perf.py`):
   - Measure write latency for Redis (<100ms target)
   - Measure write latency for PostgreSQL (<5s target)
   - Test batch write performance
   - Test concurrent writes (100+ simultaneous)

2. **Read Performance** (`test_checkpoint_read_perf.py`):
   - Measure cache hit latency (<50ms target)
   - Measure cache miss latency (<500ms target)
   - Test query performance with large datasets (10,000+ checkpoints)

3. **Scalability** (`test_checkpoint_scalability.py`):
   - Test with 10,000+ concurrent jobs
   - Test with 100,000+ checkpoints
   - Measure storage growth rate
   - Test cleanup performance

### Test Automation

```bash
# Run all checkpoint tests
pytest builder/tests/test_checkpoint_*.py -v

# Run with coverage
pytest builder/tests/test_checkpoint_*.py --cov=builder --cov-report=html

# Run integration tests only
pytest tests/integration/test_checkpoint_*.py -v -m integration

# Run failure scenario tests
pytest tests/failure/test_checkpoint_*.py -v -m failure

# Run performance tests
pytest tests/performance/test_checkpoint_*.py -v -m performance
```

### Continuous Integration

- All unit tests run on every commit
- Integration tests run on pull requests
- Failure scenario tests run nightly
- Performance tests run weekly
- Coverage threshold: 85% minimum for checkpoint code



## Checkpoint Cleanup and Archival

**Location**: `builder/checkpoint_cleanup.py`

**Design Rationale**: Automatic cleanup prevents unbounded storage growth while maintaining data for debugging and analytics. The tiered archival strategy balances cost and accessibility.

### Cleanup Strategy

```python
class CheckpointCleanup:
    """Manages checkpoint lifecycle and archival"""
    
    def __init__(self, checkpoint_mgr: CheckpointManager, azure_client: AzureBlobClient):
        self.checkpoint_mgr = checkpoint_mgr
        self.azure = azure_client
    
    async def cleanup_completed_jobs(self):
        """Archive checkpoints for completed jobs within 1 hour"""
        completed_jobs = await self.checkpoint_mgr.query_jobs(
            status='completed',
            completed_before=datetime.utcnow() - timedelta(hours=1)
        )
        
        for job in completed_jobs:
            await self._archive_job_checkpoints(job.id)
    
    async def cleanup_failed_jobs(self):
        """Retain failed job checkpoints for 7 days before archival"""
        failed_jobs = await self.checkpoint_mgr.query_jobs(
            status='failed',
            failed_before=datetime.utcnow() - timedelta(days=7)
        )
        
        for job in failed_jobs:
            await self._archive_job_checkpoints(job.id)
    
    async def cleanup_old_checkpoints(self):
        """Delete checkpoints older than 30 days from hot storage"""
        old_checkpoints = await self.checkpoint_mgr.query_checkpoints(
            created_before=datetime.utcnow() - timedelta(days=30)
        )
        
        # Process in batches of 100
        for batch in self._batch(old_checkpoints, 100):
            await self._compress_and_move_to_cold_storage(batch)
    
    async def cleanup_ancient_checkpoints(self):
        """Delete checkpoints older than 90 days from all storage"""
        ancient_checkpoints = await self.checkpoint_mgr.query_checkpoints(
            created_before=datetime.utcnow() - timedelta(days=90)
        )
        
        for checkpoint in ancient_checkpoints:
            await self.azure.delete_blob(f"checkpoints/{checkpoint.id}.json.gz")
            await self.checkpoint_mgr.delete_checkpoint(checkpoint.id)
    
    async def _archive_job_checkpoints(self, job_id: int):
        """Archive all checkpoints for a job to Azure Blob cold tier"""
        checkpoints = await self.checkpoint_mgr.get_all_checkpoints(job_id)
        
        # Compress all checkpoints into single archive
        archive_data = self._compress_checkpoints(checkpoints)
        
        # Upload to Azure Blob cold tier
        blob_path = f"checkpoints/archived/{job_id}/{datetime.utcnow().isoformat()}.json.gz"
        await self.azure.upload_blob(blob_path, archive_data, tier='cold')
        
        # Clear from Redis
        for checkpoint in checkpoints:
            await self.checkpoint_mgr.redis_store.delete(checkpoint.id)
        
        # Mark as archived in PostgreSQL
        await self.checkpoint_mgr.postgres_store.archive(job_id)
    
    async def retrieve_archived_checkpoint(self, job_id: int) -> List[BaseCheckpoint]:
        """Retrieve archived checkpoint from cold storage (5-minute SLA)"""
        # Query PostgreSQL for archive location
        archive_info = await self.checkpoint_mgr.postgres_store.get_archive_info(job_id)
        
        # Download from Azure Blob cold tier
        archive_data = await self.azure.download_blob(archive_info.blob_path)
        
        # Decompress and deserialize
        checkpoints = self._decompress_checkpoints(archive_data)
        
        return checkpoints
```

### Cleanup Schedule

**Celery Beat Tasks**:
```python
# celery_core/tasks.py

@app.task(name='checkpoint.cleanup_completed')
def cleanup_completed_checkpoints():
    """Run every hour"""
    cleanup = CheckpointCleanup(checkpoint_mgr, azure_client)
    asyncio.run(cleanup.cleanup_completed_jobs())

@app.task(name='checkpoint.cleanup_failed')
def cleanup_failed_checkpoints():
    """Run daily at 2 AM"""
    cleanup = CheckpointCleanup(checkpoint_mgr, azure_client)
    asyncio.run(cleanup.cleanup_failed_jobs())

@app.task(name='checkpoint.cleanup_old')
def cleanup_old_checkpoints():
    """Run daily at 3 AM"""
    cleanup = CheckpointCleanup(checkpoint_mgr, azure_client)
    asyncio.run(cleanup.cleanup_old_checkpoints())

@app.task(name='checkpoint.cleanup_ancient')
def cleanup_ancient_checkpoints():
    """Run weekly on Sunday at 4 AM"""
    cleanup = CheckpointCleanup(checkpoint_mgr, azure_client)
    asyncio.run(cleanup.cleanup_ancient_checkpoints())
```

### Retention Policy

| Checkpoint Status | Hot Storage (Redis + PostgreSQL) | Cold Storage (Azure Blob) | Total Retention |
|-------------------|-----------------------------------|---------------------------|-----------------|
| Active (in_progress) | Until completion | N/A | N/A |
| Completed | 1 hour | 30 days | 30 days |
| Failed | 7 days | 30 days | 37 days |
| Archived | Deleted | 90 days | 90 days |

### Storage Optimization

1. **Compression**: Use zstandard compression (level 3) for 70-80% size reduction
2. **Deduplication**: Store common metadata (engine configs, variations) once per job
3. **Pruning**: Remove redundant fields before archival (e.g., intermediate states)
4. **Aggregation**: Combine all checkpoints for a job into single archive file

### Retrieval SLA

- **Hot Storage (Redis/PostgreSQL)**: <500ms
- **Cold Storage (Azure Blob)**: <5 minutes (cold tier rehydration)
- **Deleted**: Not retrievable (user notified before deletion)

## Integration with Existing Systems

**Design Rationale**: The checkpoint system must integrate seamlessly with existing PixCrawler components without requiring major refactoring. Integration points are designed to be minimally invasive and backward compatible.

### Integration with Progress Tracking (`builder/progress.py`)

**Current System**: `ProgressCache`, `DatasetTracker`, `ProgressManager`

**Migration Strategy**:
1. **Phase 1**: Run checkpoint system in parallel with existing progress tracking
2. **Phase 2**: Migrate progress queries to use checkpoint data
3. **Phase 3**: Deprecate old progress tracking system

**Adapter Layer**:
```python
class ProgressCheckpointAdapter:
    """Adapts checkpoint system to existing progress tracking interface"""
    
    def __init__(self, checkpoint_mgr: CheckpointManager, legacy_progress: ProgressManager):
        self.checkpoint_mgr = checkpoint_mgr
        self.legacy_progress = legacy_progress
    
    async def get_progress(self, job_id: int) -> dict:
        """Get progress from checkpoint system with fallback to legacy"""
        try:
            checkpoint = await self.checkpoint_mgr.get_job_checkpoint(job_id)
            return self._convert_checkpoint_to_progress(checkpoint)
        except CheckpointNotFoundError:
            # Fallback to legacy system
            return await self.legacy_progress.get_progress(job_id)
    
    def _convert_checkpoint_to_progress(self, checkpoint: JobCheckpoint) -> dict:
        """Convert checkpoint format to legacy progress format"""
        return {
            'job_id': checkpoint.job_id,
            'total_images': checkpoint.max_images,
            'downloaded_images': sum(c.images_downloaded for c in checkpoint.chunks),
            'progress_percentage': checkpoint.completed_chunks / checkpoint.total_chunks * 100,
            'status': checkpoint.status
        }
```

### Integration with Celery Tasks (`builder/tasks.py`)

**Modification Strategy**: Add checkpoint hooks to existing tasks without breaking current functionality

**Task Decorator**:
```python
def with_checkpoint(checkpoint_type: str):
    """Decorator to add checkpoint tracking to Celery tasks"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            checkpoint_mgr = CheckpointManager()
            checkpoint_context = kwargs.get('checkpoint_context', {})
            
            # Create checkpoint at task start
            if checkpoint_type == 'chunk':
                checkpoint = checkpoint_mgr.create_chunk_checkpoint(
                    job_id=checkpoint_context['job_id'],
                    task_id=self.request.id,
                    metadata=checkpoint_context
                )
            
            try:
                # Execute original task
                result = func(self, *args, **kwargs)
                
                # Update checkpoint on success
                checkpoint_mgr.update_checkpoint(checkpoint.id, {
                    'status': 'COMPLETED',
                    'result': result
                })
                
                return result
            except Exception as e:
                # Update checkpoint on failure
                checkpoint_mgr.update_checkpoint(checkpoint.id, {
                    'status': 'FAILED',
                    'error': str(e),
                    'traceback': traceback.format_exc()
                })
                raise
        
        return wrapper
    return decorator

# Usage in existing tasks
@app.task(bind=True, base=BaseTask, name='builder.download_google')
@with_checkpoint('chunk')
def task_download_google(self, keyword: str, output_dir: str, max_images: int, 
                         checkpoint_context: Optional[dict] = None):
    # Existing task implementation remains unchanged
    pass
```

### Integration with Database Models (`backend/database/models.py`)

**Schema Changes**: Add checkpoint-related fields to existing `crawl_jobs` table

```sql
-- Migration: Add checkpoint fields to crawl_jobs
ALTER TABLE crawl_jobs ADD COLUMN IF NOT EXISTS checkpoint_enabled BOOLEAN DEFAULT TRUE;
ALTER TABLE crawl_jobs ADD COLUMN IF NOT EXISTS last_checkpoint_id UUID;
ALTER TABLE crawl_jobs ADD COLUMN IF NOT EXISTS checkpoint_created_at TIMESTAMP;
ALTER TABLE crawl_jobs ADD COLUMN IF NOT EXISTS checkpoint_updated_at TIMESTAMP;

-- Index for checkpoint queries
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_checkpoint ON crawl_jobs(last_checkpoint_id) WHERE checkpoint_enabled = TRUE;
```

**SQLAlchemy Model Update**:
```python
class CrawlJob(Base):
    __tablename__ = 'crawl_jobs'
    
    # Existing fields...
    
    # New checkpoint fields
    checkpoint_enabled = Column(Boolean, default=True)
    last_checkpoint_id = Column(UUID, nullable=True)
    checkpoint_created_at = Column(DateTime, nullable=True)
    checkpoint_updated_at = Column(DateTime, nullable=True)
    
    # Relationship to checkpoint system
    @property
    def checkpoint(self):
        """Lazy load checkpoint from checkpoint system"""
        if self.last_checkpoint_id:
            checkpoint_mgr = CheckpointManager()
            return checkpoint_mgr.get_checkpoint(self.last_checkpoint_id)
        return None
```

### Integration with Frontend (`frontend/lib/api/index.ts`)

**API Client Methods**:
```typescript
// Add to existing API client
export const checkpointApi = {
  getJobCheckpoint: async (jobId: number): Promise<JobCheckpoint> => {
    return apiClient.get(`/jobs/${jobId}/checkpoint`);
  },
  
  getChunkCheckpoints: async (jobId: number, status?: string): Promise<ChunkCheckpoint[]> => {
    return apiClient.get(`/jobs/${jobId}/checkpoints/chunks`, { params: { status } });
  },
  
  getKeywordProgress: async (jobId: number): Promise<KeywordProgress[]> => {
    return apiClient.get(`/jobs/${jobId}/checkpoints/keywords`);
  },
  
  resumeJob: async (jobId: number): Promise<ResumeResponse> => {
    return apiClient.post(`/jobs/${jobId}/resume`);
  }
};
```

**React Hook for Real-time Progress**:
```typescript
// frontend/hooks/useCheckpointProgress.ts
export function useCheckpointProgress(jobId: number) {
  const [checkpoint, setCheckpoint] = useState<JobCheckpoint | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  
  useEffect(() => {
    const fetchCheckpoint = async () => {
      try {
        const data = await checkpointApi.getJobCheckpoint(jobId);
        setCheckpoint(data);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };
    
    // Poll every 5 seconds for active jobs
    const interval = setInterval(fetchCheckpoint, 5000);
    fetchCheckpoint();
    
    return () => clearInterval(interval);
  }, [jobId]);
  
  return { checkpoint, loading, error };
}
```

### Integration with Notification System (`backend/api/v1/endpoints/notifications.py`)

**Checkpoint Events**:
```python
class CheckpointNotificationService:
    """Send notifications for checkpoint events"""
    
    async def notify_job_resumed(self, job_id: int, resume_context: ResumeContext):
        """Notify user when job is resumed"""
        notification = {
            'type': 'job_resumed',
            'title': 'Job Resumed',
            'message': f'Job #{job_id} resumed with {resume_context.chunks_to_retry} chunks to retry',
            'metadata': {
                'job_id': job_id,
                'estimated_time': resume_context.estimated_remaining_time
            }
        }
        await self._send_notification(notification)
    
    async def notify_checkpoint_failed(self, job_id: int, error: str):
        """Notify user when checkpoint system fails"""
        notification = {
            'type': 'checkpoint_error',
            'title': 'Checkpoint Error',
            'message': f'Job #{job_id} checkpoint failed: {error}',
            'metadata': {'job_id': job_id}
        }
        await self._send_notification(notification)
```

### Backward Compatibility

**Compatibility Layer**:
- All existing APIs continue to work without modification
- Checkpoint system is opt-in via `checkpoint_enabled` flag
- Legacy progress tracking runs in parallel during migration
- Gradual rollout: 10% → 50% → 100% of jobs

**Feature Flags**:
```python
# backend/core/settings/base.py
CHECKPOINT_ENABLED = os.getenv('CHECKPOINT_ENABLED', 'true').lower() == 'true'
CHECKPOINT_MIGRATION_PERCENTAGE = int(os.getenv('CHECKPOINT_MIGRATION_PERCENTAGE', '100'))
```

## Performance Considerations

**Design Rationale**: Performance targets are based on user experience requirements - checkpoint operations should be imperceptible to users and not impact task processing throughput.

### Optimization Strategies

1. **Batch Updates**: 
   - Group multiple checkpoint updates into single write operation
   - Reduces database round-trips by 80%
   - Implemented in `CheckpointPersistence.batch_update()`

2. **Async Writes**: 
   - Use async I/O for non-blocking checkpoint persistence
   - Tasks continue processing while checkpoints write in background
   - Implemented with asyncio and aioredis/asyncpg

3. **Compression**: 
   - Compress checkpoint data >100KB before storage
   - Use zstandard (level 3) for 70-80% size reduction
   - Automatic compression in Redis adapter

4. **Indexing**: 
   - Strategic indexes on job_id, task_id, status, created_at
   - Composite indexes for common query patterns
   - Partial indexes for active checkpoints only

5. **Caching**: 
   - Redis cache for hot checkpoints (active jobs)
   - PostgreSQL for cold storage (completed/failed jobs)
   - Cache hit rate target: >80%

6. **Partitioning**: 
   - Monthly partitions for checkpoint tables
   - Automatic partition creation via PostgreSQL
   - Old partitions dropped during cleanup

7. **Connection Pooling**:
   - Redis connection pool (min=10, max=50)
   - PostgreSQL connection pool (min=5, max=20)
   - Prevents connection exhaustion under load

8. **Query Optimization**:
   - Use JSONB indexes for metadata queries
   - Avoid SELECT * - only fetch needed fields
   - Use EXPLAIN ANALYZE to optimize slow queries

### Performance Targets

| Operation | Target | Measurement |
|-----------|--------|-------------|
| Checkpoint write (Redis) | <100ms | p95 latency |
| Checkpoint write (PostgreSQL) | <5s | p95 latency |
| Checkpoint read (Redis hit) | <50ms | p95 latency |
| Checkpoint read (PostgreSQL) | <500ms | p95 latency |
| Resume calculation | <2s | For jobs with <100 chunks |
| Reconciliation | <10s | For jobs with <1000 chunks |
| Storage overhead | <5% | Of total image data size |
| Batch update (100 checkpoints) | <1s | Total time |
| Cleanup (1000 checkpoints) | <30s | Total time |

### Performance Monitoring

**Metrics to Track**:
- Write latency (p50, p95, p99)
- Read latency (p50, p95, p99)
- Cache hit rate
- Write failure rate
- Storage usage growth rate
- Query execution time
- Connection pool utilization

**Alerting Thresholds**:
- p95 write latency >200ms (Redis) or >10s (PostgreSQL)
- p95 read latency >100ms (Redis) or >1s (PostgreSQL)
- Cache hit rate <70%
- Write failure rate >5%
- Storage growth >10GB/day
- Connection pool utilization >80%

### Load Testing

**Scenarios**:
1. **High Write Volume**: 1000 checkpoint updates/second
2. **High Read Volume**: 5000 checkpoint reads/second
3. **Concurrent Jobs**: 10,000 active jobs with checkpoints
4. **Large Checkpoints**: Checkpoints with 10,000+ URLs
5. **Database Failover**: Simulate PostgreSQL failover during load

**Tools**:
- Locust for load generation
- Prometheus for metrics collection
- Grafana for visualization
- Azure Monitor for production monitoring

## Security Considerations

**Design Rationale**: Checkpoint data may contain sensitive information (keywords, URLs, user metadata) and must be protected at rest and in transit.

### Data Protection

1. **Encryption at Rest**:
   - PostgreSQL: Transparent Data Encryption (TDE) via Azure
   - Redis: Encryption enabled via Azure Cache for Redis
   - Azure Blob: Server-side encryption (SSE) with Microsoft-managed keys

2. **Encryption in Transit**:
   - TLS 1.2+ for all database connections
   - HTTPS for all API endpoints
   - Redis connections over TLS

3. **Access Control**:
   - Row Level Security (RLS) in PostgreSQL for user isolation
   - Redis key namespacing per user/job
   - API endpoints require authentication (Supabase Auth)
   - Admin-only endpoints for system-wide operations

4. **Data Sanitization**:
   - Remove sensitive data before archival (API keys, tokens)
   - Redact user PII in logs
   - Sanitize error messages before exposing to users

### Compliance

1. **GDPR**:
   - User data deletion includes checkpoint data
   - Checkpoint data included in data export requests
   - Retention policies comply with data minimization

2. **Audit Trail**:
   - All checkpoint operations logged with user_id
   - Checkpoint access logged for compliance
   - Deletion events logged with reason

## Deployment Strategy

**Design Rationale**: Phased rollout minimizes risk and allows for validation at each stage.

### Phase 1: Infrastructure Setup (Week 1)

1. Create PostgreSQL tables and indexes
2. Configure Redis with appropriate TTL settings
3. Set up Azure Blob storage for archival
4. Deploy monitoring and alerting

### Phase 2: Core Implementation (Week 2-3)

1. Implement checkpoint models and persistence layer
2. Implement CheckpointManager with CRUD operations
3. Add unit tests and integration tests
4. Deploy to staging environment

### Phase 3: Celery Integration (Week 4)

1. Add checkpoint hooks to Celery tasks
2. Test with small subset of jobs (10%)
3. Monitor performance and error rates
4. Gradually increase to 50% of jobs

### Phase 4: API and Frontend (Week 5)

1. Implement REST API endpoints
2. Add frontend components for checkpoint visibility
3. Implement resume functionality
4. User acceptance testing

### Phase 5: Full Rollout (Week 6)

1. Enable checkpoints for 100% of jobs
2. Deprecate legacy progress tracking
3. Monitor system performance
4. Gather user feedback

### Rollback Plan

If critical issues are discovered:
1. Disable checkpoint creation via feature flag
2. Continue using legacy progress tracking
3. Investigate and fix issues
4. Resume rollout after validation

## Success Criteria

The checkpoint management system will be considered successful when:

1. **Reliability**: >95% of interrupted jobs successfully resume from checkpoint
2. **Performance**: Checkpoint operations meet all latency targets (p95)
3. **Adoption**: 100% of jobs use checkpoint system
4. **User Satisfaction**: <1% user complaints about resume functionality
5. **System Health**: <0.1% checkpoint data corruption rate
6. **Cost Efficiency**: Checkpoint storage <5% of total storage costs

## Future Enhancements

### Phase 2 Features (Post-MVP)

1. **Checkpoint Versioning**:
   - Support multiple checkpoint versions per job
   - Allow rollback to specific checkpoint
   - Useful for debugging and experimentation

2. **Checkpoint Sharing**:
   - Share checkpoints between similar jobs
   - Deduplicate common data (engine configs, variations)
   - Reduce storage costs by 30-40%

3. **Predictive Resume**:
   - ML model to predict optimal resume strategy
   - Estimate success probability for resume
   - Recommend job restart vs. resume

4. **Checkpoint Compression Optimization**:
   - Adaptive compression based on data characteristics
   - Use different compression levels for different checkpoint types
   - Further reduce storage costs

5. **Real-time Checkpoint Streaming**:
   - Stream checkpoint updates to frontend via WebSocket
   - Eliminate polling for progress updates
   - Improve user experience with instant feedback

6. **Checkpoint Analytics**:
   - Dashboard for checkpoint system health
   - Identify patterns in failures
   - Optimize retry strategies based on historical data

## Conclusion

The checkpoint management system provides comprehensive resumability for PixCrawler crawl jobs through a batch-based, multi-level checkpoint hierarchy. The design balances performance (Redis caching), durability (PostgreSQL persistence), and cost (tiered archival) while maintaining backward compatibility with existing systems.

**Key Design Decisions**:

1. **Dual Persistence**: Redis for speed, PostgreSQL for durability
2. **Batch-Based Hierarchy**: Four levels (job, chunk, engine, download) for granular tracking
3. **Graceful Degradation**: System continues operating even when components fail
4. **Comprehensive Metadata**: Track everything needed for intelligent resume
5. **Minimal Integration Impact**: Decorator-based integration with existing tasks
6. **Phased Rollout**: Gradual migration reduces risk

**Benefits**:

- Users never lose progress on interrupted jobs
- System automatically recovers from failures
- Detailed visibility into job progress at all levels
- Reduced wasted compute and credits
- Improved user satisfaction and trust

**Next Steps**:

1. Review and approve design document
2. Create detailed implementation tasks
3. Begin Phase 1 infrastructure setup
4. Implement core checkpoint system
5. Integrate with Celery tasks
6. Deploy to production with phased rollout

This design addresses all requirements specified in the requirements document and provides a solid foundation for reliable, resumable crawl jobs in PixCrawler.

