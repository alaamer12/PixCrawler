# PixCrawler Python SDK

A simple, lightweight Python SDK for accessing PixCrawler datasets. Designed for ML workflows with minimal API surface and maximum ease of use.

## Installation

```bash
pip install pixcrawler
```

Or install from source:

```bash
cd sdk
pip install -e .
```

## Quick Start

```python
import pixcrawler as pix

# Set authentication (optional if using environment variables)
pix.auth(token="your_api_key")

# Load dataset into memory
dataset = pix.load_dataset("dataset-id-123")

# Iterate over items
for item in dataset:
    print(item)
```

## Authentication

The SDK supports three authentication methods (in priority order):

### 1. Programmatic Authentication (Recommended for Scripts)

```python
import pixcrawler as pix

pix.auth(token="your_api_key")
```

### 2. Environment Variables (Recommended for Production)

```bash
export PIXCRAWLER_SERVICE_KEY="your_api_key"
```

### 3. Per-Request Configuration

```python
from pixcrawler import load_dataset

dataset = load_dataset(
    "dataset-id-123",
    config={"api_key": "your_api_key"}
)
```

## API Reference

### `auth(token, base_url=None)`

Set global authentication token for the session.

**Parameters:**
- `token` (str): API token or JWT token from Supabase Auth
- `base_url` (str, optional): Override API base URL (default: https://api.pixcrawler.com/v1)

**Example:**
```python
import pixcrawler as pix

pix.auth(token="your_api_key")
# All subsequent calls will use this token
```

---

### `load_dataset(dataset_id, config=None)`

Load dataset into memory for iteration.

**Parameters:**
- `dataset_id` (str): UUID of the dataset
- `config` (dict, optional): Configuration with 'api_key' and 'base_url'

**Returns:**
- `Dataset`: In-memory dataset object

**Raises:**
- `AuthenticationError`: If authentication fails
- `NotFoundError`: If dataset not found
- `RuntimeError`: If dataset exceeds memory limit (300MB)

**Example:**
```python
import pixcrawler as pix

# Load dataset
dataset = pix.load_dataset("dataset-id-123")

# Iterate over items
for item in dataset:
    image_url = item['url']
    label = item['label']
    print(f"{label}: {image_url}")
```

---

### `list_datasets(page=1, size=20, config=None)`

List user's datasets with pagination.

**Parameters:**
- `page` (int): Page number (default: 1)
- `size` (int): Items per page (default: 20, max: 100)
- `config` (dict, optional): Configuration with 'api_key' and 'base_url'

**Returns:**
- `List[dict]`: List of dataset metadata dictionaries

**Raises:**
- `AuthenticationError`: If authentication fails
- `APIError`: If API request fails

**Example:**
```python
import pixcrawler as pix

pix.auth(token="your_api_key")

# List all datasets
datasets = pix.list_datasets(page=1, size=50)

for dataset in datasets:
    print(f"{dataset['id']}: {dataset['name']} ({dataset['image_count']} images)")
```

---

### `get_dataset_info(dataset_id, config=None)`

Get dataset metadata without downloading.

**Parameters:**
- `dataset_id` (str): UUID of the dataset
- `config` (dict, optional): Configuration with 'api_key' and 'base_url'

**Returns:**
- `dict`: Dataset metadata (image_count, size_mb, labels, etc.)

**Raises:**
- `AuthenticationError`: If authentication fails
- `NotFoundError`: If dataset not found

**Example:**
```python
import pixcrawler as pix

# Get metadata
dataset = pix.dataset("dataset-id-123")

print(f"Name: {dataset.name]}")
print(f"Images: {dataset.image_count]}")
print(f"Size: {dataset.size_mb}MB")
```

---

### `download_dataset(dataset_id, output_path, config=None)`

Download dataset archive to local file.

**Parameters:**
- `dataset_id` (str): UUID of the dataset
- `output_path` (str): Local file path (e.g., "./wildlife.zip")
- `config` (dict, optional): Configuration with 'api_key' and 'base_url'

**Returns:**
- `str`: Absolute path to downloaded file

**Raises:**
- `AuthenticationError`: If authentication fails
- `NotFoundError`: If dataset not found
- `PixCrawlerError`: If download fails

**Example:**
```python
import pixcrawler as pix

pix.auth(token="your_api_key")

# Download to file (doesn't load into memory)
path = pix.download_dataset("dataset-id-123", "./my_dataset.zip")
print(f"Downloaded to: {path}")
```

---

## Exception Handling

The SDK provides custom exceptions for different error scenarios:

```python
import pixcrawler as pix
from pixcrawler import (
    PixCrawlerError,      # Base exception
    APIError,             # API returned error
    AuthenticationError,  # Auth failed
    ValidationError,      # Validation failed
    NotFoundError,        # Resource not found
    RateLimitError,       # Rate limit exceeded
)

try:
    dataset = pix.load_dataset("dataset-id-123")
except AuthenticationError:
    print("Authentication failed. Check your API key.")
except NotFoundError:
    print("Dataset not found.")
except RateLimitError:
    print("Rate limit exceeded. Please try again later.")
except APIError as e:
    print(f"API error {e.status_code}: {e.message}")
except PixCrawlerError as e:
    print(f"SDK error: {e}")
```

## Complete Examples

### Example 1: Load and Process Dataset

```python
import pixcrawler as pix

# Authenticate
pix.auth(token="your_api_key")

# Load dataset
dataset = pix.load_dataset("dataset-id-123")

# Process items
for item in dataset:
    # Your ML preprocessing here
    image_url = item['url']
    label = item['label']
    # Download image, apply transforms, etc.
```

### Example 2: List and Download Datasets

```python
import pixcrawler as pix

pix.auth(token="your_api_key")

# List all datasets
datasets = pix.list_datasets()

# Find specific dataset
target_dataset = next(
    (d for d in datasets if d['name'] == 'Wildlife Images'),
    None
)

if target_dataset:
    # Get detailed info
    info = pix.get_dataset_info(target_dataset['id'])
    print(f"Found dataset: {info['name']} ({info['image_count']} images)")
    
    # Download to file
    path = pix.download_dataset(target_dataset['id'], "./wildlife.zip")
    print(f"Downloaded to: {path}")
```

### Example 3: Environment-Based Authentication

```python
# Set environment variable first:
# export SERVICE_API_KEY="your_api_key"

import pixcrawler as pix

# No need to call auth() - uses environment variable
dataset = pix.load_dataset("dataset-id-123")

for item in dataset:
    print(item)
```

### Example 4: Custom Base URL (Testing)

```python
import pixcrawler as pix

# Use custom API URL (e.g., for testing)
pix.auth(
    token="your_api_key",
    base_url="http://localhost:8000/api/v1"
)

datasets = pix.list_datasets()
```

## Memory Considerations

The `load_dataset()` function loads data into memory and has a **300MB limit** to prevent memory issues. For larger datasets:

1. Use `download_dataset()` to save to disk
2. Process the downloaded file in chunks
3. Or use the API directly for streaming

```python
import pixcrawler as pix

# For large datasets, download to file instead
path = pix.download_dataset("large-dataset-id", "./large_dataset.zip")

# Then process the ZIP file in chunks
import zipfile
with zipfile.ZipFile(path, 'r') as zf:
    # Process files one at a time
    for filename in zf.namelist():
        with zf.open(filename) as f:
            # Process file
            pass
```

## Requirements

- Python 3.8+
- requests
- python-dotenv

## License

MIT License

## Support

- Documentation: https://docs.pixcrawler.com
- Issues: https://github.com/pixcrawler/pixcrawler/issues
- Email: support@pixcrawler.com
