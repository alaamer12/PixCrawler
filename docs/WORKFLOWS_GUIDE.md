# Celery Workflows Guide for PixCrawler

This guide demonstrates how to use Celery Canvas workflows for complex task orchestration in PixCrawler.

## Overview

PixCrawler now uses Celery's Canvas primitives for powerful workflow composition:

- **group**: Execute tasks in parallel
- **chain**: Execute tasks sequentially
- **chord**: Execute tasks in parallel, then run a callback
- **map**: Apply a task to multiple arguments

## Priority Queues

Tasks are automatically routed to priority queues:

| Queue | Priority | Use Case |
|-------|----------|----------|
| `crawl` | 9 (High) | Image crawling tasks |
| `validation` | 5 (Medium) | Image validation tasks |
| `default` | 5 (Medium) | General tasks |
| `maintenance` | 1 (Low) | Cleanup, health checks |

## Rate Limiting

Tasks support rate limiting to prevent API abuse:

```python
@app.task(rate_limit='100/h')  # 100 tasks per hour
def crawl_google(keyword):
    pass
```

## Common Workflow Patterns

### 1. Parallel Crawling

Crawl multiple keywords simultaneously:

```python
from celery_core.workflows import create_parallel_workflow
from builder.tasks import crawl_images

# Crawl 3 keywords in parallel
workflow = create_parallel_workflow([
    crawl_images.s('cats', max_images=100),
    crawl_images.s('dogs', max_images=100),
    crawl_images.s('birds', max_images=100)
])

result = workflow.apply_async()
```

### 2. Sequential Processing

Process data through multiple stages:

```python
from celery_core.workflows import create_sequential_workflow
from builder.tasks import crawl_images
from validator.tasks import validate_batch
from backend.tasks import store_dataset

# Crawl → Validate → Store
workflow = create_sequential_workflow([
    crawl_images.s('cats', max_images=100),
    validate_batch.s(),
    store_dataset.s(dataset_name='cats_dataset')
])

result = workflow.apply_async()
```

### 3. Map-Reduce Pattern

Process multiple items and aggregate results:

```python
from celery_core.workflows import create_map_reduce_workflow
from builder.tasks import crawl_images
from backend.tasks import merge_results

# Crawl multiple keywords, then merge
workflow = create_map_reduce_workflow(
    map_task=crawl_images.s(max_images=50),
    items=['cats', 'dogs', 'birds', 'fish'],
    reduce_task=merge_results.s()
)

result = workflow.apply_async()
```

### 4. Complete Dataset Building Workflow

The most common PixCrawler pattern:

```python
from celery_core.workflows import create_crawl_and_validate_workflow
from builder.tasks import crawl_images
from validator.tasks import validate_batch
from backend.tasks import store_dataset

# Complete workflow: Parallel crawl → Validate → Store
workflow = create_crawl_and_validate_workflow(
    keywords=['cats', 'dogs', 'birds'],
    crawl_task=crawl_images.s(max_images=100),
    validate_task=validate_batch.s(),
    merge_task=store_dataset.s(dataset_name='animals')
)

result = workflow.apply_async()
```

### 5. Callbacks for Notifications

Execute callbacks on success or failure:

```python
from celery_core.workflows import create_callback_workflow
from builder.tasks import crawl_images
from backend.tasks import notify_user, log_error

workflow = create_callback_workflow(
    task=crawl_images.s('cats', max_images=100),
    success_callback=notify_user.s(message='Crawl completed!'),
    error_callback=log_error.s()
)

result = workflow.apply_async()
```

## Monitoring Workflows

### Check Workflow Status

```python
from celery_core.workflows import get_workflow_status

result = workflow.apply_async()
status = get_workflow_status(result)

print(f"State: {status['state']}")
print(f"Ready: {status['ready']}")
print(f"Successful: {status['successful']}")
```

### Cancel Running Workflow

```python
from celery_core.workflows import cancel_workflow

result = workflow.apply_async()

# Cancel if needed
cancel_workflow(result, terminate=True)
```

## Task Scheduling

### Delayed Execution

```python
from datetime import datetime, timedelta

# Run in 1 hour
result = crawl_images.apply_async(
    args=['cats'],
    countdown=3600
)

# Run at specific time
eta = datetime.utcnow() + timedelta(hours=2)
result = crawl_images.apply_async(
    args=['dogs'],
    eta=eta
)
```

### Task Expiration

```python
# Task expires if not executed within 5 minutes
result = crawl_images.apply_async(
    args=['cats'],
    expires=300
)
```

## Scheduled Tasks (Celery Beat)

Periodic tasks are configured in `celery_core/app.py`:

