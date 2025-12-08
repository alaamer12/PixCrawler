"""
Celery tasks for dataset lifecycle policies.
"""

import asyncio
from celery_core.app import get_celery_app
from celery_core.base import BaseTask
from utility.logging_config import get_logger

from backend.database.connection import AsyncSessionLocal
from backend.repositories.dataset_repository import DatasetRepository
from backend.repositories.policy_repository import (
    ArchivalPolicyRepository,
    CleanupPolicyRepository,
    PolicyExecutionLogRepository,
)
from backend.services.policy import PolicyExecutionService

logger = get_logger(__name__)
app = get_celery_app()


@app.task(
    bind=True,
    base=BaseTask,
    name="backend.tasks.policy.execute_archival_policies",
    # Result Storage
    ignore_result=False,
    acks_late=True,
    track_started=True,
    # Time Limits
    soft_time_limit=1800,
    time_limit=3600,
    # Rate Limiting (once per hour)
    rate_limit="1/h",
    # Serialization
    serializer="json",
)
def execute_archival_policies(self):
    """
    Periodic task to execute archival policies.
    """
    logger.info("Starting archival policy execution task")
    
    async def _execute():
        async with AsyncSessionLocal() as session:
            dataset_repo = DatasetRepository(session)
            archival_repo = ArchivalPolicyRepository(session)
            cleanup_repo = CleanupPolicyRepository(session)
            log_repo = PolicyExecutionLogRepository(session)
            
            service = PolicyExecutionService(
                dataset_repo, archival_repo, cleanup_repo, log_repo
            )
            
            stats = await service.execute_archival_policies()
            logger.info(f"Archival policy execution completed: {stats}")
            return stats

    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(_execute())
    except Exception as e:
        logger.error(f"Error executing archival policies: {e}")
        raise


@app.task(
    bind=True,
    base=BaseTask,
    name="backend.tasks.policy.execute_cleanup_policies",
    # Result Storage
    ignore_result=False,
    acks_late=True,
    track_started=True,
    # Time Limits
    soft_time_limit=1800,
    time_limit=3600,
    # Rate Limiting (once per hour)
    rate_limit="1/h",
    # Serialization
    serializer="json",
)
def execute_cleanup_policies(self):
    """
    Periodic task to execute cleanup policies.
    """
    logger.info("Starting cleanup policy execution task")
    
    async def _execute():
        async with AsyncSessionLocal() as session:
            dataset_repo = DatasetRepository(session)
            archival_repo = ArchivalPolicyRepository(session)
            cleanup_repo = CleanupPolicyRepository(session)
            log_repo = PolicyExecutionLogRepository(session)
            
            service = PolicyExecutionService(
                dataset_repo, archival_repo, cleanup_repo, log_repo
            )
            
            stats = await service.execute_cleanup_policies()
            logger.info(f"Cleanup policy execution completed: {stats}")
            return stats

    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        loop.run_until_complete(_execute())
    except Exception as e:
        logger.error(f"Error executing cleanup policies: {e}")
        raise
