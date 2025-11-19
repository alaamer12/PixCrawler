"""
Custom middleware for the PixCrawler backend.
"""

import time
import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from utility.logging_config import get_logger
from backend.core.config import get_settings

logger = get_logger(__name__)


async def request_logging_middleware(request: Request, call_next: Callable) -> Response:
    """Log incoming requests and responses."""
    request_id = str(uuid.uuid4())
    start_time = time.time()

    # Add request ID to request state
    request.state.request_id = request_id

    logger.info(
        "Request started",
        extra={
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
    )

    response = await call_next(request)

    process_time = time.time() - start_time

    logger.info(
        "Request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "process_time": round(process_time, 4),
        }
    )

    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(round(process_time, 4))

    return response


async def security_headers_middleware(request: Request,
                                      call_next: Callable) -> Response:
    """Add security headers to responses."""
    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    return response


def setup_middleware(app: FastAPI) -> None:
    """Setup middleware for the FastAPI application."""
    settings = get_settings()

    # GZip compression for responses > 500 bytes
    app.add_middleware(
        GZipMiddleware,
        minimum_size=500,
        compresslevel=6  # Balance between speed and compression
    )

    # Trusted host validation (production)
    if settings.environment == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.allowed_hosts,
            www_redirect=True
        )

    # HTTPS redirect (production)
    if settings.environment == "production" and settings.force_https:
        app.add_middleware(HTTPSRedirectMiddleware)

    # Custom middleware
    app.middleware("http")(request_logging_middleware)
    app.middleware("http")(security_headers_middleware)
