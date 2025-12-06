import typing
from starlette.concurrency import run_in_threadpool

async def run_sync(func: typing.Callable[..., typing.Any], *args: typing.Any, **kwargs: typing.Any) -> typing.Any:
    """Run a synchronous function in a thread pool."""
    return await run_in_threadpool(func, *args, **kwargs)

__all__ = ["run_sync", "run_in_threadpool"]
