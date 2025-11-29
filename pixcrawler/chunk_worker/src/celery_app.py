"""
Celery application entry point for the Chunk Worker.

This module uses the shared Celery application from celery_core.
"""

from celery_core.app import celery_app as app

# Auto-discover tasks in this package
app.autodiscover_tasks(['pixcrawler.chunk_worker.src.tasks'])

if __name__ == '__main__':
    app.start()
