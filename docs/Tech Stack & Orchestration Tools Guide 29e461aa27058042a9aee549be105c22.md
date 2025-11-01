# Tech Stack & Orchestration Tools Guide

## Table of Contents

1. [Current Tech Stack](Tech%20Stack%20&%20Orchestration%20Tools%20Guide%2029e461aa27058042a9aee549be105c22.md)
2. [Libraries to Add](Tech%20Stack%20&%20Orchestration%20Tools%20Guide%2029e461aa27058042a9aee549be105c22.md)
3. [Distributed Locking Strategy](Tech%20Stack%20&%20Orchestration%20Tools%20Guide%2029e461aa27058042a9aee549be105c22.md)
4. [Azure Redis vs Redis Lock](Tech%20Stack%20&%20Orchestration%20Tools%20Guide%2029e461aa27058042a9aee549be105c22.md)
5. [Orchestration Tools Comparison](Tech%20Stack%20&%20Orchestration%20Tools%20Guide%2029e461aa27058042a9aee549be105c22.md)
6. [Big Data Tools Evaluation](Tech%20Stack%20&%20Orchestration%20Tools%20Guide%2029e461aa27058042a9aee549be105c22.md)
7. [Recommendations Summary](Tech%20Stack%20&%20Orchestration%20Tools%20Guide%2029e461aa27058042a9aee549be105c22.md)

---

## Current Tech Stack {#current-stack}

### What You Already Have

```python
# From pyproject.toml
celery>=5.3.0              # Task queue ✓
redis>=5.0.0               # Message broker + result backend ✓
kombu                      # Celery's messaging library ✓
pydantic>=2.0.0           # Data validation ✓
sqlalchemy>=2.0.0         # Database ORM ✓
fastapi                    # Web framework ✓
asyncpg                    # Async PostgreSQL ✓

```

**Capabilities:**

- ✅ Task queue and async processing
- ✅ Message brokering and caching
- ✅ Data validation and ORM
- ✅ API framework with async support

---

## Libraries to Add {#libraries-to-add}

### 1. Resource Monitoring

```python
# System resource monitoring (cross-platform)
psutil>=5.9.0

```

**Usage:**

```python
import psutil

# Monitor disk and memory
disk_usage = psutil.disk_usage('/tmp')
memory = psutil.virtual_memory()

# Calculate available processing slots
available_slots = calculate_slots(disk_usage.free, memory.available)

```

### 2. Priority Queue Management

```python
# Already have Redis ✓
redis>=5.0.0

```

**Implementation using Redis Sorted Sets:**

```python
# Add chunks with priority scores
redis_client.zadd('pending_chunks', {chunk_id: priority_score})

# Get highest priority chunks
chunks = redis_client.zpopmax('pending_chunks', count=5)

```

### 3. Distributed Locking

```python
# For coordinating scheduler across multiple instances
python-redis-lock>=4.0.0

```

**Usage:**

```python
from redis_lock import Lock

# Ensure only one scheduler runs at a time
with Lock(redis_client, "scheduler_lock", expire=60):
    allocate_chunks_to_workers()

```

**Note:** Not needed if using Celery Beat pattern (recommended).

### 4. State Machine Management (Optional)

```python
# For structured state transitions
transitions>=0.9.0

```

**Usage:**

```python
from transitions import Machine

states = ['pending', 'processing', 'completed', 'failed']
transitions = [
    {'trigger': 'start', 'source': 'pending', 'dest': 'processing'},
    {'trigger': 'complete', 'source': 'processing', 'dest': 'completed'},
    {'trigger': 'fail', 'source': 'processing', 'dest': 'failed'}
]

```

### 5. Rate Limiting

```python
# Already have FastAPI limiter ✓
# Built-in Celery rate limiting
celery[redis]>=5.3.0  # Already installed

@app.task(rate_limit='100/m')  # 100 tasks per minute
def process_chunk():
    pass

```

### 6. Monitoring & Observability (Optional)

```python
# Celery monitoring
flower>=2.0.0

# Metrics collection
prometheus-client>=0.17.0

# Structured logging (already have pixcrawler-logging with Loguru) ✓

```

### Minimal "Good Enough" Stack

**Only need to add 2 libraries:**

```toml
[project]
dependencies = [
    # ... existing deps ...
    "psutil>=5.9.0",              # Resource monitoring
    "python-redis-lock>=4.0.0"    # Distributed locking (if not using Celery Beat)
]

```

