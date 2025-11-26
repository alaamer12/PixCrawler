"""
PixCrawler Backend API Server

Main application entry point for the PixCrawler backend service.
"""

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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Lifespan context manager for FastAPI application.

    Handles startup and shutdown events including:
    - Redis connection for rate limiting
    - FastAPI-Limiter initialization

    In development: Redis is optional, will start with warning if unavailable
    In production: Redis is required, will fail startup if unavailable
    """
    import asyncio

    settings = get_settings()
    redis_connection = None
    is_production = settings.environment == "production"

    # Check if Redis is available
    redis_available = await check_redis_available(settings.redis.url)

    if not redis_available:
        if is_production:
            error_msg = (
                f"❌ FATAL: Redis is not available at {settings.redis.url}\n"
                "Redis is required in production for rate limiting and caching.\n"
                "Please start Redis or update REDIS_URL in your environment."
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        else:
            logger.warning(f"⚠️  Redis not available at {settings.redis.url}")
            logger.warning("⚠️  Rate limiting disabled. This is acceptable in development.")
            logger.warning("⚠️  For production, ensure Redis is running.")
    else:
        # Initialize Redis connection for rate limiting
        try:
            redis_connection = await redis.from_url(
                settings.redis.url,
                encoding="utf-8",
                decode_responses=True
            )
            await FastAPILimiter.init(redis_connection)
            logger.info(f"✅ FastAPI-Limiter initialized with Redis at {settings.redis.url}")
        except Exception as e:
            error_msg = f"Failed to initialize FastAPI-Limiter: {e}"
            if is_production:
                logger.error(f"❌ FATAL: {error_msg}")
                raise
            else:
                logger.warning(f"⚠️  {error_msg}")
                logger.warning("⚠️  Rate limiting disabled.")

    yield

    # Cleanup with timeout to prevent hanging
    if redis_connection:
        try:
            # Close with timeout to prevent hanging on shutdown

            await asyncio.wait_for(FastAPILimiter.close(), timeout=2.0)
            await asyncio.wait_for(redis_connection.close(), timeout=2.0)
            logger.info("FastAPI-Limiter and Redis connection closed")
        except asyncio.TimeoutError:
            logger.warning("Redis cleanup timed out (this is normal if Redis is unavailable)")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")

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
