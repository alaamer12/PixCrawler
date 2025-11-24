"""
Celery tasks for backend service.
"""
import asyncio
from celery_core.app import get_celery_app
from backend.services.crawl_job import execute_crawl_job
from utility.logging_config import get_logger

logger = get_logger(__name__)
app = get_celery_app()

@app.task(name="backend.tasks.run_crawl_job", bind=True)
def run_crawl_job_task(self, job_id: int):
    """
    Celery task to run a crawl job.
    """
    logger.info(f"Starting crawl job task for job {job_id}")
    
    try:
        # Run the async execution function in a new event loop
        # or the current one if available (Celery workers usually don't have a running loop)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(execute_crawl_job(job_id))
        loop.close()
        
    except Exception as e:
        logger.error(f"Crawl job task failed: {e}")
        raise
