"""
Custom exception classes for the PixCrawler project.

This module provides a comprehensive error classification system for retry logic.
Errors are classified into two main categories:
- PermanentError: Errors that should NOT be retried (e.g., 404, validation failures)
- TransientError: Errors that MAY succeed on retry (e.g., timeouts, rate limits)
"""

from typing import Type


class PixCrawlerError(Exception):
    """Base exception for PixCrawler related errors."""
    pass


class ConfigurationError(PixCrawlerError):
    """Exception raised for errors in configuration settings."""
    pass


class DownloadError(PixCrawlerError):
    """Exception raised for errors during the image download process."""
    pass


class GenerationError(PixCrawlerError):
    """Exception raised for errors during the image generation process."""
    pass


class CrawlerError(PixCrawlerError):
    """Base exception for all crawler-related errors."""
    pass


class CrawlerInitializationError(CrawlerError):
    """Exception raised when a crawler fails to initialize."""
    pass


class CrawlerExecutionError(CrawlerError):
    """Exception raised when a crawler encounters an error during its execution."""
    pass


# ============================================================================
# Error Classification for Retry Logic
# ============================================================================


class PermanentError(Exception):
    """
    Base class for errors that should NOT be retried.
    
    These errors indicate problems that will not be resolved by retrying
    the operation. Examples include validation failures, authentication errors,
    and resource not found errors.
    
    Retry Behavior: Fail immediately without retry
    """
    pass


class TransientError(Exception):
    """
    Base class for errors that MAY succeed on retry.
    
    These errors indicate temporary problems that might be resolved by
    retrying the operation after a delay. Examples include network timeouts,
    rate limiting, and temporary service unavailability.
    
    Retry Behavior: Retry with exponential backoff (Tenacity)
    """
    pass


# ============================================================================
# Permanent Errors (No Retry)
# ============================================================================


class ValidationError(PermanentError):
    """
    Validation failures - data does not meet requirements.
    
    Examples:
    - Invalid input format
    - Missing required fields
    - Data constraint violations
    
    Retry Behavior: Fail immediately without retry
    HTTP Status: N/A (application-level validation)
    """
    pass


class NotFoundError(PermanentError):
    """
    Resource not found (HTTP 404).
    
    The requested resource does not exist and retrying will not help.
    
    Retry Behavior: Fail immediately without retry
    HTTP Status: 404 Not Found
    """
    pass


class AuthenticationError(PermanentError):
    """
    Authentication or authorization failures (HTTP 401, 403).
    
    Examples:
    - Invalid credentials
    - Expired tokens
    - Insufficient permissions
    
    Retry Behavior: Fail immediately without retry
    HTTP Status: 401 Unauthorized, 403 Forbidden
    """
    pass


class BadRequestError(PermanentError):
    """
    Bad request - malformed or invalid request (HTTP 400).
    
    The request is syntactically incorrect or violates API constraints.
    
    Retry Behavior: Fail immediately without retry
    HTTP Status: 400 Bad Request
    """
    pass


# ============================================================================
# Transient Errors (Retry with Backoff)
# ============================================================================


class RateLimitError(TransientError):
    """
    Rate limit exceeded (HTTP 429).
    
    The client has sent too many requests in a given time period.
    Should respect Retry-After header if present.
    
    Retry Behavior: Retry with exponential backoff + Retry-After header
    HTTP Status: 429 Too Many Requests
    """
    pass


class ServiceUnavailableError(TransientError):
    """
    Service temporarily unavailable (HTTP 503, 504).
    
    Examples:
    - Server overloaded
    - Maintenance mode
    - Gateway timeout
    
    Retry Behavior: Retry with exponential backoff
    HTTP Status: 503 Service Unavailable, 504 Gateway Timeout
    """
    pass


class TimeoutException(TransientError):
    """
    Network timeout during operation.
    
    The operation took too long to complete. May succeed if retried
    with a longer timeout or when network conditions improve.
    
    Retry Behavior: Retry with exponential backoff
    HTTP Status: N/A (network-level timeout)
    """
    pass


class NetworkError(TransientError):
    """
    Network connectivity issues.
    
    Examples:
    - Connection refused
    - DNS resolution failure
    - Network unreachable
    
    Retry Behavior: Retry with exponential backoff
    HTTP Status: N/A (network-level error)
    """
    pass


# ============================================================================
# Error Classification Functions
# ============================================================================


# HTTP status code to exception type mapping
HTTP_ERROR_MAP = {
    400: BadRequestError,
    401: AuthenticationError,
    403: AuthenticationError,
    404: NotFoundError,
    429: RateLimitError,
    503: ServiceUnavailableError,
    504: ServiceUnavailableError,
}


def classify_http_error(status_code: int) -> Type[Exception]:
    """
    Classify HTTP status codes into permanent or transient errors.
    
    This function maps HTTP status codes to appropriate exception types
    to guide retry logic. Unmapped status codes default to PermanentError
    to avoid unnecessary retries.
    
    Args:
        status_code: HTTP status code (e.g., 404, 429, 503)
        
    Returns:
        Exception class (PermanentError or TransientError subclass)
        
    Examples:
        >>> classify_http_error(404)
        <class 'NotFoundError'>
        >>> classify_http_error(429)
        <class 'RateLimitError'>
        >>> classify_http_error(503)
        <class 'ServiceUnavailableError'>
        >>> classify_http_error(500)
        <class 'PermanentError'>
    """
    return HTTP_ERROR_MAP.get(status_code, PermanentError)


def classify_network_error(error: Exception) -> Type[Exception]:
    """
    Classify network-level errors into appropriate exception types.
    
    This function examines network exceptions and maps them to either
    TimeoutException or NetworkError for proper retry handling.
    
    Args:
        error: The exception to classify
        
    Returns:
        Exception class (TimeoutException or NetworkError)
        
    Examples:
        >>> import socket
        >>> classify_network_error(socket.timeout())
        <class 'TimeoutException'>
        >>> classify_network_error(ConnectionError())
        <class 'NetworkError'>
    """
    error_name = type(error).__name__.lower()
    
    # Timeout-related errors
    if 'timeout' in error_name:
        return TimeoutException
    
    # Network connectivity errors
    if any(keyword in error_name for keyword in ['connection', 'network', 'dns', 'socket']):
        return NetworkError
    
    # Default to NetworkError for unknown network issues
    return NetworkError
