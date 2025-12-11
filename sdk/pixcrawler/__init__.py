from .core import (
    # Core classes
    Dataset,
    Project,
    # Functions
    auth,
    dataset,
    datasets,
    project,
    get_dataset_info,
    download_dataset,
    # Legacy functions (for backward compatibility)
    load_dataset,
    list_datasets,
    # Exceptions
    PixCrawlerError,
    APIError,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    RateLimitError,
)

__all__ = [
    # Core classes
    "Dataset",
    "Project",
    # Functions
    "auth",
    "dataset",
    "datasets", 
    "project",
    "get_dataset_info",
    "download_dataset",
    # Legacy functions (for backward compatibility)
    "load_dataset",
    "list_datasets",
    # Exceptions
    "PixCrawlerError",
    "APIError",
    "AuthenticationError",
    "ValidationError",
    "NotFoundError",
    "RateLimitError",
]
