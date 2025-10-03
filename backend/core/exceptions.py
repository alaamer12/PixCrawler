"""
Custom exceptions and error handling for the PixCrawler backend.
"""

from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pixcrawler_logging import get_logger

logger = get_logger(__name__)


class PixCrawlerException(Exception):
    """Base exception for PixCrawler application."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(PixCrawlerException):
    """Raised when data validation fails."""
    pass


class NotFoundError(PixCrawlerException):
    """Raised when a requested resource is not found."""
    pass


class AuthenticationError(PixCrawlerException):
    """Raised when authentication fails."""
    pass


class AuthorizationError(PixCrawlerException):
    """Raised when authorization fails."""
    pass


class ExternalServiceError(PixCrawlerException):
    """Raised when external service calls fail."""
    pass


class RateLimitError(PixCrawlerException):
    """Raised when rate limits are exceeded."""
    pass


async def pixcrawler_exception_handler(
    request: Request, exc: PixCrawlerException
) -> JSONResponse:
    """Handle custom PixCrawler exceptions."""
    logger.error(
        "PixCrawler exception occurred",
        extra={
            "exception_type": type(exc).__name__,
            "message": exc.message,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method,
        }
    )

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    if isinstance(exc, ValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, NotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, AuthenticationError):
        status_code = status.HTTP_401_UNAUTHORIZED
    elif isinstance(exc, AuthorizationError):
        status_code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, RateLimitError):
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
    elif isinstance(exc, ExternalServiceError):
        status_code = status.HTTP_502_BAD_GATEWAY

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "type": type(exc).__name__,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""
    logger.warning(
        "HTTP exception occurred",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
            "method": request.method,
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "HTTPException",
                "message": exc.detail,
                "status_code": exc.status_code,
            }
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.exception(
        "Unexpected exception occurred",
        extra={
            "exception_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method,
        }
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "InternalServerError",
                "message": "An unexpected error occurred",
            }
        },
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup exception handlers for the FastAPI application."""
    app.add_exception_handler(PixCrawlerException, pixcrawler_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