**Why these two?**

**psutil:**

- Check disk space before starting chunks
- Monitor memory usage
- Prevent resource exhaustion
- Works on local and Azure

**python-redis-lock:**

- Prevent multiple schedulers from running simultaneously
- Coordinate chunk allocation
- Already using Redis (no new infrastructure)

### Architecture with Current + New Libraries

```python
# Resource Monitor (uses psutil)
class ResourceMonitor:
    def get_available_slots(self) -> int:
        disk_free = psutil.disk_usage('/tmp').free
        memory_free = psutil.virtual_memory().available
        # 20K images = ~10GB, 35 chunks max
        return min(35, disk_free // (10 * 1024**3) * 35)

# Priority Scheduler (uses Redis + redis-lock)
class ChunkScheduler:
    def schedule_chunks(self):
        with Lock(redis_client, "scheduler", expire=60):
            available = resource_monitor.get_available_slots()
            chunks = redis_client.zpopmax("pending_chunks", available)
            for chunk_id, priority in chunks:
                celery_app.send_task("process_chunk", args=[chunk_id])

# Chunk Worker (uses Celery)
@celery_app.task(bind=True, acks_late=True)
def process_chunk(self, chunk_id: str):
    # Download 500 images
    # Validate
    # Upload to storage
    # Clean temp
    pass

```

---

## Distributed Locking Strategy {#distributed-locking}

### Do You Need Redis Lock?

The answer depends on your deployment architecture.

### Scenario 1: Single App Service

```
┌─────────────────────────────┐
│ Azure App Service           │
│ ┌──────────┐ ┌─────────┐  │
│ │ FastAPI  │ │ Celery  │  │
│ │ (1 inst) │ │ Worker  │  │
│ └──────────┘ └─────────┘  │
└─────────────────────────────┘
         │
         ▼
   External Redis

```

**Need Redis Lock?** ❌ NO - Only one scheduler instance running

### Scenario 2: Scaled App Service

```
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ App Instance 1  │ │ App Instance 2  │ │ App Instance 3  │
│ ┌────┐ ┌─────┐ │ │ ┌────┐ ┌─────┐ │ │ ┌────┐ ┌─────┐ │
│ │API │ │Sched│ │ │ │API │ │Sched│ │ │ │API │ │Sched│ │
│ └────┘ └─────┘ │ │ └────┘ └─────┘ │ │ └────┘ └─────┘ │
└─────────────────┘ └─────────────────┘ └─────────────────┘
         │                │                │
         └────────────────┴────────────────┘
                         ▼
                   Shared Redis

```

**Need Redis Lock?** ✅ YES - Multiple schedulers would conflict

### Scenario 3: Separate Containers

```
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   FastAPI    │ │ Celery Worker│ │    Redis     │
│  Container   │ │  Container   │ │  Container   │
│              │ │              │ │              │
│  (API only)  │ │  (Workers +  │ │              │
│              │ │   Scheduler) │ │              │
└──────────────┘ └──────────────┘ └──────────────┘

```

**Need Redis Lock?** ❌ NO - Only Celery container runs scheduler

**But if you scale Celery containers:**

```
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   FastAPI    │ │  Celery #1   │ │  Celery #2   │
│  Container   │ │  (Workers +  │ │  (Workers +  │
│              │ │   Scheduler) │ │   Scheduler) │
└──────────────┘ └──────────────┘ └──────────────┘

```

**Need Redis Lock?** ✅ YES - Multiple schedulers again

### Decision Matrix

| Deployment Pattern | Scheduler Location | Need Lock? |
| --- | --- | --- |
| Single App Service | Inside FastAPI app (1 instance) | ❌ No |
| Scaled App Service | Inside FastAPI app (N instances) | ✅ Yes |
| Separate Containers | Dedicated scheduler container (1) | ❌ No |
| Scaled Celery Workers | Each worker has scheduler | ✅ Yes |
| **Celery Beat (Recommended)** | **Single Beat container** | **❌ No** |

### Best Practice: Use Celery Beat

Instead of running scheduler in FastAPI or workers, use Celery Beat:

```bash
# Separate container/process for scheduler
celery -A celery_core beat --loglevel=info

# Worker containers (no scheduler, can scale)
celery -A celery_core worker --concurrency=7 -n worker1@%h
celery -A celery_core worker --concurrency=7 -n worker2@%h

```

