# PixCrawler Chunk Worker

The Chunk Worker is a specialized Celery worker designed to process image datasets in chunks. It handles the end-to-end pipeline of downloading, validating, compressing, and uploading images to Azure Blob Storage.


## 🧪 Testing

A test script is provided to verify the pipeline logic (using mocks):

```bash
# From the project root
uv run pytest tests/test_process_chunk.py
```

## 🏗️ Architecture

```ascii
+-------------+      +-----------+      +-----------+      +------------+      +-------------+
|  Celery     | ---> | Download  | ---> | Validate  | ---> | Compress   | ---> | Upload      |
|  Task       |      | (Builder) |      | (Validator)|     | (Archiver) |      | (Azure Blob)|
+-------------+      +-----------+      +-----------+      +------------+      +-------------+
       |                   |                  |                  |                   |
       v                   v                  v                  v                   v
+---------------------------------------------------------------------------------------+
|                                  Context-Aware Logging                                |
|                   [task_id=...][chunk=...][phase=...]                                 |
+---------------------------------------------------------------------------------------+
       |
       v
+-------------+      +---------------+
|   Cleanup   |      | StatusManager |
|  (Finally)  |      | (DB Updates)  |
+-------------+      +---------------+
```

## 🚀 Processing Pipeline

1.  **Initialization**: The task starts, updates chunk status to `PROCESSING` via `StatusManager`, and creates a secure temporary directory.
2.  **Download Phase**:
    *   Uses `builder` package to download images for the given keyword.
    *   Target: 500 images per chunk.
    *   **Retry Logic**: Uses Tenacity to retry network failures (3 attempts).
3.  **Validation Phase**:
    *   Uses `validator` package to check image integrity.
    *   Removes corrupted files and duplicates.
    *   **Failure**: If no valid images remain, the task fails immediately (non-retriable).
4.  **Compression Phase**:
    *   Compresses valid images into a ZIP file (`chunk_{id}.zip`) using `utility.compress.archiver`.
    *   **Retry Logic**: Retries once on filesystem errors.
5.  **Upload Phase**:
    *   Uploads the ZIP file to Azure Blob Storage.
    *   **Retry Logic**: Retries up to 5 times for connection/service errors.
6.  **Cleanup Phase**:
    *   Always runs (finally block).
    *   Removes all temporary files and directories.
7.  **Completion**:
    *   Updates chunk status to `COMPLETED` (or `FAILED`) via `StatusManager`.
    *   Returns the Azure Blob URL.

## 🛠️ Configuration

The worker uses environment variables for configuration. Ensure these are set in your `.env` file:

```env
# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net"
AZURE_CONTAINER_NAME="datasets"

# Celery (from celery_core)
PIXCRAWLER_CELERY_BROKER_URL="redis://localhost:6379/0"
PIXCRAWLER_CELERY_RESULT_BACKEND="redis://localhost:6379/1"
```

## 🏃 Running the Worker

To start the Celery worker:

```bash
# From the project root
celery -A pixcrawler.chunk_worker.src.celery_app worker --loglevel=info
```

## 📁 Directory Structure

```
src/
├── celery_app.py          # Celery application entry point
├── tasks/
│   └── process_chunk.py   # Main task logic
├── services/
│   ├── downloader.py      # Wraps builder package
│   ├── validator.py       # Wraps validator package
│   ├── uploader.py        # Azure upload
│   ├── cleanup.py         # Resource cleanup
│   └── status_manager.py  # Chunk status updates
└── utils/
    ├── logging.py         # Context-aware logging
    └── retry.py           # Tenacity retry strategies
```

## 🤖 Changes Made by the AI

The following improvements and fixes were applied to ensure strict adherence to the project architecture:

1.  **Celery Integration**:
    -   Modified `src/celery_app.py` to import the shared `celery_app` from `celery_core.app` instead of creating a new isolated instance.

2.  **Compression Logic**:
    -   Removed the redundant `src/services/compressor.py` service.
    -   Refactored `process_chunk_task` to use `utility.compress.archiver.Archiver` directly.
    -   Added a `compress_directory` helper with Tenacity retry logic to handle filesystem operations reliably.

3.  **Task Signature**:
    -   Updated `process_chunk_task` signature to `(self, chunk_id: int, *, metadata: Optional[dict]=None)` to match the required standard.
    -   Added validation to ensure `keyword` is present in `metadata`.

4.  **Error Handling**:
    -   Updated `ChunkDownloader` to raise `ConnectionError` on failure, ensuring Tenacity retries are triggered correctly.
    -   Verified that `ChunkValidator` raises `ValueError` for non-retriable validation failures.

5.  **Testing**:
    -   Updated `tests/test_process_chunk.py` to reflect the removal of `ChunkCompressor` and the new task signature.
    -   Added `os.listdir` patching to ensure tests pass with the new compression logic.
