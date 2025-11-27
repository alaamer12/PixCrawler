import logging
from sqlalchemy import select, func, text
from .config import settings

logger = logging.getLogger(__name__)

async def count_active_chunks() -> int | None:
    """
    Count the number of active chunks (status='processing').
    Uses the project's existing DB connection and models if available.
    """
    try:
        # Try to import from backend
        from backend.database.connection import AsyncSessionLocal
        from backend.models.chunks import JobChunk
        
        async with AsyncSessionLocal() as session:
            try:
                # Use ORM
                stmt = select(func.count()).where(JobChunk.status == 'processing')
                result = await session.execute(stmt)
                count = result.scalar()
                return count
            except Exception as e:
                logger.error(f"Error counting active chunks (ORM): {e}")
                return None
                
    except Exception:
        # Fallback if backend package is not accessible, structure changed, or config invalid
        logger.warning("Could not import or use backend models. Using fallback SQL.")
        return await _fallback_count_active_chunks()
    except Exception as e:
        logger.error(f"Unexpected error in count_active_chunks: {e}")
        return None

async def _fallback_count_active_chunks() -> int | None:
    """
    Fallback implementation using raw SQL and settings.DB_URL.
    """
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        
        # Ensure URL is async compatible
        db_url = settings.DB_URL
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            
        engine = create_async_engine(db_url)
        
        async with engine.connect() as conn:
            # Fallback SQL - assuming table name is 'job_chunks' and status is 'processing'
            # If table name is different, this needs to be updated.
            result = await conn.execute(text("SELECT COUNT(*) FROM job_chunks WHERE status='processing'"))
            count = result.scalar()
            return count
    except Exception as e:
        logger.error(f"Error counting active chunks (Fallback): {e}")
        return None