```python
app.conf.beat_schedule = {
    'cleanup-expired-results': {
        'task': 'celery_core.cleanup_expired_results',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
    'health-check': {
        'task': 'celery_core.health_check',
        'schedule': 300.0,  # Every 5 minutes
    },
}
```

Start Celery Beat:

```bash
celery -A celery_core.app beat --loglevel=info
```

## Task Revocation

Cancel running tasks:

```python
from celery_core import revoke_task

# Revoke and terminate
revoke_task('task-id-here', terminate=True)

# Revoke but let finish current work
revoke_task('task-id-here', terminate=False)
```

## Best Practices

### 1. Use Appropriate Queues

```python
# High priority user-initiated crawl
crawl_images.apply_async(
    args=['cats'],
    queue='crawl',
    priority=9
)

# Background validation
validate_batch.apply_async(
    args=[image_ids],
    queue='validation',
    priority=5
)

# Low priority cleanup
cleanup_old_data.apply_async(
    queue='maintenance',
    priority=1
)
```

### 2. Set Rate Limits

```python
@app.task(rate_limit='100/h')  # Respect API limits
def crawl_google(keyword):
    pass

@app.task(rate_limit='200/m')  # 200 per minute
def validate_image(image_id):
    pass
```

### 3. Handle Errors Gracefully

```python
@app.task(
    bind=True,
    autoretry_for=(ConnectionError,),
    retry_kwargs={'max_retries': 3, 'countdown': 60}
)
def crawl_images(self, keyword):
    try:
        # Crawling logic
        pass
    except Exception as exc:
        logger.error(f"Crawl failed: {exc}")
        raise
```

### 4. Use Task Expiration for Time-Sensitive Tasks

```python
# Crawl job expires after 1 hour
result = crawl_images.apply_async(
    args=['cats'],
    expires=3600
)
```

## Running Workers

### Start Workers for Specific Queues

```bash
# High priority crawl worker
celery -A celery_core.app worker -Q crawl -n crawl_worker@%h --concurrency=4

# Validation worker
celery -A celery_core.app worker -Q validation -n validation_worker@%h --concurrency=2

# Maintenance worker
celery -A celery_core.app worker -Q maintenance -n maintenance_worker@%h --concurrency=1

# General worker (all queues)
celery -A celery_core.app worker -Q crawl,validation,maintenance,default -n general_worker@%h
```

### Monitor with Flower

```bash
celery -A celery_core.app flower --port=5555
```

Then visit: http://localhost:5555

## Example: Complete Dataset Building

Here's a real-world example of building a dataset:

```python
from celery_core.workflows import create_crawl_and_validate_workflow
from celery_core import get_workflow_status, cancel_workflow
from builder.tasks import crawl_images
from validator.tasks import validate_batch
from backend.tasks import store_dataset

# Define keywords
keywords = ['cats', 'dogs', 'birds', 'fish', 'rabbits']

# Create workflow
workflow = create_crawl_and_validate_workflow(
    keywords=keywords,
    crawl_task=crawl_images.s(max_images=200, search_engine='google'),
    validate_task=validate_batch.s(validation_level='standard'),
    merge_task=store_dataset.s(
        dataset_name='animals_dataset',
        user_id=123
    )
)

# Execute
result = workflow.apply_async()
print(f"Workflow started: {result.id}")

# Monitor progress
import time
while not result.ready():
    status = get_workflow_status(result)
    print(f"Status: {status['state']}")
    time.sleep(5)

# Get final result
if result.successful():
    final_result = result.result
    print(f"Dataset created: {final_result}")
else:
    print(f"Workflow failed: {result.info}")
```

## Troubleshooting

### Task Not Executing

1. Check worker is running: `celery -A celery_core.app inspect active`
2. Check queue routing: Ensure task is routed to correct queue
3. Check rate limits: Task may be rate-limited

### Workflow Stuck

1. Check individual task status
2. Look for failed tasks in the chain
3. Check worker logs for errors

### High Memory Usage

1. Set `worker_max_memory_per_child` in settings
2. Reduce `worker_prefetch_multiplier`
3. Use task expiration to prevent queue buildup

## Configuration

Key settings in `celery_core/config.py`:

```python
# Task limits
task_time_limit = 1800  # 30 minutes
task_soft_time_limit = 1500  # 25 minutes

# Worker settings
worker_concurrency = 4
worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 1000

# Rate limiting (per task)
rate_limit = '100/m'  # 100 tasks per minute
```

## Summary

PixCrawler's Celery implementation now provides:

✅ **Priority queues** for task routing
✅ **Canvas workflows** for complex orchestration  
✅ **Rate limiting** to prevent API abuse
✅ **Task revocation** for cancellation
✅ **Scheduled tasks** via Celery Beat
✅ **Comprehensive monitoring** with Flower

This gives you full control over distributed task processing while maintaining simplicity.
