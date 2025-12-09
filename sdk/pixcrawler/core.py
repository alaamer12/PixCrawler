import os
import time
from pathlib import Path
from typing import Optional, Any, Dict, List

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# Module-Level State for Global Authentication
# ============================================================================

_global_auth_token: Optional[str] = None
_global_base_url: str = "https://api.pixcrawler.com/v1"


# ============================================================================
# Custom Exceptions
# ============================================================================

class PixCrawlerError(Exception):
    """Base exception for all PixCrawler SDK errors."""
    pass


class APIError(PixCrawlerError):
    """API returned an error response."""
    def __init__(self, status_code: int, message: str, details: Optional[Dict] = None):
        self.status_code = status_code
        self.message = message
        self.details = details or {}
        super().__init__(f"API Error {status_code}: {message}")


class AuthenticationError(PixCrawlerError):
    """Authentication failed or credentials missing."""
    pass


class ValidationError(PixCrawlerError):
    """Request validation failed."""
    pass


class NotFoundError(PixCrawlerError):
    """Resource not found."""
    pass


class RateLimitError(PixCrawlerError):
    """Rate limit exceeded."""
    pass


# ============================================================================
# Dataset Class
# ============================================================================

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


# ============================================================================
# Global Authentication Function
# ============================================================================

def auth(token: str, base_url: Optional[str] = None) -> None:
    """
    Set global authentication token for the session.
    
    This function sets the authentication token that will be used for all
    subsequent API calls. The token is stored in module-level state.
    
    Args:
        token: API token or JWT token from Supabase Auth
        base_url: Optional base URL override (default: https://api.pixcrawler.com/v1)
    
    Example:
        >>> import pixcrawler as pix
        >>> pix.auth(token="your_api_key")
        >>> datasets = pix.list_datasets()
    
    Note:
        - Token is stored in memory for the current Python session
        - Use environment variables (SERVICE_API_KEY) for production
        - This function is optional if using environment variables
    """
    global _global_auth_token, _global_base_url
    _global_auth_token = token
    if base_url:
        _global_base_url = base_url


def _get_auth_token(config: Optional[Dict[str, Any]] = None) -> str:
    """
    Get authentication token from config, global state, or environment.
    
    Priority:
        1. config["api_key"]
        2. Global auth token (set via auth())
        3. SERVICE_API_KEY environment variable
        4. SERVICE_API_TOKEN environment variable
    
    Args:
        config: Optional configuration dictionary
    
    Returns:
        Authentication token
    
    Raises:
        AuthenticationError: If no token is found
    """
    config = config or {}
    
    # Priority 1: config parameter
    token = config.get("api_key")
    if token:
        return token
    
    # Priority 2: global auth token
    if _global_auth_token:
        return _global_auth_token
    
    # Priority 3 & 4: environment variables
    token = os.getenv("SERVICE_API_KEY") or os.getenv("SERVICE_API_TOKEN")
    if token:
        return token
    
    raise AuthenticationError(
        "Authentication failed: No API key found. "
        "Use pix.auth(token='...') or set SERVICE_API_KEY environment variable."
    )


def _get_base_url(config: Optional[Dict[str, Any]] = None) -> str:
    """
    Get base URL from config, global state, or environment.
    
    Args:
        config: Optional configuration dictionary
    
    Returns:
        Base URL for API requests
    """
    config = config or {}
    
    # Priority 1: config parameter
    if "base_url" in config:
        return config["base_url"]
    
    # Priority 2: global base URL
    if _global_base_url != "https://api.pixcrawler.com/v1":
        return _global_base_url
    
    # Priority 3: environment variable
    return os.getenv("PIXCRAWLER_API_URL", _global_base_url)


