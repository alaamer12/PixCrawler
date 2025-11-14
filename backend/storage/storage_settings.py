"""Configuration helpers for Azure Blob Storage access.

Defines the ``StorageSettings`` dataclass and utilities to load configuration
from environment variables.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class StorageSettings:
    """Settings required to connect to Azure Blob Storage.

    Attributes:
        connection_string: Azure Storage connection string. If provided, it
            takes precedence over ``account_name``/``account_key``.
        account_name: Storage account name when not using a connection string.
        account_key: Storage account key when not using a connection string.
        container_name: Default container to operate on.
    """
    connection_string: Optional[str] = None
    account_name: Optional[str] = None
    account_key: Optional[str] = None
    container_name: str = "default-container"

    @classmethod
    def from_env(cls) -> "StorageSettings":
        """Create settings from environment variables.

        Environment Variables:
            AZURE_STORAGE_CONNECTION_STRING: Full connection string.
            AZURE_ACCOUNT_NAME: Storage account name.
            AZURE_ACCOUNT_KEY: Storage account key.
            AZURE_CONTAINER_NAME: Default container name (optional).

        Returns:
            A ``StorageSettings`` instance populated from the environment.
        """
        import os
        return cls(
            connection_string=os.getenv("AZURE_STORAGE_CONNECTION_STRING"),
            account_name=os.getenv("AZURE_ACCOUNT_NAME"),
            account_key=os.getenv("AZURE_ACCOUNT_KEY"),
            container_name=os.getenv("AZURE_CONTAINER_NAME", "default-container"),
        )
