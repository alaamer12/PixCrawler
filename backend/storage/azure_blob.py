from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
from typing import List, Optional
from .base import StorageProvider
import os

class AzureBlobStorageProvider(StorageProvider):
    def __init__(self, connection_string: str, container_name: str):
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_client = self.blob_service_client.get_container_client(container_name)
        try:
            self.container_client.create_container()
        except Exception:
            pass

    def upload(self, file_path: str, destination_path: str) -> None:
        with open(file_path, "rb") as data:
            self.container_client.upload_blob(name=destination_path, data=data, overwrite=True)

    def download(self, file_path: str, destination_path: str) -> None:
        blob_client = self.container_client.get_blob_client(file_path)
        with open(destination_path, "wb") as file:
            data = blob_client.download_blob()
            file.write(data.readall())

    def delete(self, file_path: str) -> None:
        self.container_client.delete_blob(file_path)

    def list_files(self, prefix: Optional[str] = None) -> List[str]:
        return [blob.name for blob in self.container_client.list_blobs(name_starts_with=prefix or "")]

    def generate_presigned_url(self, file_path: str, expires_in: int = 3600) -> str:
        sas_token = generate_blob_sas(
            account_name=self.blob_service_client.account_name,
            container_name=self.container_client.container_name,
            blob_name=file_path,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(seconds=expires_in)
        )
        return f"{self.container_client.url}/{file_path}?{sas_token}"
