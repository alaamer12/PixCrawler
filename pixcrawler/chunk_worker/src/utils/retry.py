"""
Retry utility for the Chunk Worker.

This module provides Tenacity retry strategies for network operations,
Azure uploads, and other potentially transient failures.
"""

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log
import requests
from azure.core.exceptions import AzureError
from loguru import logger
import logging

def get_retry_strategy(max_attempts: int = 5):
    """
    Returns a Tenacity retry decorator configured for network and Azure errors.

    Retries on:
    - requests.exceptions.RequestException (Network issues)
    - ConnectionError
    - TimeoutError
    - AzureError (Azure Blob Storage issues)

    Strategy:
    - Exponential backoff: 2s, 4s, 8s... up to 10s
    - Max attempts: 5 (default)
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((
            requests.exceptions.RequestException,
            ConnectionError,
            TimeoutError,
            AzureError,
            IOError # For transient filesystem issues if any
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
