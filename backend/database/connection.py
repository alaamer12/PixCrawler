"""
Database connection and session management.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.core.config import get_settings

settings = get_settings()

# Create async engine with asyncpg driver
# Convert postgresql:// to postgresql+asyncpg:// for async support
database_url = str(settings.database_url)
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    database_url,
    pool_size=10,  # Default pool size for Supabase
    max_overflow=20,  # Default max overflow
    echo=settings.debug,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.

    Yields:
        Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
