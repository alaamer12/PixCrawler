# Celery & Redis Integration Guide

## Architecture Overview

PixCrawler uses **Celery** for distributed task processing and **Redis** for both the message broker and result backend. This ensures high performance, reliability, and scalability for image crawling and processing tasks.

### Components

1.  **Celery App**: Configured in `celery_core/app.py`. It manages task registration, routing, and execution.
2.  **Redis Broker**: Stores task messages waiting to be processed.
    *   URL: `redis://localhost:6379/0` (Default)
3.  **Redis Backend**: Stores the results of completed tasks.
    *   URL: `redis://localhost:6379/1` (Default)
4.  **Workers**: Processes that consume tasks from the broker and write results to the backend.

## Configuration

Configuration is managed via `celery_core/config.py` using Pydantic Settings, allowing environment variable overrides.

| Setting | Environment Variable | Default Value | Description |
| :--- | :--- | :--- | :--- |
| Broker URL | `PIXCRAWLER_CELERY_BROKER_URL` | `redis://localhost:6379/0` | Connection string for the message broker. |
| Result Backend | `PIXCRAWLER_CELERY_RESULT_BACKEND` | `redis://localhost:6379/1` | Connection string for the result backend. |
| Task Time Limit | `PIXCRAWLER_CELERY_TASK_TIME_LIMIT` | `1800` (30 mins) | Hard time limit for tasks. |
| Task Soft Limit | `PIXCRAWLER_CELERY_TASK_SOFT_TIME_LIMIT` | `1500` (25 mins) | Soft time limit for tasks. |

## Task Execution Flow

1.  **Dispatch**: A task is called using `.delay()` or `.apply_async()`.
2.  **Broker**: The task message is serialized (JSON) and pushed to a Redis list (queue).
3.  **Worker**: A Celery worker picks up the message from the queue.
4.  **Execution**: The worker executes the Python function associated with the task.
5.  **Result**: The return value is wrapped in a standard format (by `BaseTask`) and stored in the Redis backend.
6.  **Retrieval**: The client can retrieve the result using the task ID.

## Failure and Recovery

*   **Connection Loss**: Celery workers automatically attempt to reconnect to Redis if the connection is lost.
*   **Task Failure**: Tasks are configured with retry policies (`task_max_retries`, `task_default_retry_delay`).
*   **Worker Crash**: If a worker crashes while processing a task, the task is re-queued (if `task_acks_late=True`, which is enabled).

## Environment Configuration

The system supports multiple environments (Dev, Staging, Prod) via `.env` files. The `CelerySettings` class automatically loads these values.

## Verification

To verify the integration, run the provided test script:

```bash
uv run python scripts/test_celery_redis.py
```

This script checks:
1.  Connectivity to Redis Broker.
2.  Connectivity to Redis Backend.
3.  Task dispatch and execution.
4.  Result retrieval.
