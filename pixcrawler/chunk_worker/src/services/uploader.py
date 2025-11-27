"""
Uploader service for the Chunk Worker.

This module handles uploading the compressed ZIP file to Azure Blob Storage.
"""

import os
from azure.storage.blob import BlobServiceClient
from pixcrawler.chunk_worker.src.utils.logging import ContextLogger
from pixcrawler.chunk_worker.src.utils.retry import get_retry_strategy

class ChunkUploader:
    """
    Service responsible for uploading files to Azure Blob Storage.
    """

    def __init__(self, logger: ContextLogger, connection_string: str, container_name: str):
        """
        Initialize the ChunkUploader.

        Args:
            logger: ContextLogger instance for logging.
            connection_string: Azure Blob Storage connection string.
            container_name: Name of the container to upload to.
        """
        self.logger = logger
        self.connection_string = connection_string
        self.container_name = container_name
        
        if not self.connection_string:
            raise ValueError("Azure connection string is required")
        
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)

    @get_retry_strategy(max_attempts=5)
    def upload_chunk(self, file_path: str) -> str:
        """
        Upload a file to Azure Blob Storage.

        Args:
            file_path: Path to the file to upload.

        Returns:
            str: The URL of the uploaded blob.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File to upload not found: {file_path}")

        blob_name = os.path.basename(file_path)
        self.logger.info(f"Starting upload of {file_path} to container '{self.container_name}' as '{blob_name}'")
        
        try:
            # Get blob client
            blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=blob_name)
            
            # Upload file
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
                
            url = blob_client.url
            self.logger.info(f"Upload completed. URL: {url}")
            return url
        except Exception as e:
            self.logger.error(f"Upload failed: {e}")
            raise
