"""
Celery task for processing a single chunk of images.

This module defines the process_chunk_task which orchestrates the entire
pipeline: Download -> Validate -> Compress -> Upload -> Cleanup.
"""

import os
import tempfile
from typing import Optional
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from pixcrawler.chunk_worker.src.utils.logging import get_logger
from pixcrawler.chunk_worker.src.services.downloader import ChunkDownloader
from pixcrawler.chunk_worker.src.services.validator import ChunkValidator
from pixcrawler.chunk_worker.src.services.uploader import ChunkUploader
from pixcrawler.chunk_worker.src.services.cleanup import ChunkCleanup
from pixcrawler.chunk_worker.src.services.status_manager import StatusManager
from pixcrawler.chunk_worker.src.utils.retry import get_retry_strategy
from utility.compress.archiver import Archiver
from pathlib import Path

@get_retry_strategy(max_attempts=2)
def compress_directory(source_dir: str, zip_path: str, logger) -> str:
    """Helper to compress directory with retry logic."""
    logger.info(f"Starting compression of {source_dir} to {zip_path}")
    if not os.path.exists(source_dir) or not os.listdir(source_dir):
        raise ValueError(f"Source directory {source_dir} is empty or does not exist")
    
    archiver = Archiver(Path(source_dir))
    created_path = archiver.create(
        output=Path(zip_path),
        use_tar=False,
        kind="zip",
        level=6
    )
    logger.info(f"Compression completed: {created_path}")
    return str(created_path)

@shared_task(bind=True, acks_late=True, name='process_chunk_task')
def process_chunk_task(self, chunk_id: int, *, metadata: Optional[dict] = None) -> str:
    """
    Process a chunk of images.

    Pipeline:
    1. Download images using Builder package (with retries).
    2. Validate images using Validator package (remove corrupted/duplicates).
    3. Compress valid images to ZIP using utility.compress.
    4. Upload ZIP to Azure Blob Storage (with retries).
    5. Cleanup temporary files.

    Args:
        chunk_id: Unique ID of the chunk.
        metadata: Dictionary containing task metadata, must include 'keyword'.
    
    Returns:
        str: The URL of the uploaded blob.
        
    Raises:
        ValueError: If validation fails (non-retriable) or keyword is missing.
        Exception: If other errors occur (potentially retriable).
    """
    # Extract keyword
    if not metadata or 'keyword' not in metadata:
        raise ValueError("Metadata must contain 'keyword'")
    
    keyword = metadata['keyword']

    # Initial logger
    logger = get_logger(self.request.id, chunk_id, "INIT")
    logger.info(f"Received task for chunk {chunk_id}, keyword: '{keyword}'")
    
    status_manager = StatusManager(logger)
    status_manager.update_status(chunk_id, "PROCESSING")
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix=f"chunk_{chunk_id}_")
    download_dir = os.path.join(temp_dir, "images")
    output_dir = os.path.join(temp_dir, "output")
    
    # Ensure directories exist
    os.makedirs(download_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    zip_path: Optional[str] = None
    cleanup_service = ChunkCleanup(logger)
    
    try:
        # 1. Download Phase
        logger = get_logger(self.request.id, chunk_id, "DOWNLOAD")
        downloader = ChunkDownloader(logger)
        # Download 500 images
        downloader.download_chunk(keyword, download_dir, target_count=500)
        
        # 2. Validation Phase
        logger = get_logger(self.request.id, chunk_id, "VALIDATE")
        validator = ChunkValidator(logger)
        validator.validate_chunk(download_dir)
        
        # 3. Compression Phase
        logger = get_logger(self.request.id, chunk_id, "COMPRESS")
        zip_filename = f"chunk_{chunk_id}.zip"
        zip_path = os.path.join(output_dir, zip_filename)
        
        # Use helper with retry
        compress_directory(download_dir, zip_path, logger)
        
        # 4. Upload Phase
        logger = get_logger(self.request.id, chunk_id, "UPLOAD")
        conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        container = os.getenv("AZURE_CONTAINER_NAME", "datasets")
        
        blob_url: str
        if not conn_str:
            logger.warning("AZURE_STORAGE_CONNECTION_STRING not set. Skipping upload in dev mode.")
            blob_url = f"file://{zip_path}" # Mock URL for dev
        else:
            uploader = ChunkUploader(logger, conn_str, container)
            blob_url = uploader.upload_chunk(zip_path)
        
        # Success
        logger = get_logger(self.request.id, chunk_id, "COMPLETE")
        logger.info(f"Pipeline completed successfully. Blob URL: {blob_url}")
        status_manager.update_status(chunk_id, "COMPLETED", details={"url": blob_url})
        
        return blob_url

    except ValueError as ve:
        # Validation errors or other non-retriable errors
        logger = get_logger(self.request.id, chunk_id, "ERROR")
        logger.error(f"Non-retriable error: {ve}")
        status_manager.update_status(chunk_id, "FAILED", details={"error": str(ve)})
        # Do not retry
        raise ve

    except Exception as exc:
        logger = get_logger(self.request.id, chunk_id, "ERROR")
        logger.error(f"Task failed with error: {exc}")
        status_manager.update_status(chunk_id, "FAILED", details={"error": str(exc)})
        
        # Retry logic for recoverable errors (if Tenacity didn't solve it)
        # We retry the whole task for unexpected failures that might be transient
        try:
            logger.info("Retrying task...")
            self.retry(exc=exc, countdown=60, max_retries=3)
        except MaxRetriesExceededError:
            logger.error("Max retries exceeded for task.")
            raise exc
            
    finally:
        # Cleanup Phase
        logger = get_logger(self.request.id, chunk_id, "CLEANUP")
        cleanup_service.cleanup(temp_dir)
