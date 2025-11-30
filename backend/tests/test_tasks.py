import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.tasks import execute_crawl_job

@pytest.mark.asyncio
async def test_execute_crawl_job_task():
    """Test the execute_crawl_job Celery task."""
    job_id = 123
    user_id = "user-123"
    tier = "pro"

    with patch("backend.tasks.execute_crawl_job_service", new_callable=AsyncMock) as mock_service:
        # Mock request context
        mock_request = MagicMock()
        mock_request.id = "test-task-id"
        mock_request.retries = 0

        # Push mock request to stack
        execute_crawl_job.request_stack.push(mock_request)
        
        try:
            # Mock asyncio.run to just await the coroutine directly
            # This is needed because we are already in an async test loop
            with patch("asyncio.run", side_effect=lambda coro: coro):
                # Call the task function directly
                # The task is synchronous (wrapped by BaseTask), so we don't await it
                execute_crawl_job(job_id, user_id, tier)

            # Verify service was called with correct arguments
            mock_service.assert_called_once_with(
                job_id=job_id,
                user_id=user_id,
                tier=tier
            )
        finally:
            execute_crawl_job.request_stack.pop()
