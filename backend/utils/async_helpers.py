"""
Async/sync interoperability utilities.

This module provides utilities for running synchronous code in async contexts
using Starlette's run_in_threadpool, which is essential for integrating
sync libraries (like validator, builder) with FastAPI's async endpoints.
"""

from typing import TypeVar, Callable, Any
from starlette.concurrency import run_in_threadpool, iterate_in_threadpool

__all__ = [
    'run_sync_in_thread',
    'iterate_sync_in_thread'
]

T = TypeVar('T')


async def run_sync_in_thread(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """
    Run a synchronous function in a thread pool.
    
    This is useful for running CPU-bound or blocking I/O operations
    without blocking the async event loop.
    
    Args:
        func: Synchronous function to run
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        Function result
        
    Example:
        >>> from validator.validation import CheckManager
        >>> 
        >>> async def validate_images(image_paths: list[str]):
        ...     manager = CheckManager()
        ...     # Run sync validation in thread pool
        ...     result = await run_sync_in_thread(
        ...         manager.check_integrity,
        ...         directory="/path/to/images",
        ...         category="validation"
        ...     )
        ...     return result
    """
    if kwargs:
        # Create a partial function if kwargs are provided
        from functools import partial
        func_with_kwargs = partial(func, **kwargs)
        return await run_in_threadpool(func_with_kwargs, *args)
    else:
        return await run_in_threadpool(func, *args)


async def iterate_sync_in_thread(iterable):
    """
    Iterate over a synchronous iterator in a thread pool.
    
    This is useful for iterating over sync generators or iterators
    without blocking the async event loop.
    
    Args:
        iterable: Synchronous iterable
        
    Yields:
        Items from the iterable
        
    Example:
        >>> async def process_large_file(file_path: str):
        ...     def read_lines():
        ...         with open(file_path) as f:
        ...             for line in f:
        ...                 yield line
        ...     
        ...     async for line in iterate_sync_in_thread(read_lines()):
        ...         process(line)
    """
    async for item in iterate_in_threadpool(iterable):
        yield item
