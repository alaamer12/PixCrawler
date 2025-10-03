"""
Custom middleware for the PixCrawler backend.
"""

import time
import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response
from pixcrawler_logging import get_logger

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


async def security_headers_middleware(request: Request, call_next: Callable) -> Response:
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
    app.middleware("http")(request_logging_middleware)
    app.middleware("http")(security_headers_middleware)