**Celery Beat is designed to run as a single instance** - it's the scheduler that triggers periodic tasks.

### Recommended Architecture

```
┌─────────────────┐
│    FastAPI      │ ← API endpoints only
│  Container(s)   │ ← Can scale horizontally
└─────────────────┘
         │
         ▼
┌─────────────────┐
│  Celery Beat    │ ← Scheduler (single instance)
│   Container     │ ← Runs chunk allocation logic
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ Celery Workers  │ ← Process chunks (scale to 5+ containers)
│  Container(s)   │ ← Each with concurrency=7
└─────────────────┘
         │
         ▼
┌─────────────────┐
│     Redis       │ ← Message broker + priority queue
│ (Azure Redis)   │
└─────────────────┘

```

**Benefits:**

- ❌ No Redis Lock needed - Only one Beat instance
- ✅ Scale workers independently - Add more worker containers
- ✅ FastAPI scales freely - No scheduler conflicts
- ✅ Clean separation - Each service has one job

---

## Azure Redis vs Redis Lock {#azure-redis}

### What is Azure Redis Cache?

Azure Redis Cache is **managed Redis** - same protocol, managed by Azure.

```
Regular Redis (self-hosted)     Azure Redis Cache
┌─────────────────┐             ┌─────────────────┐
│  Redis Server   │             │  Managed Redis  │
│  (you manage)   │   ====>     │ (Azure manages) │
│  - Updates      │             │  - Auto updates │
│  - Backups      │             │  - Auto backups │
│  - Scaling      │             │  - Auto scaling │
└─────────────────┘             └─────────────────┘

```

**Key point:** It's the same Redis protocol - just managed by Azure.

### Distributed Locking Options

### Option 1: Redis Lock (Works with Azure Redis)

```python
import redis
from redis_lock import Lock

# Connect to Azure Redis
redis_client = redis.Redis(
    host='your-cache.redis.cache.windows.net',
    port=6380,
    password='your-key',
    ssl=True
)

# Use lock (same code as regular Redis)
with Lock(redis_client, "scheduler_lock", expire=60):
    schedule_chunks()

```

**Benefits:**

- ✅ Works with Azure Redis Cache
- ✅ Same code for local and Azure
- ✅ Simple and reliable

### Option 2: Azure Service Bus

```python
from azure.servicebus import ServiceBusClient

# Has built-in message locking
# When worker receives message, it's locked automatically
# No manual locking needed

```

**Pros:**

- ✅ Native Azure service
- ✅ Built-in message locking

**Cons:**

- ❌ Different from Celery (migration needed)
- ❌ More expensive than Redis

### Option 3: Azure Storage Queues

```python
from azure.storage.queue import QueueClient

# Simpler than Service Bus
# Also has automatic message locking

```

**Pros:**

- ✅ Simpler than Service Bus
- ✅ Cheaper

**Cons:**

- ❌ Less features than Service Bus
- ❌ Different from Celery

### Cost Comparison

| Scenario | Lock Solution | Monthly Cost |
| --- | --- | --- |
| Local Redis + Celery Beat | No lock needed | Free |
| Azure Redis + Celery Beat | No lock needed | ~$15 |
| Azure Redis + Scaled Beat | python-redis-lock | ~$15 |
| Azure Service Bus | Built-in locking | ~$10 |
| Azure Storage Queues | Built-in locking | ~$1 |

### Recommendation

1. **Now (Development):** Use Celery Beat pattern → No locks needed
2. **Azure Deployment:**
    - Use Azure Redis Cache (drop-in replacement)
    - Keep Celery Beat pattern → Still no locks needed
3. **Future Migration to Azure Functions:**
    - Use Azure Service Bus or Storage Queues
    - Built-in locking → Still no locks needed

**Azure Redis Cache = Regular Redis managed by Azure**

- No special "Azure Redis-lock" service
- Use same `python-redis-lock` library
- Best practice: Use Celery Beat (single instance) → No locks needed

---

## Orchestration Tools Comparison {#orchestration-tools}

### Tool Overview

When evaluating orchestration tools, consider your actual needs vs. tool capabilities.

### Celery (What You Have)

**What it is:** Task queue for simple job execution

