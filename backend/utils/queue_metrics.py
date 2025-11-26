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
    Get the current depth of a Celery queue using Redis.
    
    Args:
        queue_name: Name of the queue to check
        broker_url: Optional broker URL (uses default if not provided)
        
    Returns:
        Current queue depth (number of pending tasks)
    """
    try:
        # Import here to avoid circular imports
        from backend.core.settings.redis import get_redis_settings
        import redis.asyncio as redis
        
        if not broker_url:
            settings = get_redis_settings()
            broker_url = settings.url
            
        # Connect to Redis
        client = redis.from_url(broker_url)
        
        try:
            # Get queue length directly from Redis
            # Celery stores tasks in a list with the queue name
            depth = await client.llen(queue_name)
            return int(depth)
        finally:
            await client.aclose()
            
    except Exception as e:
        # Fallback or log error
        print(f"Error getting queue depth: {e}")
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

