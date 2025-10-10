"""Azure Blob Storage provider for PixCrawler backend.

This module implements Azure Blob Storage with optional dependency handling,
allowing the application to work without Azure SDK installed.

Classes:
    AzureBlobStorageProvider: Azure Blob Storage implementation

Features:
    - Optional azure-storage-blob dependency with graceful fallback
    - Comprehensive error handling and logging
    - SAS token generation for presigned URLs
    - Automatic container creation
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Union

from logging_config import get_logger

__all__ = ['AzureBlobStorageProvider', 'AZURE_AVAILABLE']

logger = get_logger(__name__)

# Try to import Azure SDK
try:
    from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    logger.warning("azure-storage-blob not installed. Azure storage provider unavailable.")


class AzureBlobStorageProvider:
    """Azure Blob Storage provider.
    
    Implements storage operations using Azure Blob Storage with
    proper error handling and optional dependency support.
    
    Attributes:
        blob_service_client: Azure Blob Service client
        container_client: Azure container client
        container_name: Name of the storage container
    
    Raises:
        ImportError: If azure-storage-blob is not installed
    """

    def __init__(self, connection_string: str, container_name: str, max_retries: int = 3) -> None:
        """Initialize Azure Blob Storage provider.
        
        Args:
            connection_string: Azure Storage connection string
            container_name: Name of the blob container
            max_retries: Maximum retry attempts for operations
            
        Raises:
            ImportError: If azure-storage-blob is not installed
            ValueError: If connection string or container name is invalid
        """
        if not AZURE_AVAILABLE:
            raise ImportError(
                "azure-storage-blob is not installed. "
                "Install it with: pip install azure-storage-blob"
            )
        
        if not connection_string:
            raise ValueError("Azure connection string cannot be empty")
        
        if not container_name:
            raise ValueError("Container name cannot be empty")
        
        try:
            self.blob_service_client = BlobServiceClient.from_connection_string(
                connection_string,
                max_single_get_size=4 * 1024 * 1024,  # 4MB
                max_chunk_get_size=4 * 1024 * 1024
            )
            self.container_name = container_name
            self.container_client = self.blob_service_client.get_container_client(container_name)
            
            # Create container if it doesn't exist
            if not self.container_client.exists():
                self.container_client.create_container()
                logger.info(f"Created Azure container: {container_name}")
            else:
                logger.info(f"Using existing Azure container: {container_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize Azure storage: {e}")
            raise

    def upload(self, file_path: Union[str, Path], destination_path: str) -> None:
        """Upload a file to Azure Blob Storage.
        
        Args:
            file_path: Path to the local file to upload
            destination_path: Destination blob name
            
        Raises:
            FileNotFoundError: If source file doesn't exist
            IOError: If upload fails
        """
        source = Path(file_path)
        
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {file_path}")
        
        if not source.is_file():
            raise ValueError(f"Source path is not a file: {file_path}")
        
        try:
            with open(source, "rb") as data:
                self.container_client.upload_blob(
                    name=destination_path,
                    data=data,
                    overwrite=True
                )
            logger.debug(f"Uploaded file to Azure: {file_path} -> {destination_path}")
        except Exception as e:
            logger.error(f"Failed to upload file {file_path} to Azure: {e}")
            raise IOError(f"Azure upload failed: {e}") from e

    def download(self, file_path: str, destination_path: Union[str, Path]) -> None:
        """Download a file from Azure Blob Storage.
        
        Args:
            file_path: Blob name in storage
            destination_path: Local destination path
            
        Raises:
            FileNotFoundError: If blob doesn't exist
            IOError: If download fails
        """
        try:
            blob_client = self.container_client.get_blob_client(file_path)
            
            if not blob_client.exists():
                raise FileNotFoundError(f"Blob not found in Azure: {file_path}")
            
            destination = Path(destination_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            with open(destination, "wb") as file:
                download_stream = blob_client.download_blob()
                file.write(download_stream.readall())
            
            logger.debug(f"Downloaded file from Azure: {file_path} -> {destination_path}")
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to download file {file_path} from Azure: {e}")
            raise IOError(f"Azure download failed: {e}") from e

    def delete(self, file_path: str) -> None:
        """Delete a file from Azure Blob Storage.
        
        Args:
            file_path: Blob name in storage
            
        Raises:
            FileNotFoundError: If blob doesn't exist
            IOError: If deletion fails
        """
        try:
            blob_client = self.container_client.get_blob_client(file_path)
            
            if not blob_client.exists():
                raise FileNotFoundError(f"Blob not found in Azure: {file_path}")
            
            self.container_client.delete_blob(file_path)
            logger.debug(f"Deleted blob from Azure: {file_path}")
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete blob {file_path} from Azure: {e}")
            raise IOError(f"Azure deletion failed: {e}") from e

    def list_files(self, prefix: Optional[str] = None) -> List[str]:
        """List files in Azure Blob Storage with optional prefix filter.
        
        Args:
            prefix: Optional prefix to filter blobs
            
        Returns:
            List of blob names
            
        Raises:
            IOError: If listing fails
        """
        try:
            blobs = self.container_client.list_blobs(name_starts_with=prefix or "")
            file_list = [blob.name for blob in blobs]
            logger.debug(f"Listed {len(file_list)} blobs from Azure with prefix: {prefix}")
            return file_list
        except Exception as e:
            logger.error(f"Failed to list blobs from Azure: {e}")
            raise IOError(f"Azure listing failed: {e}") from e

    def generate_presigned_url(self, file_path: str, expires_in: int = 3600) -> str:
        """Generate a presigned URL for Azure blob access.
        
        Args:
            file_path: Blob name in storage
            expires_in: URL expiration time in seconds
            
        Returns:
            Presigned URL with SAS token
            
        Raises:
            FileNotFoundError: If blob doesn't exist
            IOError: If URL generation fails
        """
        try:
            blob_client = self.container_client.get_blob_client(file_path)
            
            if not blob_client.exists():
                raise FileNotFoundError(f"Blob not found in Azure: {file_path}")
            
            # Generate SAS token
            sas_token = generate_blob_sas(
                account_name=self.blob_service_client.account_name,
                container_name=self.container_name,
                blob_name=file_path,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(seconds=expires_in)
            )
            
            url = f"{blob_client.url}?{sas_token}"
            logger.debug(f"Generated presigned URL for Azure blob: {file_path}")
            return url
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for {file_path}: {e}")
            raise IOError(f"Azure URL generation failed: {e}") from e
