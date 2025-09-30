import os
from .local import LocalStorageProvider
from .azure_blob import AzureBlobStorageProvider

def get_storage_provider():
    provider = os.getenv("STORAGE_PROVIDER", "local").lower()

    if provider == "azure":
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        container_name = os.getenv("AZURE_CONTAINER", "my-container")

        if not connection_string:
            raise ValueError("AZURE_STORAGE_CONNECTION_STRING is not set")

        return AzureBlobStorageProvider(connection_string, container_name)

    # Default to Local
    base_directory = os.getenv("LOCAL_STORAGE_PATH", "local_storage")
    return LocalStorageProvider(base_directory)
