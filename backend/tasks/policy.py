"""
Celery tasks for dataset lifecycle policies.
"""

import asyncio
from celery import shared_task
from loguru import logger

from backend.database.session import AsyncSessionLocal
from backend.repositories.dataset_repository import DatasetRepository
from backend.repositories.policy_repository import (
    ArchivalPolicyRepository,
    CleanupPolicyRepository,
    PolicyExecutionLogRepository,
)
from backend.services.policy import PolicyExecutionService


@shared_task(name="tasks.policy.execute_archival_policies")
def execute_archival_policies():
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


@shared_task(name="tasks.policy.execute_cleanup_policies")
def execute_cleanup_policies():
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
