"""
Celery application entry point for the Chunk Worker.

This module configures the Celery app using settings from celery_core.
"""

import os
from celery import Celery
from celery_core.config import get_celery_settings

# Get settings
settings = get_celery_settings()

# Create Celery app
app = Celery('chunk_worker')

# Apply configuration
app.conf.update(settings.get_celery_config())

# Auto-discover tasks
# We point to the tasks module inside the chunk_worker package
app.autodiscover_tasks(['pixcrawler.chunk_worker.src.tasks'])

if __name__ == '__main__':
    app.start()
