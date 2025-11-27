"""Enhanced storage factory with Archive Tier support for PixCrawler.

This module extends PixCrawler's storage factory to create storage providers
with archive tier support while maintaining backward compatibility.

Functions:
    create_storage_provider: Factory function to create storage providers
    create_archive_enabled_provider: Create Azure provider with archive support

Features:
    - Backward compatible with existing PixCrawler code
    - Automatic provider selection based on configuration
    - Archive tier support for Azure provider
    - Graceful fallback to standard provider
"""

from backend.storage.config import StorageSettings
from utility.logging_config import get_logger
from backend.storage.local import LocalStorageProvider
from backend.storage.azure_blob import AzureBlobStorageProvider
from backend.storage.azure_blob_archive import AzureBlobArchiveProvider, AccessTier

__all__ = ['create_storage_provider', 'create_archive_enabled_provider']

logger = get_logger(__name__)


def create_archive_enabled_provider(settings: StorageSettings):
    """Create Azure Blob Storage provider with archive tier support.

    Args:
        settings: Enhanced storage settings with archive tier configuration

    Returns:
        AzureBlobArchiveProvider instance

    Raises:
        ImportError: If azure-storage-blob is not installed
        ValueError: If Azure configuration is invalid

    Example:
        settings = StorageSettings(
            storage_provider="azure",
            azure_connection_string="...",
            azure_enable_archive_tier=True,
            azure_default_tier="hot"
        )
        provider = create_archive_enabled_provider(settings)
    """
    try:
        # Get tier enum from settings
        default_tier = settings.get_tier_enum()

        provider = AzureBlobArchiveProvider(
            connection_string=settings.azure_connection_string,
            container_name=settings.azure_container_name,
            max_retries=settings.azure_max_retries,
            enable_archive_tier=settings.azure_enable_archive_tier,
            default_tier=default_tier
        )

        logger.info(
            f"Created Azure Blob Storage provider with archive tier support "
            f"(default tier: {settings.azure_default_tier})"
        )
        return provider

    except ImportError as e:
        logger.error(f"Failed to import Azure archive provider: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to create archive-enabled provider: {e}")
        raise


def _handle_local() -> LocalStorageProvider:
    # Create local storage provider
    try:

        storage_path = settings.local_storage_path
        provider = LocalStorageProvider(base_directory=storage_path)

        logger.info(
            f"Created local storage provider at: {storage_path or 'default location'}")
        return provider

    except ImportError as e:
        logger.error(f"Failed to import local storage provider: {e}")
        raise ValueError(f"Local storage provider not available: {e}")

def _handle_azure() -> Union[AzureBlobStorageProvider, AzureBlobArchiveProvider]:
    # Create Azure storage provider with archive support
    if not settings.azure_connection_string:
        raise ValueError("Azure connection string is required for Azure provider")

    try:
        # Try to create archive-enabled provider
        if settings.azure_enable_archive_tier:
            try:
                return create_archive_enabled_provider(settings)
            except ImportError:
                logger.warning(
                    "Archive tier support not available, falling back to standard Azure provider"
                )

        # Fallback to standard Azure provider
        provider = AzureBlobStorageProvider(
            connection_string=settings.azure_connection_string,
            container_name=settings.azure_container_name,
            max_retries=settings.azure_max_retries
        )

        logger.info("Created standard Azure Blob Storage provider")
        return provider

    except ImportError as e:
        logger.error(f"Failed to import Azure storage provider: {e}")
        raise ValueError(f"Azure storage provider not available: {e}")


# noinspection D
def create_storage_provider(settings: StorageSettings):
    """Create storage provider based on configuration.

    Factory function that creates the appropriate storage provider
    (local or Azure) based on settings. For Azure, creates archive-enabled
    provider if archive tier is enabled, otherwise falls back to standard.

    Args:
        settings: Storage configuration settings

    Returns:
        Storage provider instance (LocalStorageProvider or AzureBlobArchiveProvider)

    Raises:
        ValueError: If provider type is invalid or configuration is incomplete
        ImportError: If required dependencies are not installed

    Example:
        # From environment variables or .env file
        settings = StorageSettings()
        provider = create_storage_provider(settings)

        # Upload file (works with both local and Azure)
        provider.upload("image.jpg", "images/image.jpg")

        # Archive file (only works with Azure archive-enabled provider)
        if hasattr(provider, 'archive_blob'):
            provider.archive_blob("images/old_image.jpg")
    """
    provider_type = settings.storage_provider.lower()

    if provider_type == "local":
        _handle_local()

    elif provider_type == "azure":
        _handle_azure()

    else:
        raise ValueError(
            f"Invalid storage provider: {provider_type}. "
            "Must be 'local' or 'azure'"
        )


# Convenience function for backward compatibility
def get_storage_provider(settings: StorageSettings = None):
    """Get storage provider instance (convenience wrapper).

    Args:
        settings: Optional storage settings (creates new if not provided)

    Returns:
        Storage provider instance
    """
    if settings is None:
        settings = StorageSettings()

    return create_storage_provider(settings)
