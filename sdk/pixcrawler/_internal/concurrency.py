"""
Internal concurrency helpers for the SDK.
"""
import asyncio
from typing import TypeVar, Callable, Any
from functools import partial

T = TypeVar("T")

async def run_in_thread(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """
    Run a blocking function in a separate thread.
    Useful for wrapping legacy synchronous code (like icrawler).
    """
    loop = asyncio.get_running_loop()
    pfunc = partial(func, *args, **kwargs)
    return await loop.run_in_executor(None, pfunc)
