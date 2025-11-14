# Azure: Data Lake Storage Blob Provider (Part 2)

Essential blob operations (upload, download, list, delete) using Azure Blob Storage SDK.
Works with ADLS Gen2 via the Blob endpoint.

## Features
- Upload from bytes, file-like, or file path
- Download to bytes or file
- List blobs with optional prefix
- Delete blobs
- Container auto-create if missing

## Requirements
- Python 3.10+
- Azure account and storage container permissions

Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration
Copy `.env.example` to `.env` and set credentials:
```ini
AZURE_STORAGE_CONNECTION_STRING=
# or
AZURE_ACCOUNT_NAME=
AZURE_ACCOUNT_KEY=

AZURE_CONTAINER_NAME=default-container
```

## Usage
```python
from dotenv import load_dotenv
from storage_settings import StorageSettings
from datalake_blob_provider import DataLakeBlobProvider

load_dotenv()
settings = StorageSettings.from_env()
provider = DataLakeBlobProvider(settings)

# Upload bytes
provider.upload_blob("hello.txt", b"hello world", overwrite=True)

# Upload file
provider.upload_file("./local-file.bin")

# List
print(provider.list_blobs(prefix="hello"))

# Download
data = provider.download_blob("hello.txt")
print(data)

# Download to file
provider.download_to_file("hello.txt", "./out/hello.txt")

# Delete
provider.delete_blob("hello.txt")
```

## Notes
- This module focuses on core CRUD-style blob operations.
- For archive-tier, lifecycle, or rehydration features, see the previous task implementation referenced in your workspace.
