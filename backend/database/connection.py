"""Database connection and session management.

This module provides database connectivity using SQLAlchemy async engine
with PostgreSQL/Supabase backend. Implements dependency injection pattern
for FastAPI integration with support for easy database provider switching.

Public Functions:
    get_engine: Create and return cached database engine
    get_session_maker: Create and return cached session maker
    get_db: FastAPI dependency for database sessions
    get_async_session: Alias for get_db (backward compatibility)
    init_db: Initialize database connection on startup
    close_db: Close database connections on shutdown

Features:
    - Async SQLAlchemy engine with asyncpg driver
    - Session management with proper cleanup
    - FastAPI dependency injection support
    - Connection pooling optimized per provider
    - Automatic commit/rollback handling
    - Supabase session/transaction pooler support
"""

from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.core.config import get_settings
from utility.logging_config import get_logger

__all__ = ["get_engine", "get_session_maker", "get_db", "get_async_session", "init_db", "close_db"]

logger = get_logger(__name__)


@lru_cache
def get_engine() -> AsyncEngine:
    """Create and return cached database engine.

    This function creates a single engine instance that is reused across
    the application. The engine is configured based on the database provider
    (Supabase or PostgreSQL) with appropriate connection pooling settings.

    Returns:
        AsyncEngine: SQLAlchemy async engine (cached singleton)
    """
    settings = get_settings()

    # Get connection URL and convert to asyncpg driver
    database_url = settings.database.get_connection_url()
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine_kwargs = {
        "url": database_url,
        "echo": settings.database.echo or settings.debug,
        "future": True,
        "pool_pre_ping": settings.database.pool_pre_ping,
        "pool_size": settings.database.pool_size,
        "max_overflow": settings.database.max_overflow,
        "pool_recycle": 3600,  # Recycle connections after 1 hour
    }

    # Base connect_args
    connect_args = {
        "timeout": 30,
        "command_timeout": 60,
    }

    # Supabase-specific optimizations
    is_supabase = settings.database.provider.lower() == "supabase"
    if is_supabase:
        # Supabase has connection limits, so we use smaller pool
        engine_kwargs["pool_size"] = min(settings.database.pool_size, 5)
        engine_kwargs["max_overflow"] = min(settings.database.max_overflow, 5)
        # Supabase connections can be flaky, enable pre-ping
        engine_kwargs["pool_pre_ping"] = True

    # Disable prepared statements for transaction pooler only
    # Session pooler and direct connections support prepared statements
    if settings.database.connection_mode == "transaction_pooler":
        logger.info("Using transaction pooler mode with prepared statements disabled")
        logger.info(f"Connection mode: {settings.database.connection_mode}")
        logger.info(f"Host: {settings.database.host}")

        # Disable at asyncpg level
        connect_args["statement_cache_size"] = 0

        # Disable at SQLAlchemy level
        engine_kwargs["execution_options"] = {"prepared_statement_cache_size": 0}
    elif is_supabase:
        logger.info(
            f"Using {settings.database.connection_mode} mode (prepared statements enabled)"
        )
        logger.info(f"Host: {settings.database.host}")

    # Set connect_args
    engine_kwargs["connect_args"] = connect_args

    logger.debug(f"Creating database engine with config: provider={settings.database.provider}, "
                f"mode={settings.database.connection_mode}, pool_size={engine_kwargs['pool_size']}")
    
    return create_async_engine(**engine_kwargs)


@lru_cache
def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """Create and return cached session maker.

    Returns:
        async_sessionmaker[AsyncSession]: Async session maker factory (cached singleton)
    """
    engine = get_engine()
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency.

    This is a FastAPI dependency that provides a database session
    for each request. The session is automatically closed after use.

    Yields:
        AsyncSession: Database session with automatic cleanup
        
    Example:
        ```python
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
        ```
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


# Backward compatibility alias
get_async_session = get_db
get_session = get_db


async def init_db() -> None:
    """Initialize database connection.

    This function should be called on application startup to ensure
    the database connection is established and ready.

    Example:
        @app.on_event("startup")
        async def startup():
            await init_db()
    """
    settings = get_settings()
    engine = get_engine()

    # Test connection
    async with engine.begin() as conn:
        # Simple query to verify connection
        await conn.execute(text("SELECT 1"))

    logger.info(f"Database connected: {settings.database.provider} @ {settings.database.host or 'localhost'}")


async def close_db() -> None:
    """Close database connections.

    This function should be called on application shutdown to properly
    close all database connections and clean up resources.

    Example:
        @app.on_event("shutdown")
        async def shutdown():
            await close_db()
    """
    try:
        engine = get_engine()
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.warning(f"Error closing database connections: {e}")