```python
@celery_app.task
def process_chunk(chunk_id):
    download_images()
    validate_images()
    upload_to_storage()

```

**Best for:**

- ✅ Simple task queues
- ✅ Background jobs
- ✅ Real-time processing
- ✅ API-triggered tasks
- ✅ Microservices

**Not great for:**

- ❌ Complex workflows with dependencies
- ❌ Advanced retry logic with backoff
- ❌ Workflow visualization
- ❌ Dynamic DAGs

### Apache Airflow (Workflow Orchestration)

**What it is:** DAG-based workflow orchestration

```python
with DAG('image_dataset_pipeline') as dag:
    chunk_job = split_into_chunks()
    download = download_images(chunk_job)
    validate = validate_images(download)
    upload = upload_to_storage(validate)

    chunk_job >> download >> validate >> upload

```

**Best for:**

- ✅ Complex ETL pipelines
- ✅ Data engineering workflows
- ✅ Scheduled batch jobs
- ✅ Workflow dependencies (DAGs)
- ✅ Monitoring & visualization

**Not great for:**

- ❌ Real-time task processing
- ❌ API-triggered jobs (not designed for it)
- ❌ High-frequency tasks
- ❌ Simple queues

### Prefect (Modern Workflow Orchestration)

**What it is:** Modern workflow orchestration with better API

```python
@flow
def image_dataset_pipeline(job_id):
    chunks = split_into_chunks(job_id)
    for chunk in chunks:
        download = download_images(chunk)
        validate = validate_images(download)
        upload = upload_to_storage(validate)

```

**Best for:**

- ✅ Complex workflows (like Airflow)
- ✅ Better Python API than Airflow
- ✅ Dynamic workflows
- ✅ Hybrid (scheduled + event-driven)
- ✅ Modern UI and monitoring

**Not great for:**

- ❌ Simple task queues (overkill)
- ❌ Lightweight deployments

### Your Use Case Analysis

**What You Need:**

- ✅ API-triggered jobs - User clicks "Create Dataset" → Start job
- ✅ Real-time processing - Process as requests come in
- ✅ Priority queuing - New users > Enterprise > Free
- ✅ Resource management - 35 concurrent chunks max
- ✅ Simple workflow - Download → Validate → Upload → Clean

**What You DON'T Need:**

- ❌ Complex DAGs with 20+ dependencies
- ❌ Scheduled ETL pipelines
- ❌ Data engineering workflows
- ❌ Workflow visualization (nice to have, not critical)

### Recommendation: Stick with Celery

**Why Celery is perfect for you:**

```
User Request → API → Celery Task → Process → Done
                ↓
        [Priority Queue]
                ↓
          [35 workers]
                ↓
       [Chunk processing]

```

**Reasons:**

1. ✅ Already installed and configured
2. ✅ Perfect for API-triggered jobs
3. ✅ Real-time processing
4. ✅ Simple priority queuing (Redis sorted sets)
5. ✅ Lightweight (no heavy orchestration overhead)
6. ✅ Azure migration path (→ Azure Functions)

### When You WOULD Need Airflow/Prefect

**Example: Complex ML Pipeline**

```python
with DAG('ml_training_pipeline'):
    # Stage 1: Data Collection (parallel)
    scrape_google = scrape_images('google')
    scrape_bing = scrape_images('bing')
    scrape_flickr = scrape_images('flickr')

    # Stage 2: Data Processing (depends on Stage 1)
    merge = merge_datasets([scrape_google, scrape_bing, scrape_flickr])
    deduplicate = deduplicate_images(merge)
    validate = validate_quality(deduplicate)

    # Stage 3: ML Training (depends on Stage 2)
    train_model = train_classifier(validate)
    evaluate = evaluate_model(train_model)

    # Stage 4: Deployment (depends on Stage 3)
    if evaluate.accuracy > 0.95:
        deploy = deploy_model(train_model)
    else:
        retrain = retrain_with_more_data(train_model)

```

**This needs orchestration because:**

- Complex dependencies
- Conditional logic
- Multiple stages
- Long-running (hours/days)
- Needs monitoring/retry/backoff

### Your Actual Workflow (Simple)

```python
@celery_app.task
def process_job(job_id):
    chunks = create_chunks(job_id, chunk_size=500)

    for chunk in chunks:
        process_chunk.delay(chunk.id)  # Queue it

@celery_app.task
def process_chunk(chunk_id):
    # Simple linear workflow
    images = download_images(chunk_id)
    validated = validate_images(images)
    upload_to_storage(validated)
    cleanup_temp(chunk_id)

```

