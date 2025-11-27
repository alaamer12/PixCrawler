"""Data Lake Storage (Blob API) provider utilities.

Implements upload, download, list, and delete operations against Azure Blob
Storage (compatible with ADLS Gen2 accounts via the Blob endpoint).

This module provides a thin convenience wrapper around the Azure SDK to perform
common blob operations.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterable, Optional, Union, List, Dict, Any

from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import (
    BlobServiceClient,
    ContainerClient,
)

from .storage_settings import StorageSettings


logger = logging.getLogger(__name__)


BytesLike = Union[bytes, bytearray, memoryview]
Uploadable = Union[BytesLike, BinaryIO, str, Path]


@dataclass
class BlobInfo:
    """Metadata about a blob.

    Attributes:
        name: Blob name including any virtual directories.
        size: Size in bytes, if known.
        content_type: MIME type if available.
        last_modified: Last modified timestamp ISO string, if available.
    """
    name: str
    size: Optional[int] = None
    content_type: Optional[str] = None
    last_modified: Optional[str] = None


class DataLakeBlobProvider:
    def __init__(self, settings: StorageSettings):
        """Initialize the provider.

        Args:
            settings: Storage configuration including credentials and container.
        """
        self.settings = settings
        self._blob_service_client: Optional[BlobServiceClient] = None
        self._container_client: Optional[ContainerClient] = None
        self._initialize_clients()

    def _initialize_clients(self) -> None:
        """Create SDK clients for the target account and container.

        Chooses between a connection string or account name/key. Ensures the
        container exists (creates it if missing).

        Raises:
            ValueError: If neither a connection string nor account credentials
                are provided.
        """
        if self.settings.connection_string:
            self._blob_service_client = BlobServiceClient.from_connection_string(
                self.settings.connection_string
            )
        elif self.settings.account_name and self.settings.account_key:
            account_url = f"https://{self.settings.account_name}.blob.core.windows.net"
            self._blob_service_client = BlobServiceClient(
                account_url=account_url,
                credential=self.settings.account_key,
            )
        else:
            raise ValueError("Provide either connection_string or account_name/account_key")

        self._container_client = self._blob_service_client.get_container_client(
            self.settings.container_name
        )
        try:
            self._container_client.create_container()
            logger.info("Created container '%s'", self.settings.container_name)
        except Exception as e:
            # Container may already exist
            logger.debug("create_container skipped: %s", e)

    # ----------------------------
    # Helpers
    # ----------------------------
    @staticmethod
    def _to_stream(data: Uploadable) -> BinaryIO:
        """Normalize input data into a binary stream.

        Accepts bytes-like data, a filesystem path, or a file-like object and
        returns a readable binary stream suitable for upload.

        Args:
            data: Bytes-like object, file path, or binary file-like object.

        Returns:
            A binary stream positioned at the beginning.
        """
        # Accepts bytes-like, file path, or file-like
        if isinstance(data, (bytes, bytearray, memoryview)):
            import io
            return io.BytesIO(bytes(data))
        if isinstance(data, (str, Path)):
            return open(Path(data), "rb")
        # assume file-like (BinaryIO)
        return data  # type: ignore[return-value]

    # ----------------------------
    # Core operations
    # ----------------------------
    def upload_blob(
        self,
        blob_name: str,
        data: Uploadable,
        *,
        overwrite: bool = True,
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upload data to a blob.

        Args:
            blob_name: Target blob name including any virtual directories.
            data: Bytes-like object, path to a file, or a binary file-like object.
            overwrite: Whether to overwrite the blob if it already exists.
            metadata: Optional user-defined metadata.
            content_type: MIME type to set for the blob.

        Returns:
            A dict with keys such as ``blob_name``, ``etag``, ``last_modified``,
            and ``success``. On failure, includes ``error``.
        """
        blob_client = self._container_client.get_blob_client(blob_name)
        stream = None
        try:
            stream = self._to_stream(data)
            result = blob_client.upload_blob(
                stream,
                overwrite=overwrite,
                metadata=metadata,
                content_type=content_type,
            )
            logger.info("Uploaded blob '%s'", blob_name)
            return {
                "blob_name": blob_name,
                "etag": getattr(result, "etag", None) or (result.get("etag") if isinstance(result, dict) else None),
                "last_modified": getattr(result, "last_modified", None)
                or (result.get("last_modified") if isinstance(result, dict) else None),
                "success": True,
            }
        except Exception as e:
            logger.error("Upload failed for '%s': %s", blob_name, e)
            return {"blob_name": blob_name, "success": False, "error": str(e)}
        finally:
            try:
                if stream and hasattr(stream, "close"):
                    stream.close()  # only closes if we opened a file/BytesIO
            except Exception:
                pass

    def upload_file(
        self,
        file_path: Union[str, Path],
        blob_name: Optional[str] = None,
        *,
        overwrite: bool = True,
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upload a local file to a blob.

        Args:
            file_path: Path to the local file.
            blob_name: Optional destination blob name. Defaults to the filename.
            overwrite: Whether to overwrite the blob if it already exists.
            metadata: Optional user-defined metadata.
            content_type: MIME type to set for the blob.

        Returns:
            Same dictionary structure as ``upload_blob``.
        """
        p = Path(file_path)
        name = blob_name or p.name
        return self.upload_blob(name, p, overwrite=overwrite, metadata=metadata, content_type=content_type)

    def download_blob(self, blob_name: str) -> Optional[bytes]:
        """Download a blob's contents.

        Args:
            blob_name: Name of the blob to download.

        Returns:
            The blob contents as bytes, or ``None`` if not found or on error.
        """
        try:
            blob_client = self._container_client.get_blob_client(blob_name)
            stream = blob_client.download_blob()
            return stream.readall()
        except ResourceNotFoundError:
            logger.warning("Blob not found: '%s'", blob_name)
            return None
        except Exception as e:
            logger.error("Download failed for '%s': %s", blob_name, e)
            return None

    def download_to_file(self, blob_name: str, dest_path: Union[str, Path]) -> bool:
        """Download a blob directly into a local file.

        Args:
            blob_name: Name of the blob to download.
            dest_path: Destination file path.

        Returns:
            ``True`` on success, ``False`` if not found or on error.
        """
        try:
            blob_client = self._container_client.get_blob_client(blob_name)
            p = Path(dest_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "wb") as f:
                stream = blob_client.download_blob()
                stream.readinto(f)
            return True
        except ResourceNotFoundError:
            logger.warning("Blob not found: '%s'", blob_name)
            return False
        except Exception as e:
            logger.error("Download to file failed for '%s': %s", blob_name, e)
            return False

    def list_blobs(self, prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        """List blobs in the container.

        Args:
            prefix: Optional name prefix to filter blobs.

        Returns:
            A list of dictionaries, each containing fields such as ``name``,
            ``size``, ``last_modified``, and ``content_type``.
        """
        try:
            result: List[Dict[str, Any]] = []
            for blob in self._container_client.list_blobs(name_starts_with=prefix):
                result.append(
                    {
                        "name": blob.name,
                        "size": getattr(blob, "size", None),
                        "last_modified": getattr(blob, "last_modified", None).isoformat()
                        if getattr(blob, "last_modified", None)
                        else None,
                        "content_type": getattr(getattr(blob, "content_settings", None), "content_type", None),
                    }
                )
            return result
        except Exception as e:
            logger.error("List blobs failed: %s", e)
            return []

    def delete_blob(self, blob_name: str) -> bool:
        """Delete a blob.

        Args:
            blob_name: Name of the blob to delete.

        Returns:
            ``True`` on success, ``False`` if the blob does not exist or on error.
        """
        try:
            blob_client = self._container_client.get_blob_client(blob_name)
            blob_client.delete_blob()
            logger.info("Deleted blob '%s'", blob_name)
            return True
        except ResourceNotFoundError:
            logger.warning("Blob not found: '%s'", blob_name)
            return False
        except Exception as e:
            logger.error("Delete failed for '%s': %s", blob_name, e)
            return False
