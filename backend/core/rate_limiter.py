"""Conditional rate limiter dependency.

Provides a rate limiter that only applies when rate limiting is enabled in settings.
When disabled, it acts as a no-op dependency.
"""

from typing import Optional
from fastapi import Request
from fastapi_limiter.depends import RateLimiter as FastAPIRateLimiter

from backend.core.config import get_settings

__all__ = ["RateLimiter", "get_rate_limiter"]


class ConditionalRateLimiter:
    """
    Conditional rate limiter that only applies when enabled in settings.
    
    When rate limiting is disabled, this acts as a no-op dependency.
    When enabled, it delegates to FastAPI-Limiter's RateLimiter.
    """
    
    def __init__(self, times: int = 1, seconds: int = 60):
        """
        Initialize conditional rate limiter.
        
        Args:
            times: Number of allowed requests
            seconds: Time window in seconds
        """
        self.times = times
        self.seconds = seconds
        self._limiter: Optional[FastAPIRateLimiter] = None
    
    async def __call__(self, request: Request) -> None:
        """
        Apply rate limiting if enabled.
        
        Args:
            request: FastAPI request object
        """
        settings = get_settings()
        
        # If rate limiting is disabled, do nothing
        if not settings.rate_limit.enabled:
            return
        
        # If rate limiting is enabled, use FastAPI-Limiter
        if self._limiter is None:
            self._limiter = FastAPIRateLimiter(times=self.times, seconds=self.seconds)
        
        await self._limiter(request)


# Alias for backward compatibility
RateLimiter = ConditionalRateLimiter


def get_rate_limiter(times: int = 1, seconds: int = 60) -> ConditionalRateLimiter:
    """
    Get a conditional rate limiter instance.
    
    Args:
        times: Number of allowed requests
        seconds: Time window in seconds
        
    Returns:
        ConditionalRateLimiter instance
        
    Example:
        ```python
        @router.post("/endpoint", dependencies=[Depends(get_rate_limiter(times=10, seconds=60))])
        async def endpoint():
            ...
        ```
    """
    return ConditionalRateLimiter(times=times, seconds=seconds)