**No complex dependencies, no DAGs needed.**

### Decision Timeline

**Now:** Use Celery

- Already have it
- Fits your use case perfectly
- Lightweight
- Easy to understand

**Later:** Consider Prefect IF:

- You add complex ML pipelines
- You need workflow visualization
- You have 10+ interdependent steps
- You need advanced retry/backoff strategies

**Never:** Airflow

- Too heavy for your use case
- Designed for batch ETL, not real-time API jobs
- Harder to deploy and maintain

---

## Big Data Tools Evaluation {#big-data-tools}

### Tool-by-Tool Analysis

### Apache Kafka (Event Streaming Platform)

**Use case:** Real-time event streaming, millions of events/sec

**Examples:** Uber tracking, Netflix recommendations, Stock trading

**Your use case:**

- 100 concurrent users
- ~2K images per job (avg)
- API-triggered jobs (not continuous streams)

**Verdict:** ❌ NO - Massive overkill

**Why:**

- Kafka is for continuous event streams (millions/sec)
- You have discrete jobs (user clicks → job starts)
- Redis pub/sub or Celery is enough
- Kafka adds complexity: Zookeeper, brokers, partitions, consumer groups

**When you'd need it:**

- 10,000+ requests per second
- Real-time analytics on image processing
- Event sourcing architecture

### Apache Flink (Stream Processing)

**Use case:** Real-time data processing, complex event processing

**Examples:** Fraud detection, real-time analytics, IoT data processing

**Your use case:**

- Batch image processing (500 images per chunk)
- Simple workflow: download → validate → upload

**Verdict:** ❌ NO - Wrong tool

**Why:**

- Flink is for real-time stream processing
- You're doing batch processing
- No complex aggregations or windowing needed

**When you'd need it:**

- Real-time image quality metrics
- Live dashboard of processing stats
- Complex event patterns

### Apache Spark (Big Data Processing)

**Use case:** Large-scale data processing, ML training on massive datasets

**Examples:** Processing petabytes of data, distributed ML training

**Your use case:**

- Processing images (not analyzing massive datasets)
- Max 10M images per job (enterprise)
- Simple validation, not complex analytics

**Verdict:** ❌ NO - Overkill

**Why:**

- Spark is for data analytics at scale (TB/PB)
- You're doing image processing (GB scale)
- Spark overhead not worth it for your workload

**When you'd need it:**

- Analyzing metadata from billions of images
- Training ML models on massive datasets
- Complex data transformations

### dbt (Data Build Tool)

**Use case:** SQL transformations, data warehouse modeling

**Examples:** Transform raw data → analytics-ready tables

**Your use case:**

- Image processing SaaS
- Operational database (PostgreSQL via Supabase)
- No data warehouse

**Verdict:** ❌ NO - Wrong domain

**Why:**

- dbt is for analytics engineering (data warehouses)
- You're building a SaaS product (operational)
- No complex SQL transformations needed

**When you'd need it:**

- Building analytics dashboards
- Data warehouse (Snowflake, BigQuery)
- Complex reporting pipelines

### What You Actually Need

**Your Current Stack (Perfect for Your Scale):**

```
┌─────────────────────────────────────────┐
│         Your Current Stack              │
├─────────────────────────────────────────┤
│ FastAPI        → API endpoints          │
│ Celery + Redis → Task queue             │
│ PostgreSQL     → Database               │
│ SQLAlchemy     → ORM                    │
│ Azure Blob     → Storage                │
└─────────────────────────────────────────┘

Scale: 100 concurrent users ✓
       10M images/job max ✓
       35 concurrent chunks ✓

```

### Tools That Make Sense to Add

| Tool | Purpose | When to Add |
| --- | --- | --- |
| psutil | Resource monitoring | ✅ Now |
| Flower | Celery monitoring | ✅ Now (optional) |
| Prometheus + Grafana | Metrics & dashboards | Later (100+ users) |
| Sentry | Error tracking | Later (production) |

### Scale Thresholds

### Current Scale (100 users)

- ✅ FastAPI + Celery + Redis + PostgreSQL
- ❌ Kafka, Flink, Spark, dbt

### Medium Scale (1,000 users)

