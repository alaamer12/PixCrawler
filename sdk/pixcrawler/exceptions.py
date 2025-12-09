"""
PixCrawler SDK Exceptions

This module defines the exception hierarchy for the PixCrawler SDK.
"""

class PixCrawlerError(Exception):
    """Base exception for all PixCrawler SDK errors."""
    pass

class ConfigurationError(PixCrawlerError):
    """Raised when there is a configuration issue."""
    pass

class APIError(PixCrawlerError):
    """Base exception for API-related errors."""
    def __init__(self, message: str, status_code: int = None, response_body: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body

class AuthenticationError(APIError):
    """Raised when API authentication fails."""
    pass

class NotFoundError(APIError):
    """Raised when a resource is not found."""
    pass

class RateLimitError(APIError):
    """Raised when API rate limit is exceeded."""
    pass

class ValidationError(PixCrawlerError):
    """Raised when data validation fails."""
    pass

class CrawlerError(PixCrawlerError):
    """Base exception for crawler/builder errors."""
    pass

class EngineError(CrawlerError):
    """Raised when a specific crawler engine fails."""
    pass
