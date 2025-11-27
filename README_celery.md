# Celery Integration Guide

This document details the Celery configuration, usage, and testing procedures for the PixCrawler project.

## Overview

The `celery_core` package serves as the central Celery application for the entire monorepo. It manages the Celery app instance, configuration, and task queues. Other packages (`backend`, `builder`, `validator`) should use the shared app instance from `celery_core`.

## Configuration

Celery is configured using Pydantic Settings in `celery_core/config.py`. It uses the `PIXCRAWLER_CELERY_` prefix for environment variables.

### Key Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PIXCRAWLER_CELERY_BROKER_URL` | `redis://localhost:6379/0` | Message broker URL (Redis) |
| `PIXCRAWLER_CELERY_RESULT_BACKEND` | `redis://localhost:6379/1` | Result backend URL (Redis) |
| `PIXCRAWLER_CELERY_WORKER_CONCURRENCY` | `35` | Number of worker processes |
| `PIXCRAWLER_CELERY_ENABLE_MONITORING` | `True` | Enable Flower monitoring |

### Queues and Routing

Tasks are routed to specific queues based on their package/priority:

- **crawl** (Priority 9): High priority, for image crawling tasks (`builder.tasks.*`)
- **validation** (Priority 5): Medium priority, for image validation (`validator.tasks.*`)
- **maintenance** (Priority 1): Low priority, for cleanup (`celery_core.cleanup_*`)
- **default** (Priority 5): Standard priority (`default`)

## Usage

### Defining Tasks

To define a new task, import the app from `celery_core.app` and use the `@app.task` decorator. Use `celery_core.base.BaseTask` as the base class for consistent error handling and logging.

```python
from celery_core.app import get_celery_app
from celery_core.base import BaseTask

app = get_celery_app()

@app.task(bind=True, base=BaseTask, name='my_package.my_task')
def my_task(self, arg1):
    # Task logic here
    return f"Processed {arg1}"
```

### Chaining Tasks

You can chain tasks using Celery's `chain` or `|` operator.

```python
from celery import chain
from builder.tasks import crawl_task
from validator.tasks import validate_task

# Chain crawl -> validate
workflow = chain(crawl_task.s(url), validate_task.s())
workflow.apply_async()
```

## Testing

### Local Testing

To test tasks locally, ensure you have Redis running.

1.  **Start Redis**:
    ```bash
    # If using Docker
    docker run -d -p 6379:6379 redis
    ```

2.  **Start Celery Worker**:
    Run the worker from the root directory:
    ```bash
    uv run celery -A celery_core.app worker --loglevel=info
    ```

3.  **Run a Test Script**:
    Create a script to trigger a task:
    ```python
    # test_celery.py
    from celery_core.tasks import health_check

    result = health_check.delay()
    print(f"Task ID: {result.id}")
    print(f"Result: {result.get(timeout=10)}")
    ```

### Error Handling & Reconnection

The `BaseTask` class handles common errors and retries.
- **Redis Disconnection**: Celery automatically attempts to reconnect to the broker.
- **Task Failures**: Tasks configured with `autoretry_for` or manual retry logic will be retried with exponential backoff.

To test reconnection:
1.  Start the worker.
2.  Stop Redis (`docker stop <redis-container>`).
3.  Trigger a task (it should fail or wait).
4.  Start Redis (`docker start <redis-container>`).
5.  The worker should reconnect and process the task.

## Feedback & Fixes Applied

### Fixes
- **Task Discovery**: Updated `celery_core/app.py` to automatically discover tasks from `celery_core`, `builder`, `validator`, and `backend` packages. This ensures that tasks defined in these modules are registered without manual imports in the app module.
- **Configuration**: Verified that `celery_core` uses a robust Pydantic configuration with environment variable support (`PIXCRAWLER_CELERY_` prefix).

### Recommendations
- **Avoid Duplicate Config**: The `backend` package has its own `celery.py` settings file. It is recommended to rely on `celery_core` for all Celery-related configuration to maintain a single source of truth.
- **Monitoring**: Use Flower for real-time monitoring of workers and tasks.
