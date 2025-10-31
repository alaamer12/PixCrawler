"""
Canvas workflow utilities for PixCrawler.

This module provides helper functions for creating complex task workflows
using Celery's Canvas primitives (group, chain, chord, map, starmap).

Functions:
    create_parallel_workflow: Execute tasks in parallel
    create_sequential_workflow: Execute tasks in sequence
    create_map_reduce_workflow: Map-reduce pattern for batch processing
    create_callback_workflow: Execute task with success/error callbacks

Canvas Primitives:
    - group: Execute tasks in parallel
    - chain: Execute tasks sequentially
    - chord: Execute tasks in parallel, then callback
    - map: Apply task to multiple arguments
    - starmap: Apply task to multiple argument tuples

Example:
    >>> from celery_core.workflows import create_parallel_workflow
    >>> workflow = create_parallel_workflow([
    ...     crawl_images.s('cats'),
    ...     crawl_images.s('dogs'),
    ...     crawl_images.s('birds')
    ... ])
    >>> result = workflow.apply_async()
"""

from typing import List, Any, Optional

from celery import group, chain, chord
from celery.canvas import Signature
from celery.result import AsyncResult, GroupResult

from utility.logging_config import get_logger

logger = get_logger(__name__)

__all__ = [
    'create_parallel_workflow',
    'create_sequential_workflow',
    'create_map_reduce_workflow',
    'create_callback_workflow',
    'create_crawl_and_validate_workflow'
]


def create_parallel_workflow(tasks: List[Signature]) -> group:
    """
    Create a workflow that executes tasks in parallel.

    Args:
        tasks: List of task signatures to execute in parallel

    Returns:
        group: Celery group that executes tasks in parallel

    Example:
        >>> tasks = [crawl_images.s('cats'), crawl_images.s('dogs')]
        >>> workflow = create_parallel_workflow(tasks)
        >>> result = workflow.apply_async()
    """
    if not tasks:
        raise ValueError("Tasks list cannot be empty")

    logger.info(f"Creating parallel workflow with {len(tasks)} tasks")
    return group(*tasks)


def create_sequential_workflow(tasks: List[Signature]) -> chain:
    """
    Create a workflow that executes tasks sequentially.

    Each task receives the result of the previous task as input.

    Args:
        tasks: List of task signatures to execute in sequence

    Returns:
        chain: Celery chain that executes tasks sequentially

    Example:
        >>> workflow = create_sequential_workflow([
        ...     crawl_images.s('cats'),
        ...     validate_images.s(),
        ...     store_results.s()
        ... ])
        >>> result = workflow.apply_async()
    """
    if not tasks:
        raise ValueError("Tasks list cannot be empty")

    logger.info(f"Creating sequential workflow with {len(tasks)} tasks")
    return chain(*tasks)


def create_map_reduce_workflow(
    map_task: Signature,
    items: List[Any],
    reduce_task: Optional[Signature] = None
) -> chord | Any:
    """
    Create a map-reduce workflow.

    Applies map_task to each item in parallel, then optionally
    applies reduce_task to aggregate results.

    Args:
        map_task: Task to apply to each item
        items: List of items to process
        reduce_task: Optional task to aggregate results

    Returns:
        chord or group: Workflow for map-reduce pattern

    Example:
        >>> workflow = create_map_reduce_workflow(
        ...     crawl_images.s(),
        ...     ['cats', 'dogs', 'birds'],
        ...     merge_results.s()
        ... )
        >>> result = workflow.apply_async()
    """
    if not items:
        raise ValueError("Items list cannot be empty")

    # Create parallel tasks for each item
    parallel_tasks = group(map_task.clone([item]) for item in items)

    if reduce_task:
        logger.info(f"Creating map-reduce workflow: {len(items)} items -> reduce")
        return chord(parallel_tasks)(reduce_task)
    else:
        logger.info(f"Creating map workflow: {len(items)} items")
        return parallel_tasks


