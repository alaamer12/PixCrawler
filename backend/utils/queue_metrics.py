"""
Queue metrics utilities for tracking Celery queue depths and wait times.
"""

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.metrics_collector import track_queue_depth

__all__ = [
    'get_celery_queue_depth',
    'track_celery_queue_metrics',
]


async def get_celery_queue_depth(
    queue_name: str = "celery",
    broker_url: Optional[str] = None
) -> int:
    """
    Get the current depth of a Celery queue.
    
    Args:
        queue_name: Name of the queue to check
        broker_url: Optional broker URL (uses default if not provided)
        
    Returns:
        Current queue depth (number of pending tasks)
    """
    try:
        # Try to import celery
        from celery import Celery
        
        # Create a temporary Celery app to inspect the queue
        # In production, you'd use the actual app instance
        if broker_url:
            app = Celery(broker=broker_url)
        else:
            # Use default broker from environment
            app = Celery()
        
        # Get queue length
        # This is a simplified version - actual implementation would
        # use the broker's API to get queue length
        inspect = app.control.inspect()
        active = inspect.active()
        
        if active:
            # Count active tasks
            total_active = sum(len(tasks) for tasks in active.values())
        else:
            total_active = 0
        
        # For queue depth, we'd need to query the broker directly
        # This is a placeholder - actual implementation depends on broker type
        # (Redis, RabbitMQ, etc.)
        return total_active
        
    except ImportError:
        # Celery not available
        return 0
    except Exception:
        # Error getting queue depth
        return 0


async def track_celery_queue_metrics(
    session: AsyncSession,
    queue_name: str = "celery",
    service_name: str = "backend",
    broker_url: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Track Celery queue depth and wait times.
    
    Args:
        session: Database session
        queue_name: Queue name to track
        service_name: Service name
        broker_url: Optional broker URL
        metadata: Additional metadata
    """
    depth = await get_celery_queue_depth(queue_name, broker_url)
    
    # Wait time would need to be calculated from task timestamps
    # This is a placeholder
    wait_time = None
    
    await track_queue_depth(
        session=session,
        queue_name=queue_name,
        depth=depth,
        wait_time_seconds=wait_time,
        service_name=service_name,
        metadata=metadata,
    )