- ✅ Same stack + Redis Cluster + Read replicas
- ❌ Still no need for Kafka/Flink/Spark

### Large Scale (10,000+ users)

- ✅ Consider Kafka for event streaming
- ✅ Consider Spark for analytics
- ❌ Still no Flink (unless real-time analytics)
- ❌ Still no dbt (unless data warehouse)

### Architecture Comparison

### ❌ Over-Engineered (What NOT to do)

```
User Request
    ↓
FastAPI
    ↓
Kafka (event stream)
    ↓
Flink (stream processing)
    ↓
Spark (batch processing)
    ↓
dbt (transformations)
    ↓
Data Warehouse
    ↓
Result

Complexity: 🔴🔴🔴🔴🔴
Cost: $$$$$
Time to build: 6+ months

```

### ✅ Right-Sized (Your actual needs)

```
User Request
    ↓
FastAPI
    ↓
Celery (task queue)
    ↓
Worker (process images)
    ↓
Azure Blob (storage)
    ↓
PostgreSQL (metadata)
    ↓
Result

Complexity: 🟢
Cost: $
Time to build: 2-4 weeks

```

---

## Recommendations Summary {#recommendations}

### Core Stack (Use Now)

```bash
# Install minimal required additions
uv add psutil

# Optional monitoring
uv add flower prometheus-client --optional monitoring

```

### Architecture Pattern

**Recommended: Celery Beat Pattern**

```
┌─────────────┐
│   FastAPI   │ ← Handle API requests
└─────────────┘
       ↓
┌─────────────┐
│ Celery Beat │ ← Single scheduler instance
└─────────────┘
       ↓
┌─────────────┐
│   Workers   │ ← Scale horizontally (5+ instances)
└─────────────┘
       ↓
┌─────────────┐
│    Redis    │ ← Message broker + priority queue
└─────────────┘

```

**Benefits:**

- ❌ No distributed locking needed
- ✅ Simple to deploy and maintain
- ✅ Easy to scale workers independently
- ✅ Clear separation of concerns

### What NOT to Use

| Tool | Why Not |
| --- | --- |
| Kafka | Overkill - designed for millions of events/sec |
| Flink | Wrong use case - you're doing batch, not stream processing |
| Spark | Wrong scale - you're at GB, not TB/PB scale |
| dbt | Wrong domain - operational SaaS, not analytics warehouse |
| Airflow | Too heavy - designed for ETL, not real-time API jobs |
| Prefect | Overkill - simple workflows don't need complex orchestration |

### When to Revisit

**Consider adding tools when:**

| Milestone | Consider Tool | Why |
| --- | --- | --- |
| 1,000+ users | Redis Cluster | Better Redis scalability |
| 10,000+ users | Kafka | Event streaming at scale |
| Analytics needs | dbt + Warehouse | Reporting and dashboards |
| Real-time ML | Flink | Stream processing for ML |
| Petabyte-scale | Spark | Massive data processing |

### Decision Framework

**Your current stack handles:**

- ✅ 100-1,000 concurrent users
- ✅ Millions of images per day
- ✅ Simple, maintainable, cost-effective
- ✅ Fast development (2-4 weeks)

**Philosophy:** "Good Enough to Start"

- Start simple with proven tools
- Scale up when you actually need it
- Avoid premature optimization
- Keep complexity low

### Final Implementation Checklist

**Required:**

- [x]  Celery (already have)
- [x]  Redis (already have)
- [x]  PostgreSQL (already have)
- [ ]  psutil (add now)

**Recommended:**

- [ ]  Celery Beat pattern (implement)
- [ ]  Flower (monitoring - optional)

**NOT Needed:**

- [ ]  ~~python-redis-lock~~ (using Celery Beat instead)
- [ ]  ~~Kafka~~
- [ ]  ~~Flink~~
- [ ]  ~~Spark~~
- [ ]  ~~dbt~~
- [ ]  ~~Airflow~~
- [ ]  ~~Prefect~~

---

## Installation Commands

```bash
# Minimal required additions
uv add psutil

# Optional monitoring tools
uv add flower --optional monitoring
uv add prometheus-client --optional monitoring

# Start Celery Beat (scheduler)
celery -A celery_core beat --loglevel=info

# Start Celery Workers (can scale these)
celery -A celery_core worker --concurrency=7 -n worker@%h

```