def create_callback_workflow(
    task: Signature,
    success_callback: Optional[Signature] = None,
    error_callback: Optional[Signature] = None
) -> Signature:
    """
    Create a workflow with success and error callbacks.

    Args:
        task: Main task to execute
        success_callback: Task to execute on success
        error_callback: Task to execute on error

    Returns:
        Signature: Task with callbacks attached

    Example:
        >>> workflow = create_callback_workflow(
        ...     crawl_images.s('cats'),
        ...     success_callback=notify_user.s(),
        ...     error_callback=log_error.s()
        ... )
        >>> result = workflow.apply_async()
    """
    if success_callback:
        task.link(success_callback)
        logger.debug(f"Added success callback to task {task.task}")

    if error_callback:
        task.link_error(error_callback)
        logger.debug(f"Added error callback to task {task.task}")

    return task


def create_crawl_and_validate_workflow(
    keywords: List[str],
    crawl_task: Signature,
    validate_task: Signature,
    merge_task: Optional[Signature] = None
) -> chain:
    """
    Create a complete crawl-and-validate workflow for PixCrawler.

    This is a common pattern: crawl images for multiple keywords in parallel,
    then validate all results, optionally merge and store.

    Args:
        keywords: List of keywords to crawl
        crawl_task: Task signature for crawling (e.g., crawl_images.s())
        validate_task: Task signature for validation
        merge_task: Optional task to merge and store results

    Returns:
        chain: Complete workflow

    Example:
        >>> from builder.tasks import crawl_images
        >>> from validator.tasks import validate_batch
        >>> from backend.tasks import store_dataset
        >>>
        >>> workflow = create_crawl_and_validate_workflow(
        ...     keywords=['cats', 'dogs', 'birds'],
        ...     crawl_task=crawl_images.s(),
        ...     validate_task=validate_batch.s(),
        ...     merge_task=store_dataset.s()
        ... )
        >>> result = workflow.apply_async()
    """
    if not keywords:
        raise ValueError("Keywords list cannot be empty")

    # Step 1: Crawl images for all keywords in parallel
    crawl_group = group(crawl_task.clone([keyword]) for keyword in keywords)

    # Step 2: Validate all crawled images
    workflow_steps = [crawl_group, validate_task]

    # Step 3: Optionally merge and store
    if merge_task:
        workflow_steps.append(merge_task)

    logger.info(
        f"Creating crawl-and-validate workflow: "
        f"{len(keywords)} keywords -> validate"
        f"{' -> merge' if merge_task else ''}"
    )

    return chain(*workflow_steps)


def get_workflow_status(result: AsyncResult) -> dict:
    """
    Get the status of a workflow execution.

    Args:
        result: AsyncResult from workflow execution

    Returns:
        dict: Workflow status information

    Example:
        >>> result = workflow.apply_async()
        >>> status = get_workflow_status(result)
        >>> print(status['state'])
    """
    status = {
        'task_id': result.id,
        'state': result.state,
        'ready': result.ready(),
        'successful': result.successful() if result.ready() else None,
        'failed': result.failed() if result.ready() else None,
    }

    if result.ready():
        if result.successful():
            status['result'] = result.result
        elif result.failed():
            status['error'] = str(result.info)

    # Handle group results
    if isinstance(result, GroupResult):
        status['total_tasks'] = len(result.results)
        status['completed_tasks'] = sum(1 for r in result.results if r.ready())
        status['successful_tasks'] = sum(
            1 for r in result.results if r.ready() and r.successful()
        )
        status['failed_tasks'] = sum(
            1 for r in result.results if r.ready() and r.failed()
        )

    return status


def cancel_workflow(result: AsyncResult, terminate: bool = True) -> None:
    """
    Cancel a running workflow.

    Args:
        result: AsyncResult from workflow execution
        terminate: Whether to terminate running tasks

    Example:
        >>> result = workflow.apply_async()
        >>> cancel_workflow(result, terminate=True)
    """
    from celery_core.app import revoke_task

    if isinstance(result, GroupResult):
        # Cancel all tasks in the group
        for task_result in result.results:
            revoke_task(task_result.id, terminate=terminate)
        logger.info(f"Cancelled workflow group with {len(result.results)} tasks")
    else:
        # Cancel single task
        revoke_task(result.id, terminate=terminate)
        logger.info(f"Cancelled workflow task {result.id}")
