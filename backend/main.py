"""
PixCrawler Backend API Server

Main application entry point for the PixCrawler backend service.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import redis.asyncio as redis
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi_limiter import FastAPILimiter
from fastapi_pagination import add_pagination

from backend.api.v1.router import api_router
from backend.core.config import get_settings
from backend.core.exceptions import setup_exception_handlers
from backend.core.middleware import setup_middleware
from utility.logging_config import get_logger

logger = get_logger(__name__)

# Resolve static directory relative to this file
STATIC_DIR = Path(__file__).parent / "static"


async def check_redis_available(redis_url: str) -> bool:
    """
    Check if Redis is available and responding.

    Args:
        redis_url: Redis connection URL

    Returns:
        True if Redis is available, False otherwise
    """
    try:
        test_connection = await redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2
        )
        await test_connection.ping()
        await test_connection.close()
        return True
    except Exception as e:
        logger.debug(f"Redis connection check failed: {e}")
        return False


async def handle_missing_redis(settings, redis_type: str = "cache") -> None:
    """
    Handle case when Redis is not available.
    
    Args:
        settings: Application settings
        redis_type: Type of Redis connection ("cache" or "limiter")
    """
    is_production = settings.environment == "production"

    if is_production:
        msg = build_fatal_redis_message(settings, redis_type)
        logger.error(msg)
        raise RuntimeError(msg)

    log_dev_redis_warning(settings, redis_type)


def build_fatal_redis_message(settings, redis_type: str) -> str:
    """
    Build fatal error message for production.
    
    Args:
        settings: Application settings
        redis_type: Type of Redis connection ("cache" or "limiter")
    """
    if redis_type == "cache":
        redis_url = settings.cache.get_redis_url()
        feature = "caching"
    else:
        redis_url = settings.rate_limit.get_redis_url()
        feature = "rate limiting"
    
    return (
        f"FATAL: Redis is not available at {redis_url}\n"
        f"Redis is required in production for {feature}.\n"
        f"Please start Redis or update {redis_type.upper()}_REDIS_* environment variables."
    )


def log_dev_redis_warning(settings, redis_type: str) -> None:
    """
    Log warnings for non-production environments.
    
    Args:
        settings: Application settings
        redis_type: Type of Redis connection ("cache" or "limiter")
    """
    if redis_type == "cache":
        redis_url = settings.cache.get_redis_url()
        feature = "Caching"
    else:
        redis_url = settings.rate_limit.get_redis_url()
        feature = "Rate limiting"
    
    logger.warning(f"WARNING: Redis not available at {redis_url}")
    logger.warning(f"WARNING: {feature} disabled. This is acceptable in development.")
    logger.warning("WARNING: For production, ensure Redis is running.")


async def initialize_cache(settings) -> redis.Redis | None:
    """
    Initialize Redis connection for caching when available.
    
    Args:
        settings: Application settings
        
    Returns:
        Redis connection or None if unavailable
    """
    if not settings.cache.enabled:
        logger.info("INFO: Caching is disabled via configuration")
        return None
    
    cache_url = settings.cache.get_redis_url()
    
    if not await check_redis_available(cache_url):
        await handle_missing_redis(settings, "cache")
        return None
    
    try:
        conn = await redis.from_url(
            cache_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2
        )
        logger.info(f"SUCCESS: Cache initialized with Redis at {cache_url}")
        return conn
    except Exception as e:
        logger.error(f"Failed to initialize cache: {e}")
        if settings.environment == "production":
            raise
        return None


async def initialize_limiter(settings) -> redis.Redis | None:
    """
    Initialize Redis connection + FastAPI-Limiter when available.
    
    Args:
        settings: Application settings
        
    Returns:
        Redis connection or None if unavailable
    """
    if not settings.rate_limit.enabled:
        logger.info("INFO: Rate limiting is disabled via configuration")
        return None
    
    limiter_url = settings.rate_limit.get_redis_url()
    
    if not await check_redis_available(limiter_url):
        await handle_missing_redis(settings, "limiter")
        return None
    
    try:
        conn = await redis.from_url(
            limiter_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2
        )
        await FastAPILimiter.init(conn)
        logger.info(f"SUCCESS: FastAPI-Limiter initialized with Redis at {limiter_url}")
        return conn
    except Exception as e:
        await handle_limiter_error(e, settings)
        return None


async def handle_limiter_error(error: Exception, settings) -> None:
    """
    Handle FastAPI-Limiter init errors based on environment.
    
    Args:
        error: Exception that occurred
        settings: Application settings
    """
    is_production = settings.environment == "production"

    msg = f"Failed to initialize FastAPI-Limiter: {error}"
    if is_production:
        logger.error(f"FATAL: {msg}")
        raise error

    logger.warning(f"WARNING: {msg}")
    logger.warning("WARNING: Rate limiting disabled.")


async def cleanup_resources(cache_conn: redis.Redis | None, limiter_conn: redis.Redis | None) -> None:
    """
    Cleanup Redis connections safely with timeout.
    
    Args:
        cache_conn: Cache Redis connection or None
        limiter_conn: Limiter Redis connection or None
    """
    try:
        # Close limiter
        if limiter_conn:
            await asyncio.wait_for(FastAPILimiter.close(), timeout=2.0)
            await asyncio.wait_for(limiter_conn.close(), timeout=2.0)
            logger.info("SUCCESS: FastAPI-Limiter and limiter Redis connection closed")
        
        # Close cache
        if cache_conn:
            await asyncio.wait_for(cache_conn.close(), timeout=2.0)
            logger.info("SUCCESS: Cache Redis connection closed")

    except asyncio.TimeoutError:
        logger.warning("WARNING: Redis cleanup timed out (normal if Redis was down on shutdown)")
    except Exception as e:
        logger.error(f"ERROR: Error closing Redis connections: {e}")


def log_configuration_status(settings) -> None:
    """
    Log configuration status on startup.
    
    Shows which services are configured and provides warnings/errors
    for production requirements.
    
    Args:
        settings: Application settings
    """
    import os
    
    is_production = settings.environment in ('production', 'prod')
    is_azure = bool(os.getenv('WEBSITE_INSTANCE_ID'))
    
    logger.info("=" * 70)
    logger.info("CONFIGURATION STATUS")
    logger.info("=" * 70)
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug Mode: {settings.debug}")
    logger.info(f"Running on Azure: {is_azure}")
    logger.info("-" * 70)
    
    # Redis/Cache status
    cache_host = settings.cache.redis_host
    cache_enabled = settings.cache.enabled
    cache_localhost = cache_host in ('localhost', '127.0.0.1')
    
    logger.info(f"Cache: {'Enabled' if cache_enabled else 'Disabled'}")
    logger.info(f"  Redis Host: {cache_host}")
    if is_production and cache_localhost:
        logger.error("  ❌ ERROR: Cache using localhost in production!")
    elif cache_localhost:
        logger.warning("  ⚠️  WARNING: Cache using localhost (OK for development)")
    else:
        logger.info("  ✅ Cache properly configured")
    
    # Rate Limiter status
    limiter_host = settings.rate_limit.redis_host
    limiter_enabled = settings.rate_limit.enabled
    limiter_localhost = limiter_host in ('localhost', '127.0.0.1')
    
    logger.info(f"Rate Limiter: {'Enabled' if limiter_enabled else 'Disabled'}")
    logger.info(f"  Redis Host: {limiter_host}")
    if is_production and not limiter_enabled:
        logger.error("  ❌ ERROR: Rate limiting disabled in production!")
    elif is_production and limiter_localhost:
        logger.error("  ❌ ERROR: Rate limiter using localhost in production!")
    elif limiter_localhost:
        logger.warning("  ⚠️  WARNING: Rate limiter using localhost (OK for development)")
    else:
        logger.info("  ✅ Rate limiter properly configured")
    
    # Celery status
    celery_broker = settings.celery.broker_url
    celery_localhost = 'localhost' in celery_broker or '127.0.0.1' in celery_broker
    
    logger.info(f"Celery Broker: {celery_broker[:50]}...")
    if is_production and celery_localhost:
        logger.error("  ❌ ERROR: Celery using localhost in production!")
    elif celery_localhost:
        logger.warning("  ⚠️  WARNING: Celery using localhost (OK for development)")
    else:
        logger.info("  ✅ Celery properly configured")
    
    # Azure Storage status
    storage_provider = os.getenv('STORAGE_PROVIDER', 'local').lower()
    logger.info(f"Storage Provider: {storage_provider}")
    
    if storage_provider == 'azure':
        has_azure_config = (
            settings.azure.blob.connection_string is not None or
            (settings.azure.blob.account_name is not None and settings.azure.blob.account_key is not None)
        )
        if is_production and not has_azure_config:
            logger.error("  ❌ ERROR: Azure storage not configured in production!")
        elif has_azure_config:
            logger.info("  ✅ Azure Blob Storage configured")
        else:
            logger.warning("  ⚠️  WARNING: Azure storage not configured")
    
    logger.info("=" * 70)
    
    if is_production:
        logger.info("🚀 PRODUCTION MODE: All services must be properly configured")
    else:
        logger.info("🔧 DEVELOPMENT MODE: Localhost services are acceptable")
    
    logger.info("=" * 70)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown of Redis connections for cache and rate limiting.
    Implements graceful degradation in development and fail-fast in production.
    
    Args:
        app: FastAPI application instance
        
    Yields:
        None during application runtime
    """
    settings = get_settings()
    
    logger.info("Starting PixCrawler API...")
    logger.info(f"Environment: {settings.environment}")
    
    # Log configuration status
    log_configuration_status(settings)
    
    # Initialize cache connection
    cache_conn = await initialize_cache(settings)
    
    # Initialize rate limiter connection
    limiter_conn = await initialize_limiter(settings)
    
    logger.info("Application startup complete")
    
    yield
    
    logger.info("Shutting down PixCrawler API...")
    await cleanup_resources(cache_conn, limiter_conn)
    logger.info("Application shutdown complete")
