# PixCrawler Celery Core

Shared Celery core package for PixCrawler distributed task processing.

## Overview

This package provides the foundational Celery infrastructure for the PixCrawler project, including:

- Centralized Celery application configuration
- Shared task base classes and utilities
- Common monitoring and management tools
- Unified configuration management with Pydantic Settings
- Task result handling and error management

## Features

- **Centralized Configuration**: Pydantic Settings-based configuration with environment variable support
- **Task Base Classes**: Abstract base classes for consistent task implementation across packages
- **Monitoring Integration**: Built-in support for Flower and Prometheus monitoring
- **Error Handling**: Comprehensive error handling and retry mechanisms
- **Result Management**: Standardized task result formats and handling
- **Queue Management**: Intelligent queue routing and load balancing

## Installation

```bash
pip install pixcrawler-celery-core
```

## Configuration

The package uses Pydantic Settings for configuration management. Set environment variables with the `PIXCRAWLER_CELERY_` prefix:

```bash
# Broker and backend
PIXCRAWLER_CELERY_BROKER_URL=redis://localhost:6379/0
PIXCRAWLER_CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Worker settings
PIXCRAWLER_CELERY_WORKER_CONCURRENCY=4
PIXCRAWLER_CELERY_TASK_TIME_LIMIT=1800

# Monitoring
PIXCRAWLER_CELERY_ENABLE_MONITORING=true
PIXCRAWLER_CELERY_FLOWER_PORT=5555
```

## Usage

### Basic Setup

```python
from celery_core import get_celery_app, CelerySettings

# Get configured Celery app
app = get_celery_app()

# Or with custom settings
settings = CelerySettings(broker_url="redis://localhost:6379/0")
app = get_celery_app(settings)
```

### Creating Tasks

```python
from celery_core import BaseTask

class MyTask(BaseTask):
    def run(self, *args, **kwargs):
        # Your task implementation
        return {"status": "completed"}

# Register with Celery app
app.register_task(MyTask())
```

### Task Management

```python
from celery_core import TaskManager

manager = TaskManager()

# Submit task
task_id = manager.submit_task("my_task", arg1="value1")

# Check status
status = manager.get_task_status(task_id)

# Cancel task
manager.cancel_task(task_id)
```

## Architecture

The package follows a modular architecture:

- `config.py`: Pydantic Settings configuration
- `app.py`: Celery application factory and setup
- `base.py`: Base task classes and utilities
- `manager.py`: Task management and monitoring
- `monitoring.py`: Monitoring and health check utilities
- `utils.py`: Common utilities and helpers

## Integration

This package is designed to be used by other PixCrawler packages:

- `pixcrawler-builder`: Image crawling and dataset generation tasks
- `pixcrawler-validator`: Image validation and integrity checking tasks
- `pixcrawler-backend`: API and web service tasks

Each package extends the base functionality provided here with package-specific task implementations.