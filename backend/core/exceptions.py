"""
Custom exceptions and error handling for the PixCrawler backend.

This module provides a comprehensive exception hierarchy and error handling
system for the PixCrawler backend, including custom exception classes,
HTTP exception handlers, and structured error responses.

Classes:
    PixCrawlerException: Base exception for all application-specific errors
    ValidationError: Data validation failures
    NotFoundError: Resource not found errors
    AuthenticationError: Authentication failures
    AuthorizationError: Authorization failures
    ExternalServiceError: External service call failures
    RateLimitError: Rate limit exceeded errors

Functions:
    pixcrawler_exception_handler: Handler for custom PixCrawler exceptions
    http_exception_handler: Handler for FastAPI HTTP exceptions
    general_exception_handler: Handler for unexpected exceptions
    setup_exception_handlers: Setup all exception handlers for FastAPI app

Features:
    - Structured error responses with consistent format_
    - Comprehensive logging of all exceptions
    - Proper HTTP status code mapping
    - Request context in error logs
"""

from typing import Any, Optional, Dict

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from utility.logging_config import get_logger

__all__ = [
    'PixCrawlerException',
    'ValidationError',
    'NotFoundError',
    'AuthenticationError',
    'AuthorizationError',
    'ExternalServiceError',
    'RateLimitError',
    'setup_exception_handlers'
]

logger = get_logger(__name__)


class PixCrawlerException(Exception):
    """
    Base exception for PixCrawler application.

    All custom exceptions in the application should inherit from this class
    to ensure consistent error handling and logging.

    Attributes:
        message: Human-readable error message
        details: Optional additional error details
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize PixCrawler exception.

        Args:
            message: Human-readable error message
            details: Optional additional error details
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(PixCrawlerException):
    """
    Raised when data validation fails.

    Used for input validation errors, schema validation failures,
    and other data-related validation issues.
    """
    pass


class NotFoundError(PixCrawlerException):
    """
    Raised when a requested resource is not found.

    Used for database record not found, file not found,
    and other resource availability issues.
    """
    pass


class AuthenticationError(PixCrawlerException):
    """
    Raised when authentication fails.

    Used for invalid credentials, expired tokens,
    and other authentication-related issues.
    """
    pass


class AuthorizationError(PixCrawlerException):
    """
    Raised when authorization fails.

    Used for insufficient permissions, access denied,
    and other authorization-related issues.
    """
    pass


class ExternalServiceError(PixCrawlerException):
    """
    Raised when external service calls fail.

    Used for API call failures, service unavailability,
    and other external service integration issues.
    """
    pass


class RateLimitError(PixCrawlerException):
    """
    Raised when rate limits are exceeded.

    Used for API rate limiting, request throttling,
    and other rate limit enforcement.
    """
    pass


class RateLimitExceeded(PixCrawlerException):
    """
    Raised when user tier rate limits are exceeded.

    Used for tier-based rate limiting with detailed
    information about current usage and limits.

    Attributes:
        tier: User tier name
        current_usage: Current usage count
        limit: Tier limit
        request_type: Type of request that exceeded limit
    """

    def __init__(
        self,
        tier: str = None,
        current_usage: int = None,
        limit: int = None,
        request_type: str = None,
        message: str = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize RateLimitExceeded exception.

        Args:
            tier: User tier name
            current_usage: Current usage count
            limit: Tier limit
            request_type: Type of request that exceeded limit
            message: Custom error message
            details: Optional additional error details
        """
        self.tier = tier
        self.current_usage = current_usage
        self.limit = limit
        self.request_type = request_type

        if message is None:
            message = f"Rate limit exceeded for tier '{tier}'"

        if details is None:
            details = {}

        if tier:
            details["tier"] = tier
        if current_usage is not None:
            details["current_usage"] = current_usage
        if limit is not None:
            details["limit"] = limit
        if request_type:
            details["request_type"] = request_type

        super().__init__(message, details)


async def pixcrawler_exception_handler(
    request: Request, exc: PixCrawlerException
) -> JSONResponse:
    """
    Handle custom PixCrawler exceptions.

    Provides structured error responses for all custom application
    exceptions with appropriate HTTP status codes and logging.

    Args:
        request: FastAPI request object
        exc: PixCrawler exception instance

    Returns:
        JSON response with error details
    """
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
    """
    Handle FastAPI HTTP exceptions.

    Provides consistent error response format_ for standard
    FastAPI HTTP exceptions.

    Args:
        request: FastAPI request object
        exc: HTTP exception instance

    Returns:
        JSON response with error details
    """
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
    """
    Handle unexpected exceptions.

    Catches all unhandled exceptions and provides a generic
    error response while logging the full exception details.

    Args:
        request: FastAPI request object
        exc: Exception instance

    Returns:
        JSON response with generic error message
    """
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
    """
    Setup exception handlers for the FastAPI application.

    Registers all custom exception handlers with the FastAPI
    application instance.

    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(PixCrawlerException, pixcrawler_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