def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="PixCrawler API",
        description="🖼️ Automated Image Dataset Builder for ML/AI | Multi-source scraping, AI-powered validation, and ML-ready exports",
        version="1.0.0",
        contact={
            "name": "PixCrawler Team",
            "url": "https://github.com/alaamer12/pixcrawler",
            "email": "support@pixcrawler.com",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        docs_url="/docs",  # Enable default FastAPI docs
        redoc_url="/redoc",  # Enable default ReDoc
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Setup CORS
    # noinspection PyTypeChecker
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.security.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Setup custom middleware
    setup_middleware(app)

    # Setup exception handlers
    setup_exception_handlers(app)

    # Mount static files for custom docs styling
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
        logger.info(f"Static files mounted at /static from {STATIC_DIR}")
    else:
        logger.warning(f"Static directory not found at {STATIC_DIR}")

    # Custom documentation routes (optional - uncomment to use custom docs instead of default)
    # @app.get("/docs", include_in_schema=False)
    # async def custom_swagger_ui_html():
    #     """Serve custom Swagger UI with PixCrawler branding."""
    #     swagger_file = STATIC_DIR / "swagger-ui.html"
    #     if swagger_file.exists():
    #         with open(swagger_file, "r", encoding="utf-8") as f:
    #             return HTMLResponse(content=f.read())
    #     return HTMLResponse(content="<h1>Swagger UI not found</h1>", status_code=404)

    # @app.get("/redoc", include_in_schema=False)
    # async def custom_redoc_html():
    #     """Serve custom ReDoc with PixCrawler branding."""
    #     redoc_file = STATIC_DIR / "redoc.html"
    #     if redoc_file.exists():
    #         with open(redoc_file, "r", encoding="utf-8") as f:
    #             return HTMLResponse(content=f.read())
    #     return HTMLResponse(content="<h1>ReDoc not found</h1>", status_code=404)

    # Root-level health check (no prefix) # Placeholder health for conventional use
    @app.get("/health", tags=["Health"], include_in_schema=True)
    async def root_health_check():
        """Root-level health check endpoint."""
        return {"status": "healthy", "service": "PixCrawler API"}

    # Include API routes
    app.include_router(api_router)

    # Add pagination support
    add_pagination(app)
    logger.info("Pagination support added to FastAPI app")

    logger.info("PixCrawler API initialized with FastAPI documentation")
    logger.info("Swagger UI: http://localhost:8000/docs")
    logger.info("ReDoc: http://localhost:8000/redoc")
    logger.info("OpenAPI Schema: http://localhost:8000/openapi.json")

    return app

app = create_app()

def main() -> None:
    """Run the application server."""
    settings = get_settings()
    development = settings.environment == "development"
    if development:
        uvicorn.run(app, reload=True)
    else:
        uvicorn.run(
            "backend.main:app",
            host=settings.host,
            port=settings.port,
            reload=settings.environment == "development",
            log_level=settings.log_level.lower(),
        )


if __name__ == "__main__":
    main()
