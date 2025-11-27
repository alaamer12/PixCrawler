"""
PixCrawler Backend API Server

Main application entry point for the PixCrawler backend service.
"""
from __future__ import annotations

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
    except Exception:
        return False


async def handle_missing_redis(settings) -> None:
    """Handle case when Redis is not available."""
    is_production = settings.environment == "production"

    if is_production:
        msg = build_fatal_redis_message(settings)
        logger.error(msg)
        raise RuntimeError(msg)

    log_dev_redis_warning(settings)


def build_fatal_redis_message(settings) -> str:
    """Build fatal error message for production."""
    return (
        f"❌ FATAL: Redis is not available at {settings.redis.url}\n"
        "Redis is required in production for rate limiting and caching.\n"
        "Please start Redis or update REDIS_URL in your environment."
    )


def log_dev_redis_warning(settings) -> None:
    """Log warnings for non-production environments."""
    logger.warning(f"⚠️  Redis not available at {settings.redis.url}")
    logger.warning("⚠️  Rate limiting disabled. This is acceptable in development.")
    logger.warning("⚠️  For production, ensure Redis is running.")


# noinspection D
async def initialize_limiter(settings) -> redis.Redis | None:
    """Initialize Redis connection + FastAPI-Limiter when available."""
    try:
        conn = await redis.from_url(
            settings.redis.url,
            encoding="utf-8",
            decode_responses=True
        )
        await FastAPILimiter.init(conn)
        logger.info(f"✅ FastAPI-Limiter initialized with Redis at {settings.redis.url}")
        return conn

    except Exception as e:
        await handle_limiter_error(e, settings)
        return None


async def handle_limiter_error(error: Exception, settings) -> None:
    """Handle FastAPI-Limiter init errors based on environment."""
    is_production = settings.environment == "production"

    msg = f"Failed to initialize FastAPI-Limiter: {error}"
    if is_production:
        logger.error(f"❌ FATAL: {msg}")
        raise error

    logger.warning(f"⚠️  {msg}")
    logger.warning("⚠️  Rate limiting disabled.")


async def cleanup_resources(conn: redis.Redis) -> None:
    """Cleanup Redis + limiter safely with timeout."""
    try:
        await asyncio.wait_for(FastAPILimiter.close(), timeout=2.0)
        await asyncio.wait_for(conn.close(), timeout=2.0)
        logger.info("FastAPI-Limiter and Redis connection closed")

    except asyncio.TimeoutError:
        logger.warning("Redis cleanup timed out (normal if Redis was down on shutdown)")
    except Exception as e:
        logger.error(f"Error closing Redis connection: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()

    if not await check_redis_available(settings.redis.url):
        await handle_missing_redis(settings)
        yield
        return

    conn = await initialize_limiter(settings)
    yield

    if conn:
        await cleanup_resources(conn)
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
        docs_url=None,  # Disable default docs
        redoc_url=None,  # Disable default redoc
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

    # Custom documentation routes
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        """Serve custom Swagger UI with PixCrawler branding."""
        swagger_file = STATIC_DIR / "swagger-ui.html"
        if swagger_file.exists():
            with open(swagger_file, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        return HTMLResponse(content="<h1>Swagger UI not found</h1>", status_code=404)

    @app.get("/redoc", include_in_schema=False)
    async def custom_redoc_html():
        """Serve custom ReDoc with PixCrawler branding."""
        redoc_file = STATIC_DIR / "redoc.html"
        if redoc_file.exists():
            with open(redoc_file, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        return HTMLResponse(content="<h1>ReDoc not found</h1>", status_code=404)

    # Root-level health check (no prefix) # Placeholder health for conventional use
    @app.get("/health", tags=["Health"], include_in_schema=True)
    async def root_health_check():
        """Root-level health check endpoint."""
        return {"status": "healthy", "service": "PixCrawler API"}

    # Include API routes
    app.include_router(api_router, prefix="/api")

    # Add pagination support
    add_pagination(app)
    logger.info("Pagination support added to FastAPI app")

    logger.info("✨ PixCrawler API initialized with custom documentation")
    logger.info("📚 Swagger UI: http://localhost:8000/docs")
    logger.info("📖 ReDoc: http://localhost:8000/redoc")

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
