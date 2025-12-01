"""
Database connection and session management.

This module provides production-grade database connection management with:
- Connection pooling optimized for Supabase
- Pre-ping health checks to detect stale connections
- Graceful connection cleanup
- Configurable pool size and overflow
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from backend.core.config import get_settings
from utility.logging_config import get_logger

logger = get_logger(__name__)

settings = get_settings()

# Create async engine with asyncpg driver
# Convert postgresql:// to postgresql+asyncpg:// for async support
database_url = str(settings.database.url)
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Create engine with production-grade settings
engine = create_async_engine(
    database_url,
    # Connection pooling optimized for Supabase (recommended: 5-10 for free tier)
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    # Pre-ping to check connection health before using from pool
    pool_pre_ping=True,
    # Connection timeout (30 seconds)
    connect_args={
        "timeout": 30,
        "command_timeout": 60,
    },
    # Echo SQL in debug mode
    echo=settings.debug,
    # Pool recycle to prevent stale connections (1 hour)
    pool_recycle=3600,
)

logger.info(
    f"Database engine created with pool_size={settings.database.pool_size}, "
    f"max_overflow={settings.database.max_overflow}"
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    
    Provides a database session with automatic cleanup and error handling.
    Uses connection pooling with pre-ping health checks.

    Yields:
        AsyncSession: Database session
        
    Example:
        ```python
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_session)):
            result = await db.execute(select(User))
            return result.scalars().all()
        ```
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


# Alias for compatibility
get_db = get_session
