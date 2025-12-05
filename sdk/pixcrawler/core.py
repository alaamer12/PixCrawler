import os
import time
from typing import Optional, Any, Dict, List

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Dataset:
    """
    A class representing a dataset loaded in memory.
    """
    def __init__(self, data: List[Any]):
        """
        Initialize the Dataset with raw in-memory data.

        Args:
            data: The list of data items.
        """
        self.data = data

    def __iter__(self):
        """
        Iterate over the data items.
        """
        for item in self.data:
            yield item

def load_dataset(dataset_id: str, config: Optional[Dict[str, Any]] = None) -> Dataset:
    """
    Load a dataset from the PixCrawler service.

    Args:
        dataset_id: The ID of the dataset to load.
        config: Optional configuration dictionary. Can contain 'api_key' and 'base_url'.

    Returns:
        A Dataset object containing the loaded data.

    Raises:
        ValueError: If authentication credentials are missing.
        ConnectionError: If the download fails after retries.
        TimeoutError: If the request times out.
        RuntimeError: For other API errors.
    """
    config = config or {}

    # 1. Authentication
    api_key = config.get("api_key") or os.getenv("SERVICE_API_KEY") or os.getenv("SERVICE_API_TOKEN")
    if not api_key:
        raise ValueError("Authentication failed: SERVICE_API_KEY or token missing or invalid")

    base_url = config.get("base_url") or os.getenv("PIXCRAWLER_API_URL", "https://api.pixcrawler.com/v1")
    url = f"{base_url}/datasets/{dataset_id}/download"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }

    # 2. Download with Retries
    max_retries = 3
    timeout = 60  # seconds
    max_memory_bytes = 300 * 1024 * 1024  # 300MB limit

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)

            if response.status_code == 200:
                # Check memory guardrail before loading
                content_length = response.headers.get('Content-Length')
                if content_length and int(content_length) > max_memory_bytes:
                    raise RuntimeError(
                        f"Dataset size ({int(content_length) / (1024*1024):.2f}MB) exceeds "
                        f"memory limit ({max_memory_bytes / (1024*1024):.0f}MB)"
                    )

                # Also check actual content size
                content_size = len(response.content)
                if content_size > max_memory_bytes:
                    raise RuntimeError(
                        f"Dataset size ({content_size / (1024*1024):.2f}MB) exceeds "
                        f"memory limit ({max_memory_bytes / (1024*1024):.0f}MB)"
                    )

                # Success - parse JSON
                try:
                    data = response.json()
                    # Basic validation that we got a list
                    if isinstance(data, dict) and "items" in data:
                        items = data["items"]
                    elif isinstance(data, list):
                        items = data
                    else:
                        # Fallback: wrap in list if it's a single object or unknown structure
                        items = [data]

                    return Dataset(items)
                except ValueError:
                    raise RuntimeError("Failed to parse dataset response as JSON")

            elif 500 <= response.status_code < 600:
                # Server error, retry
                if attempt == max_retries:
                    raise ConnectionError(f"Dataset download failed after {max_retries} retry attempts (Status {response.status_code})")
                time.sleep(1 * attempt) # Simple backoff
                continue

            else:
                # Client error (4xx), fail fast
                raise RuntimeError(f"API request failed with status {response.status_code}: {response.text}")

        except requests.exceptions.Timeout:
            if attempt == max_retries:
                raise TimeoutError(f"Connection timeout: request exceeded {timeout} seconds")
            time.sleep(1 * attempt)
            continue

        except requests.exceptions.ConnectionError:
            if attempt == max_retries:
                raise ConnectionError(f"Dataset download failed after {max_retries} retry attempts")
            time.sleep(1 * attempt)
            continue
        except Exception as e:
             # Re-raise specific exceptions we just raised
            if isinstance(e, (ValueError, RuntimeError, ConnectionError, TimeoutError)):
                raise e
            # Catch-all for unexpected errors
            raise RuntimeError(f"An unexpected error occurred: {str(e)}")

    # Should be unreachable due to raises above, but for safety:
    raise ConnectionError(f"Dataset download failed after {max_retries} retry attempts")
