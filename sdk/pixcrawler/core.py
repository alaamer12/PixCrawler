import os
import time
from pathlib import Path
from typing import Optional, Any, Dict, List, Union

import requests

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
# Core Classes
# ============================================================================

class Dataset:
    """
    A class representing a dataset that can be loaded into memory or downloaded.
    """
    def __init__(self, dataset_id: Union[str, int], config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Dataset with ID and configuration.

        Args:
            dataset_id: The ID of the dataset
            config: Optional configuration dictionary
        """
        self.dataset_id = str(dataset_id)
        self.config = config or {}
        self._data: Optional[List[Any]] = None
        self._info: Optional[Dict[str, Any]] = None

    def load(self) -> "Dataset":
        """
        Load dataset into memory for iteration.
        
        Returns:
            Self for method chaining
            
        Raises:
            AuthenticationError: If authentication fails
            NotFoundError: If dataset not found
            RuntimeError: If dataset exceeds memory limit (300MB)
        """
        if self._data is None:
            # Use the export JSON endpoint to get dataset data
            response = _make_request(
                "GET",
                f"/datasets/{self.dataset_id}/export/json",
                config=self.config,
                timeout=300  # 5 minutes for large datasets
            )
            
            # Check memory guardrail before loading
            content_length = response.headers.get('Content-Length')
            max_memory_bytes = 300 * 1024 * 1024  # 300MB limit
            
            if content_length and int(content_length) > max_memory_bytes:
                raise RuntimeError(
                    f"Dataset size ({int(content_length) / (1024*1024):.2f}MB) exceeds "
                    f"memory limit ({max_memory_bytes / (1024*1024):.0f}MB)"
                )
            
            # Parse JSON response
            try:
                data = response.json()
                if isinstance(data, list):
                    self._data = data
                elif isinstance(data, dict) and "items" in data:
                    self._data = data["items"]
                else:
                    self._data = [data] if data else []
            except ValueError:
                raise PixCrawlerError("Failed to parse dataset response as JSON")
        
        return self

    def download(self, output_path: str) -> str:
        """
        Download dataset archive to local file.
        
        Args:
            output_path: Local file path to save the dataset
            
        Returns:
            Absolute path to downloaded file
            
        Raises:
            AuthenticationError: If authentication fails
            NotFoundError: If dataset not found
            PixCrawlerError: If download fails
        """
        response = _make_request(
            "GET",
            f"/datasets/{self.dataset_id}/export/zip",
            config=self.config,
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

    def info(self) -> Dict[str, Any]:
        """
        Get dataset metadata without downloading.
        
        Returns:
            Dictionary with dataset metadata
            
        Raises:
            AuthenticationError: If authentication fails
            NotFoundError: If dataset not found
        """
        if self._info is None:
            response = _make_request(
                "GET",
                f"/datasets/{self.dataset_id}",
                config=self.config,
                timeout=30
            )
            self._info = response.json()
        
        return self._info

    @property
    def name(self) -> str:
        """Get dataset name."""
        return self.info().get("name", "")

    @property
    def image_count(self) -> int:
        """Get total image count."""
        return self.info().get("total_images", 0)

    @property
    def size_mb(self) -> float:
        """Get dataset size in MB."""
        return self.info().get("size_mb", 0.0)

    def __iter__(self):
        """
        Iterate over the dataset items.
        
        Note: This requires the dataset to be loaded first.
        """
        if self._data is None:
            self.load()
        
        for item in self._data:
            yield item

    def __len__(self) -> int:
        """Get number of items in loaded dataset."""
        if self._data is None:
            return self.image_count
        return len(self._data)


class Project:
    """
    A class representing a project that contains datasets.
    """
    def __init__(self, project_id: Union[str, int], config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Project with ID and configuration.

        Args:
            project_id: The ID of the project
            config: Optional configuration dictionary
        """
        self.project_id = str(project_id)
        self.config = config or {}
        self._info: Optional[Dict[str, Any]] = None

    def datasets(self, page: int = 1, size: int = 50) -> List[Dict[str, Any]]:
        """
        List datasets in this project.
        
        Args:
            page: Page number (default: 1)
            size: Items per page (default: 50, max: 100)
            
        Returns:
            List of dataset metadata dictionaries
            
        Raises:
            AuthenticationError: If authentication fails
            APIError: If API request fails
        """
        response = _make_request(
            "GET",
            "/datasets",
            config=self.config,
            params={"project_id": self.project_id, "page": page, "size": size},
            timeout=30
        )
        
        data = response.json()
        
        # Handle fastapi-pagination format
        if isinstance(data, dict) and "items" in data:
            return data["items"]
        elif isinstance(data, list):
            return data
        else:
            return [data] if data else []

    def dataset(self, dataset_id: Union[str, int]) -> Dataset:
        """
        Get a dataset from this project.
        
        Args:
            dataset_id: Dataset ID
            
        Returns:
            Dataset instance
        """
        return Dataset(dataset_id, self.config)

    def info(self) -> Dict[str, Any]:
        """
        Get project metadata.
        
        Returns:
            Dictionary with project metadata
            
        Raises:
            AuthenticationError: If authentication fails
            NotFoundError: If project not found
        """
        if self._info is None:
            response = _make_request(
                "GET",
                f"/projects/{self.project_id}",
                config=self.config,
                timeout=30
            )
            self._info = response.json()
        
        return self._info

    @property
    def name(self) -> str:
        """Get project name."""
        return self.info().get("name", "")

    @property
    def description(self) -> str:
        """Get project description."""
        return self.info().get("description", "")

# ============================================================================
# Main API Functions
# ============================================================================

def dataset(dataset_id: Union[str, int], config: Optional[Dict[str, Any]] = None) -> Dataset:
    """
    Create a Dataset instance for loading or downloading.

    Args:
        dataset_id: UUID or ID of the dataset
        config: Optional configuration with 'api_key' and 'base_url'

    Returns:
        Dataset instance

    Example:
        >>> import pixcrawler as pix
        >>> dataset = pix.dataset("dataset-id-123")
        >>> data = dataset.load()  # Load into memory
        >>> # or
        >>> path = dataset.download("./my_dataset.zip")  # Download to file
    """
    return Dataset(dataset_id, config)


def project(project_id: Union[str, int], config: Optional[Dict[str, Any]] = None) -> Project:
    """
    Create a Project instance for accessing datasets.

    Args:
        project_id: UUID or ID of the project
        config: Optional configuration with 'api_key' and 'base_url'

    Returns:
        Project instance

    Example:
        >>> import pixcrawler as pix
        >>> proj = pix.project("project-id-123")
        >>> datasets = proj.datasets()  # List datasets in project
        >>> dataset = proj.dataset("dataset-id-456")  # Get specific dataset
    """
    return Project(project_id, config)


def datasets(page: int = 1, size: int = 50, config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    List user's datasets with pagination.
    
    Retrieves a paginated list of datasets owned by the authenticated user.
    
    Args:
        page: Page number (default: 1)
        size: Items per page (default: 50, max: 100)
        config: Optional configuration with 'api_key' and 'base_url'
    
    Returns:
        List of dataset metadata dictionaries
    
    Raises:
        AuthenticationError: If authentication fails
        APIError: If API request fails
    
    Example:
        >>> import pixcrawler as pix
        >>> pix.auth(token="your_api_key")
        >>> datasets = pix.datasets(page=1, size=10)
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
        return [data] if data else []


# ============================================================================
# Legacy Functions (for backward compatibility)
# ============================================================================

def load_dataset(dataset_id: str, config: Optional[Dict[str, Any]] = None) -> Dataset:
    """
    Load a dataset from the PixCrawler service (legacy function).

    Args:
        dataset_id: The ID of the dataset to load.
        config: Optional configuration dictionary. Can contain 'api_key' and 'base_url'.

    Returns:
        A Dataset object containing the loaded data.

    Raises:
        AuthenticationError: If authentication credentials are missing.
        NotFoundError: If dataset not found.
        RuntimeError: If dataset exceeds memory limit (300MB).
        
    Note:
        This is a legacy function. Use pix.dataset(id).load() instead.
    """
    return dataset(dataset_id, config).load()


def list_datasets(page: int = 1, size: int = 20, config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    List user's datasets with pagination (legacy function).
    
    Args:
        page: Page number (default: 1)
        size: Items per page (default: 20, max: 100)
        config: Optional configuration with 'api_key' and 'base_url'
    
    Returns:
        List of dataset metadata dictionaries
    
    Note:
        This is a legacy function. Use pix.datasets() instead.
    """
    return datasets(page, size, config)


def get_dataset_info(dataset_id: Union[str, int], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
    return dataset(dataset_id, config).info()


def download_dataset(
    dataset_id: Union[str, int],
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
    return dataset(dataset_id, config).download(output_path)


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
        >>> datasets = pix.datasets()
    
    Note:
        - Token is stored in memory for the current Python session
        - Use environment variables (PIXCRAWLER_SERVICE_KEY) for production
        - This function is optional if using environment variables
    """
    global _global_auth_token, _global_base_url
    _global_auth_token = token
    if base_url:
        _global_base_url = base_url


# ============================================================================
# Helper Functions
# ============================================================================

def _get_auth_token(config: Optional[Dict[str, Any]] = None) -> str:
    """
    Get authentication token from config, global state, or environment.
    
    Priority:
        1. config["api_key"]
        2. Global auth token (set via auth())
        3. PIXCRAWLER_SERVICE_KEY environment variable
        4. SERVICE_API_KEY environment variable (legacy)
        5. SERVICE_API_TOKEN environment variable (legacy)
    
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
    
    # Priority 3-5: environment variables
    token = (
        os.getenv("PIXCRAWLER_SERVICE_KEY") or 
        os.getenv("SERVICE_API_KEY") or 
        os.getenv("SERVICE_API_TOKEN")
    )
    if token:
        return token
    
    raise AuthenticationError(
        "Authentication failed: No API key found. "
        "Use pix.auth(token='...') or set PIXCRAWLER_SERVICE_KEY environment variable."
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
                    message=error_data.get("message", error_data.get("detail", response.text)),
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
