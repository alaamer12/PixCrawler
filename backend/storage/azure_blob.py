"""
Azure Blob Storage provider for PixCrawler.

This module provides Azure Blob Storage integration for storing datasets
with support for hot, cool, and archive tiers for cost optimization.
"""

import os
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List, BinaryIO
from urllib.parse import urlparse

try:
    from azure.storage.blob.aio import BlobServiceClient
    from azure.storage.blob import BlobSasPermissions, generate_blob_sas
    from azure.core.exceptions import AzureError, ResourceNotFoundError
except ImportError:
    raise ImportError(
        "Azure Blob Storage dependencies not installed. "
        "Install with: pip install azure-storage-blob"
    )

from backend.storage.base import BaseStorageProvider
from utility.logging_config import get_logger

logger = get_logger(__name__)

class AzureBlobStorageProvider(BaseStorageProvider):
    """Azure Blob Storage provider with tier management."""
    
    def __init__(
        self,
        connection_string: Optional[str] = None,
        account_name: Optional[str] = None,
        account_key: Optional[str] = None,
        container_name: str = "pixcrawler-datasets",
        default_tier: str = "hot"
    ):
        """
        Initialize Azure Blob Storage provider.
        
        Args:
            connection_string: Azure Storage connection string (preferred)
            account_name: Storage account name (alternative to connection string)
            account_key: Storage account key (alternative to connection string)
            container_name: Blob container name
            default_tier: Default access tier (hot, cool, archive)
        """
        self.container_name = container_name
        self.default_tier = default_tier.lower()
        
        # Validate tier
        if self.default_tier not in ["hot", "cool", "archive"]:
            raise ValueError(f"Invalid tier: {self.default_tier}. Must be hot, cool, or archive")
        
        # Initialize client
        if connection_string:
            self.client = BlobServiceClient.from_connection_string(connection_string)
        elif account_name and account_key:
            account_url = f"https://{account_name}.blob.core.windows.net"
            self.client = BlobServiceClient(account_url=account_url, credential=account_key)
        else:
            raise ValueError(
                "Must provide either connection_string or both account_name and account_key"
            )
        
        self.account_name = account_name or self._extract_account_name(connection_string)
        self.account_key = account_key or self._extract_account_key(connection_string)
        
        logger.info(f"Initialized Azure Blob Storage: {self.account_name}/{self.container_name}")
    
    def _extract_account_name(self, connection_string: Optional[str]) -> Optional[str]:
        """Extract account name from connection string."""
        if not connection_string:
            return None
        
        for part in connection_string.split(';'):
            if part.startswith('AccountName='):
                return part.split('=', 1)[1]
        return None
    
    def _extract_account_key(self, connection_string: Optional[str]) -> Optional[str]:
        """Extract account key from connection string."""
        if not connection_string:
            return None
        
        for part in connection_string.split(';'):
            if part.startswith('AccountKey='):
                return part.split('=', 1)[1]
        return None
    
    async def _ensure_container_exists(self) -> None:
        """Ensure the blob container exists."""
        try:
            container_client = self.client.get_container_client(self.container_name)
            await container_client.get_container_properties()
        except ResourceNotFoundError:
            logger.info(f"Creating container: {self.container_name}")
            await self.client.create_container(
                name=self.container_name,
                public_access=None,  # Private container
                metadata={
                    "purpose": "pixcrawler-datasets",
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            logger.info(f"Container created: {self.container_name}")
    
    async def upload_file(
        self,
        file_path: str,
        blob_name: str,
        metadata: Optional[Dict[str, str]] = None,
        tier: Optional[str] = None
    ) -> str:
        """
        Upload file to Azure Blob Storage.
        
        Args:
            file_path: Local file path to upload
            blob_name: Blob name in container
            metadata: Optional metadata dictionary
            tier: Access tier (hot, cool, archive)
        
        Returns:
            Blob URL
        """
        await self._ensure_container_exists()
        
        tier = tier or self.default_tier
        
        try:
            blob_client = self.client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # Prepare metadata
            upload_metadata = {
                "uploaded_at": datetime.utcnow().isoformat(),
                "original_path": file_path,
                "tier": tier
            }
            if metadata:
                upload_metadata.update(metadata)
            
            # Upload file
            with open(file_path, 'rb') as data:
                await blob_client.upload_blob(
                    data,
                    blob_type="BlockBlob",
                    standard_blob_tier=tier,
                    metadata=upload_metadata,
                    overwrite=True
                )
            
            blob_url = blob_client.url
            logger.info(f"Uploaded to Azure Blob: {blob_name} (tier: {tier})")
            
            return blob_url
            
        except AzureError as e:
            logger.error(f"Failed to upload {file_path} to Azure Blob: {e}")
            raise
    
    async def upload_directory(
        self,
        directory_path: str,
        blob_prefix: str = "",
        tier: Optional[str] = None
    ) -> List[str]:
        """
        Upload entire directory to Azure Blob Storage.
        
        Args:
            directory_path: Local directory path
            blob_prefix: Prefix for blob names
            tier: Access tier for all files
        
        Returns:
            List of uploaded blob URLs
        """
        await self._ensure_container_exists()
        
        directory = Path(directory_path)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        uploaded_urls = []
        
        # Upload all files in directory
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                # Create blob name with prefix
                relative_path = file_path.relative_to(directory)
                blob_name = f"{blob_prefix}/{relative_path}".replace("\\", "/").lstrip("/")
                
                try:
                    url = await self.upload_file(
                        str(file_path),
                        blob_name,
                        metadata={
                            "directory_upload": "true",
                            "relative_path": str(relative_path)
                        },
                        tier=tier
                    )
                    uploaded_urls.append(url)
                except Exception as e:
                    logger.error(f"Failed to upload {file_path}: {e}")
        
        logger.info(f"Uploaded directory {directory_path}: {len(uploaded_urls)} files")
        return uploaded_urls
    
    async def download_file(self, blob_name: str, local_path: str) -> bool:
        """
        Download file from Azure Blob Storage.
        
        Args:
            blob_name: Blob name in container
            local_path: Local file path to save
        
        Returns:
            Success status
        """
        try:
            blob_client = self.client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # Create directory if needed
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Download blob
            with open(local_path, 'wb') as download_file:
                download_stream = await blob_client.download_blob()
                async for chunk in download_stream.chunks():
                    download_file.write(chunk)
            
            logger.info(f"Downloaded from Azure Blob: {blob_name} -> {local_path}")
            return True
            
        except AzureError as e:
            logger.error(f"Failed to download {blob_name}: {e}")
            return False
    
    async def delete_file(self, blob_name: str) -> bool:
        """
        Delete file from Azure Blob Storage.
        
        Args:
            blob_name: Blob name to delete
        
        Returns:
            Success status
        """
        try:
            blob_client = self.client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            await blob_client.delete_blob()
            logger.info(f"Deleted from Azure Blob: {blob_name}")
            return True
            
        except ResourceNotFoundError:
            logger.warning(f"Blob not found for deletion: {blob_name}")
            return True  # Consider missing file as successful deletion
        except AzureError as e:
            logger.error(f"Failed to delete {blob_name}: {e}")
            return False
    
    async def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """
        List files in Azure Blob Storage.
        
        Args:
            prefix: Blob name prefix filter
        
        Returns:
            List of file information dictionaries
        """
        try:
            container_client = self.client.get_container_client(self.container_name)
            
            files = []
            async for blob in container_client.list_blobs(name_starts_with=prefix):
                files.append({
                    "name": blob.name,
                    "size": blob.size,
                    "last_modified": blob.last_modified,
                    "tier": getattr(blob, 'blob_tier', 'unknown'),
                    "url": f"{container_client.url}/{blob.name}",
                    "metadata": blob.metadata or {}
                })
            
            return files
            
        except AzureError as e:
            logger.error(f"Failed to list blobs: {e}")
            return []
    
    async def get_download_url(
        self,
        blob_name: str,
        expiry_hours: int = 1
    ) -> Optional[str]:
        """
        Generate secure download URL with SAS token.
        
        Args:
            blob_name: Blob name
            expiry_hours: URL expiry time in hours
        
        Returns:
            Secure download URL or None if failed
        """
        if not self.account_key:
            logger.error("Account key required for SAS token generation")
            return None
        
        try:
            # Generate SAS token
            sas_token = generate_blob_sas(
                account_name=self.account_name,
                container_name=self.container_name,
                blob_name=blob_name,
                account_key=self.account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
            )
            
            # Construct URL
            blob_url = f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}?{sas_token}"
            
            logger.info(f"Generated download URL for {blob_name} (expires in {expiry_hours}h)")
            return blob_url
            
        except Exception as e:
            logger.error(f"Failed to generate download URL for {blob_name}: {e}")
            return None
    
    async def change_tier(self, blob_name: str, tier: str) -> bool:
        """
        Change blob access tier for cost optimization.
        
        Args:
            blob_name: Blob name
            tier: New tier (hot, cool, archive)
        
        Returns:
            Success status
        """
        if tier.lower() not in ["hot", "cool", "archive"]:
            logger.error(f"Invalid tier: {tier}")
            return False
        
        try:
            blob_client = self.client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            await blob_client.set_standard_blob_tier(tier.lower())
            logger.info(f"Changed tier for {blob_name}: {tier}")
            return True
            
        except AzureError as e:
            logger.error(f"Failed to change tier for {blob_name}: {e}")
            return False
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Storage statistics dictionary
        """
        try:
            container_client = self.client.get_container_client(self.container_name)
            
            stats = {
                "total_files": 0,
                "total_size": 0,
                "tiers": {"hot": 0, "cool": 0, "archive": 0, "unknown": 0}
            }
            
            async for blob in container_client.list_blobs():
                stats["total_files"] += 1
                stats["total_size"] += blob.size or 0
                
                tier = getattr(blob, 'blob_tier', 'unknown')
                if tier in stats["tiers"]:
                    stats["tiers"][tier] += 1
                else:
                    stats["tiers"]["unknown"] += 1
            
            return stats
            
        except AzureError as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {"error": str(e)}
    
    async def close(self) -> None:
        """Close the Azure Blob Storage client."""
        try:
            await self.client.close()
            logger.info("Azure Blob Storage client closed")
        except Exception as e:
            logger.error(f"Error closing Azure Blob Storage client: {e}")


# Factory function for easy initialization
def create_azure_blob_provider(
    connection_string: Optional[str] = None,
    account_name: Optional[str] = None,
    account_key: Optional[str] = None,
    container_name: str = "pixcrawler-datasets",
    default_tier: str = "hot"
) -> AzureBlobStorageProvider:
    """
    Create Azure Blob Storage provider with environment variable fallback.
    
    Args:
        connection_string: Azure Storage connection string
        account_name: Storage account name
        account_key: Storage account key
        container_name: Blob container name
        default_tier: Default access tier
    
    Returns:
        Configured Azure Blob Storage provider
    """
    # Try environment variables if not provided
    connection_string = connection_string or os.getenv("AZURE_BLOB_CONNECTION_STRING")
    account_name = account_name or os.getenv("AZURE_BLOB_ACCOUNT_NAME")
    account_key = account_key or os.getenv("AZURE_BLOB_ACCOUNT_KEY")
    container_name = os.getenv("AZURE_BLOB_CONTAINER_NAME", container_name)
    default_tier = os.getenv("AZURE_BLOB_DEFAULT_TIER", default_tier)
    
    return AzureBlobStorageProvider(
        connection_string=connection_string,
        account_name=account_name,
        account_key=account_key,
        container_name=container_name,
        default_tier=default_tier
    )