def _make_request(
    method: str,
    endpoint: str,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> requests.Response:
    """
    Make authenticated API request with error handling.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path (e.g., "/datasets")
        config: Optional configuration dictionary
        **kwargs: Additional arguments for requests
    
    Returns:
        Response object
    
    Raises:
        AuthenticationError: If authentication fails
        APIError: If API returns an error
        RateLimitError: If rate limit is exceeded
        NotFoundError: If resource is not found
    """
    token = _get_auth_token(config)
    base_url = _get_base_url(config)
    url = f"{base_url}{endpoint}"
    
    headers = kwargs.pop("headers", {})
    headers.update({
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    })
    
    try:
        response = requests.request(method, url, headers=headers, **kwargs)
        
        # Handle specific status codes
        if response.status_code == 401:
            raise AuthenticationError("Authentication failed: Invalid or expired token")
        elif response.status_code == 404:
            raise NotFoundError(f"Resource not found: {endpoint}")
        elif response.status_code == 429:
            raise RateLimitError("Rate limit exceeded. Please try again later.")
        elif response.status_code == 422:
            try:
                error_data = response.json()
                raise ValidationError(f"Validation failed: {error_data.get('detail', response.text)}")
            except ValueError:
                raise ValidationError(f"Validation failed: {response.text}")
        elif response.status_code >= 400:
            try:
                error_data = response.json()
                raise APIError(
                    status_code=response.status_code,
                    message=error_data.get("message", response.text),
                    details=error_data.get("details", {})
                )
            except ValueError:
                raise APIError(
                    status_code=response.status_code,
                    message=response.text,
                    details={}
                )
        
        return response
        
    except requests.exceptions.Timeout:
        raise PixCrawlerError("Request timeout: Connection took too long")
    except requests.exceptions.ConnectionError:
        raise PixCrawlerError("Connection error: Could not connect to API")
    except (AuthenticationError, APIError, RateLimitError, NotFoundError, ValidationError):
        raise
    except Exception as e:
        raise PixCrawlerError(f"Unexpected error: {str(e)}")


# ============================================================================
# Dataset Operations
# ============================================================================

def list_datasets(page: int = 1, size: int = 20, config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    List user's datasets with pagination.
    
    Retrieves a paginated list of datasets owned by the authenticated user.
    
    Args:
        page: Page number (default: 1)
        size: Items per page (default: 20, max: 100)
        config: Optional configuration with 'api_key' and 'base_url'
    
    Returns:
        List of dataset metadata dictionaries
    
    Raises:
        AuthenticationError: If authentication fails
        APIError: If API request fails
    
    Example:
        >>> import pixcrawler as pix
        >>> pix.auth(token="your_api_key")
        >>> datasets = pix.list_datasets(page=1, size=10)
        >>> for dataset in datasets:
        ...     print(f"{dataset['id']}: {dataset['name']}")
    """
    response = _make_request(
        "GET",
        "/datasets",
        config=config,
        params={"page": page, "size": size},
        timeout=30
    )
    
    data = response.json()
    
    # Handle fastapi-pagination format
    if isinstance(data, dict) and "items" in data:
        return data["items"]
    elif isinstance(data, list):
        return data
    else:
        return [data]


def get_dataset_info(dataset_id: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get dataset metadata without downloading.
    
    Retrieves metadata about a dataset including image count, size,
    labels, and other information without downloading the actual data.
    
    Args:
        dataset_id: UUID or ID of the dataset
        config: Optional configuration with 'api_key' and 'base_url'
    
    Returns:
        Dictionary with dataset metadata
    
    Raises:
        AuthenticationError: If authentication fails
        NotFoundError: If dataset not found
        APIError: If API request fails
    
    Example:
        >>> import pixcrawler as pix
        >>> info = pix.get_dataset_info("dataset-id-123")
        >>> print(f"Images: {info['image_count']}, Size: {info['size_mb']}MB")
    """
    response = _make_request(
        "GET",
        f"/datasets/{dataset_id}",
        config=config,
        timeout=30
    )
    
    return response.json()


def download_dataset(
    dataset_id: str,
    output_path: str,
    config: Optional[Dict[str, Any]] = None
) -> str:
    """
    Download dataset archive to local file.
    
    Downloads the dataset as a ZIP archive to the specified path.
    Does NOT load the dataset into memory, making it suitable for large datasets.
    
    Args:
        dataset_id: UUID or ID of the dataset
        output_path: Local file path to save the dataset (e.g., "./wildlife.zip")
        config: Optional configuration with 'api_key' and 'base_url'
    
    Returns:
        Path to the downloaded file
    
    Raises:
        AuthenticationError: If authentication fails
        NotFoundError: If dataset not found
        APIError: If API request fails
        PixCrawlerError: If download or file write fails
    
    Example:
        >>> import pixcrawler as pix
        >>> pix.auth(token="your_api_key")
        >>> path = pix.download_dataset("dataset-id-123", "./my_dataset.zip")
        >>> print(f"Downloaded to: {path}")
    """
    response = _make_request(
        "GET",
        f"/datasets/{dataset_id}/export/zip",
        config=config,
        timeout=300,  # 5 minutes for large downloads
        stream=True
    )
    
    # Create output directory if it doesn't exist
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Download with progress
    try:
        with open(output_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return str(output_file.absolute())
        
    except Exception as e:
        # Clean up partial download
        if output_file.exists():
            output_file.unlink()
        raise PixCrawlerError(f"Download failed: {str(e)}")
