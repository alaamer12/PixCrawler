"""Azure services configuration settings.

This module provides comprehensive Azure configuration for all services used
in PixCrawler, including Blob Storage, App Service, Static Web Apps, and
Application Insights monitoring.

Classes:
    AzureBlobSettings: Azure Blob Storage configuration
    AzureAppServiceSettings: Azure App Service configuration
    AzureStaticWebAppSettings: Azure Static Web Apps configuration
    AzureMonitorSettings: Azure Application Insights configuration
    AzureSettings: Unified Azure configuration

Features:
    - Modular settings for each Azure service
    - Environment-based configuration
    - Flexible provider switching (Azure App Service ↔ Container Apps)
    - Production-grade defaults
    - Comprehensive validation
"""

from typing import Optional, List
from enum import Enum

from pydantic import Field, field_validator, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = [
    "AzureBlobSettings",
    "AzureAppServiceSettings",
    "AzureStaticWebAppSettings",
    "AzureMonitorSettings",
    "AzureSettings",
    "AccessTier",
    "RehydratePriority",
]


class AccessTier(str, Enum):
    """Azure Blob Storage access tiers."""
    HOT = "hot"
    COOL = "cool"
    ARCHIVE = "archive"


class RehydratePriority(str, Enum):
    """Azure Blob rehydration priority."""
    STANDARD = "standard"  # 15 hours
    HIGH = "high"  # <1 hour


class AzureBlobSettings(BaseSettings):
    """
    Azure Blob Storage configuration.
    
    Environment variables:
        AZURE_BLOB_CONNECTION_STRING: Storage account connection string
        AZURE_BLOB_ACCOUNT_NAME: Storage account name (alternative to connection string)
        AZURE_BLOB_ACCOUNT_KEY: Storage account key (alternative to connection string)
        AZURE_BLOB_CONTAINER_NAME: Default container name
        AZURE_BLOB_MAX_RETRIES: Maximum retry attempts
        AZURE_BLOB_TIMEOUT: Request timeout in seconds
        AZURE_BLOB_DEFAULT_TIER: Default access tier (hot/cool/archive)
        AZURE_BLOB_ENABLE_ARCHIVE: Enable archive tier features
        AZURE_BLOB_REHYDRATE_PRIORITY: Rehydration priority (standard/high)
        AZURE_BLOB_LIFECYCLE_ENABLED: Enable lifecycle management
        AZURE_BLOB_LIFECYCLE_COOL_AFTER_DAYS: Move to cool tier after N days
        AZURE_BLOB_LIFECYCLE_ARCHIVE_AFTER_DAYS: Move to archive tier after N days
        AZURE_BLOB_LIFECYCLE_DELETE_AFTER_DAYS: Delete after N days
    
    Cost Optimization:
        - Hot tier: $0.018/GB/month (baseline)
        - Cool tier: $0.010/GB/month (44% savings)
        - Archive tier: $0.001/GB/month (94% savings)
    """
    
    model_config = SettingsConfigDict(
        env_prefix="AZURE_BLOB_",
        env_file=[".env", "backend/.env"],
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Connection settings
    connection_string: Optional[SecretStr] = Field(
        default=None,
        description="Azure Storage connection string (recommended)",
        examples=["DefaultEndpointsProtocol=https;AccountName=..."]
    )
    account_name: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=24,
        pattern=r'^[a-z0-9]+$',
        description="Storage account name (alternative to connection string)",
        examples=["pixcrawlerstorage", "prodstorageacct"]
    )
    account_key: Optional[SecretStr] = Field(
        default=None,
        description="Storage account key (alternative to connection string)",
    )
    
    # Container settings
    container_name: str = Field(
        default="pixcrawler-datasets",
        min_length=3,
        max_length=63,
        pattern=r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$',
        description="Default blob container name",
        examples=["pixcrawler-datasets", "images-prod", "dev-storage"]
    )
    
    # Performance settings
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts for operations",
        examples=[3, 5, 10]
    )
    timeout: int = Field(
        default=300,
        ge=30,
        le=3600,
        description="Request timeout in seconds",
        examples=[60, 300, 600]
    )
    max_single_get_size: int = Field(
        default=32 * 1024 * 1024,  # 32MB
        ge=1024 * 1024,
        description="Maximum size for single GET request in bytes",
    )
    max_chunk_get_size: int = Field(
        default=4 * 1024 * 1024,  # 4MB
        ge=1024 * 1024,
        description="Maximum chunk size for GET requests in bytes",
    )
    
    # Access tier settings
    default_tier: AccessTier = Field(
        default=AccessTier.HOT,
        description="Default access tier for uploads",
        examples=[AccessTier.HOT, AccessTier.COOL, AccessTier.ARCHIVE]
    )
    enable_archive: bool = Field(
        default=True,
        description="Enable archive tier features for cost optimization",
    )
    rehydrate_priority: RehydratePriority = Field(
        default=RehydratePriority.STANDARD,
        description="Default rehydration priority for archived blobs",
        examples=[RehydratePriority.STANDARD, RehydratePriority.HIGH]
    )
    
    # Lifecycle management
    lifecycle_enabled: bool = Field(
        default=False,
        description="Enable automatic lifecycle management policies",
    )
    lifecycle_cool_after_days: Optional[int] = Field(
        default=None,
        ge=1,
        description="Move to Cool tier after N days (optional)",
        examples=[30, 60, 90]
    )
    lifecycle_archive_after_days: Optional[int] = Field(
        default=None,
        ge=1,
        description="Move to Archive tier after N days (optional)",
        examples=[90, 180, 365]
    )
    lifecycle_delete_after_days: Optional[int] = Field(
        default=None,
        ge=1,
        description="Delete blobs after N days (optional)",
        examples=[365, 2555, 3650]
    )
    
    # SAS token settings
    sas_token_expiry_hours: int = Field(
        default=1,
        ge=1,
        le=168,  # 7 days
        description="Default SAS token expiry in hours",
        examples=[1, 24, 72]
    )
    
    @model_validator(mode='after')
    def validate_connection_config(self) -> 'AzureBlobSettings':
        """Validate that either connection string or account name/key is provided."""
        import warnings
        
        has_connection_string = self.connection_string is not None
        has_account_credentials = self.account_name is not None and self.account_key is not None
        
        if not has_connection_string and not has_account_credentials:
            warnings.warn(
                "Azure Blob Storage not configured: Either connection_string or both "
                "account_name and account_key must be provided. "
                "Azure storage features will be disabled. "
                "Set AZURE_BLOB_CONNECTION_STRING or AZURE_BLOB_ACCOUNT_NAME/AZURE_BLOB_ACCOUNT_KEY "
                "environment variables to enable Azure storage.",
                UserWarning,
                stacklevel=2
            )
        
        return self
    
    @model_validator(mode='after')
    def validate_lifecycle_days(self) -> 'AzureBlobSettings':
        """Validate lifecycle management day progression."""
        if not self.lifecycle_enabled:
            return self
        
        days = []
        if self.lifecycle_cool_after_days:
            days.append(('cool', self.lifecycle_cool_after_days))
        if self.lifecycle_archive_after_days:
            days.append(('archive', self.lifecycle_archive_after_days))
        if self.lifecycle_delete_after_days:
            days.append(('delete', self.lifecycle_delete_after_days))
        
        # Check progression
        for i in range(len(days) - 1):
            if days[i][1] >= days[i + 1][1]:
                raise ValueError(
                    f"Lifecycle days must be in ascending order: "
                    f"{days[i][0]} ({days[i][1]}) >= {days[i + 1][0]} ({days[i + 1][1]})"
                )
        
        return self
    
    def get_connection_string(self) -> str:
        """Get connection string (either direct or constructed from account credentials)."""
        if self.connection_string:
            return self.connection_string.get_secret_value()
        
        if self.account_name and self.account_key:
            return (
                f"DefaultEndpointsProtocol=https;"
                f"AccountName={self.account_name};"
                f"AccountKey={self.account_key.get_secret_value()};"
                f"EndpointSuffix=core.windows.net"
            )
        
        raise ValueError("No valid connection configuration available")


class AzureAppServiceSettings(BaseSettings):
    """
    Azure App Service configuration.
    
    Environment variables:
        AZURE_APP_SERVICE_NAME: App Service name
        AZURE_APP_SERVICE_RESOURCE_GROUP: Resource group name
        AZURE_APP_SERVICE_SUBSCRIPTION_ID: Azure subscription ID
        AZURE_APP_SERVICE_REGION: Azure region
        AZURE_APP_SERVICE_SKU: App Service plan SKU
        AZURE_APP_SERVICE_WORKERS: Number of Gunicorn workers
        AZURE_APP_SERVICE_TIMEOUT: Request timeout
        AZURE_APP_SERVICE_ENABLE_REDIS: Enable local Redis
        AZURE_APP_SERVICE_ENABLE_CELERY: Enable Celery worker
    """
    
    model_config = SettingsConfigDict(
        env_prefix="AZURE_APP_SERVICE_",
        env_file=[".env", "backend/.env"],
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # App Service identity
    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=60,
        pattern=r'^[a-zA-Z0-9-]+$',
        description="App Service name",
        examples=["pixcrawler-backend", "pixcrawler-api-prod"]
    )
    resource_group: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=90,
        description="Azure resource group name",
        examples=["pixcrawler-rg", "production-resources"]
    )
    subscription_id: Optional[str] = Field(
        default=None,
        pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        description="Azure subscription ID (UUID format)",
    )
    
    # Deployment settings
    region: str = Field(
        default="eastus",
        description="Azure region for deployment",
        examples=["eastus", "westus2", "westeurope", "southeastasia"]
    )
    sku: str = Field(
        default="B1",
        pattern=r'^(F1|D1|B1|B2|B3|S1|S2|S3|P1V2|P2V2|P3V2|P1V3|P2V3|P3V3)$',
        description="App Service plan SKU",
        examples=["B1", "B2", "S1", "P1V2"]
    )
    
    # Runtime settings
    workers: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Number of Gunicorn workers",
        examples=[2, 4, 8]
    )
    timeout: int = Field(
        default=300,
        ge=30,
        le=1800,
        description="Request timeout in seconds",
        examples=[120, 300, 600]
    )
    
    # Feature flags
    enable_redis: bool = Field(
        default=True,
        description="Enable local Redis server",
    )
    enable_celery: bool = Field(
        default=True,
        description="Enable Celery worker in background",
    )
    celery_concurrency: int = Field(
        default=2,
        ge=1,
        le=16,
        description="Celery worker concurrency",
        examples=[2, 4, 8]
    )
    
    # Logging
    enable_application_logging: bool = Field(
        default=True,
        description="Enable application logging to Azure",
    )
    log_level: str = Field(
        default="INFO",
        pattern=r'^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$',
        description="Application log level",
        examples=["INFO", "WARNING", "ERROR"]
    )


class AzureStaticWebAppSettings(BaseSettings):
    """
    Azure Static Web Apps configuration (for Next.js frontend).
    
    Environment variables:
        AZURE_STATIC_WEB_APP_NAME: Static Web App name
        AZURE_STATIC_WEB_APP_RESOURCE_GROUP: Resource group name
        AZURE_STATIC_WEB_APP_REGION: Azure region
        AZURE_STATIC_WEB_APP_SKU: SKU tier (Free/Standard)
        AZURE_STATIC_WEB_APP_API_LOCATION: API location (optional)
    
    Note: Azure Static Web Apps is an alternative to Vercel for Next.js hosting.
    """
    
    model_config = SettingsConfigDict(
        env_prefix="AZURE_STATIC_WEB_APP_",
        env_file=[".env", "frontend/.env.local"],
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Static Web App identity
    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=60,
        pattern=r'^[a-zA-Z0-9-]+$',
        description="Static Web App name",
        examples=["pixcrawler-frontend", "pixcrawler-web-prod"]
    )
    resource_group: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=90,
        description="Azure resource group name",
        examples=["pixcrawler-rg", "production-resources"]
    )
    
    # Deployment settings
    region: str = Field(
        default="eastus2",
        description="Azure region for deployment",
        examples=["eastus2", "westus2", "westeurope"]
    )
    sku: str = Field(
        default="Free",
        pattern=r'^(Free|Standard)$',
        description="Static Web App SKU",
        examples=["Free", "Standard"]
    )
    
    # Build settings
    app_location: str = Field(
        default="/",
        description="App source code location",
        examples=["/", "/frontend", "/app"]
    )
    api_location: Optional[str] = Field(
        default=None,
        description="API source code location (optional)",
        examples=[None, "/api", "/backend"]
    )
    output_location: str = Field(
        default=".next",
        description="Build output location",
        examples=[".next", "out", "build"]
    )
    
    # Custom domain
    custom_domain: Optional[str] = Field(
        default=None,
        description="Custom domain name (optional)",
        examples=[None, "app.pixcrawler.com", "www.pixcrawler.com"]
    )


class AzureMonitorSettings(BaseSettings):
    """
    Azure Application Insights configuration.
    
    Environment variables:
        AZURE_MONITOR_CONNECTION_STRING: Application Insights connection string
        AZURE_MONITOR_INSTRUMENTATION_KEY: Instrumentation key (legacy)
        AZURE_MONITOR_ENABLED: Enable Application Insights
        AZURE_MONITOR_SAMPLING_RATE: Telemetry sampling rate (0.0-1.0)
        AZURE_MONITOR_LOG_LEVEL: Minimum log level to send
        AZURE_MONITOR_TRACK_DEPENDENCIES: Track dependency calls
        AZURE_MONITOR_TRACK_REQUESTS: Track HTTP requests
        AZURE_MONITOR_TRACK_EXCEPTIONS: Track exceptions
    """
    
    model_config = SettingsConfigDict(
        env_prefix="AZURE_MONITOR_",
        env_file=[".env", "backend/.env"],
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Connection settings
    connection_string: Optional[SecretStr] = Field(
        default=None,
        description="Application Insights connection string (recommended)",
        examples=["InstrumentationKey=...;IngestionEndpoint=..."]
    )
    instrumentation_key: Optional[SecretStr] = Field(
        default=None,
        pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        description="Application Insights instrumentation key (legacy)",
    )
    
    # Feature flags
    enabled: bool = Field(
        default=False,
        description="Enable Application Insights telemetry",
    )
    
    # Telemetry settings
    sampling_rate: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Telemetry sampling rate (0.0-1.0, 1.0 = 100%)",
        examples=[0.1, 0.5, 1.0]
    )
    log_level: str = Field(
        default="WARNING",
        pattern=r'^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$',
        description="Minimum log level to send to Application Insights",
        examples=["INFO", "WARNING", "ERROR"]
    )
    
    # Tracking options
    track_dependencies: bool = Field(
        default=True,
        description="Track dependency calls (DB, Redis, HTTP)",
    )
    track_requests: bool = Field(
        default=True,
        description="Track HTTP requests",
    )
    track_exceptions: bool = Field(
        default=True,
        description="Track exceptions and errors",
    )
    track_events: bool = Field(
        default=True,
        description="Track custom events",
    )
    track_metrics: bool = Field(
        default=True,
        description="Track custom metrics",
    )
    
    # Performance settings
    flush_interval_seconds: int = Field(
        default=15,
        ge=1,
        le=300,
        description="Telemetry flush interval in seconds",
        examples=[5, 15, 30]
    )
    max_batch_size: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum telemetry batch size",
        examples=[50, 100, 500]
    )
    
    @model_validator(mode='after')
    def validate_connection_config(self) -> 'AzureMonitorSettings':
        """Validate that connection string or instrumentation key is provided when enabled."""
        if self.enabled:
            if not self.connection_string and not self.instrumentation_key:
                raise ValueError(
                    "Either connection_string or instrumentation_key must be provided when enabled"
                )
        return self
    
    def get_connection_string(self) -> Optional[str]:
        """Get connection string (either direct or constructed from instrumentation key)."""
        if self.connection_string:
            return self.connection_string.get_secret_value()
        
        if self.instrumentation_key:
            key = self.instrumentation_key.get_secret_value()
            return f"InstrumentationKey={key}"
        
        return None


class AzureSettings(BaseSettings):
    """
    Unified Azure configuration for all services.
    
    This class composes all Azure service settings into a single
    configuration object for easy access and management.
    
    Attributes:
        blob: Azure Blob Storage settings
        app_service: Azure App Service settings
        static_web_app: Azure Static Web Apps settings
        monitor: Azure Application Insights settings
    """
    
    model_config = SettingsConfigDict(
        env_file=[".env", "backend/.env"],
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Service-specific settings
    blob: AzureBlobSettings = Field(default_factory=AzureBlobSettings)
    app_service: AzureAppServiceSettings = Field(default_factory=AzureAppServiceSettings)
    static_web_app: AzureStaticWebAppSettings = Field(default_factory=AzureStaticWebAppSettings)
    monitor: AzureMonitorSettings = Field(default_factory=AzureMonitorSettings)
    
    # Global Azure settings
    tenant_id: Optional[str] = Field(
        default=None,
        pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        description="Azure AD tenant ID (optional)",
    )
    
    def is_azure_environment(self) -> bool:
        """Check if running in Azure environment."""
        import os
        return any([
            os.getenv('WEBSITE_INSTANCE_ID'),  # App Service
            os.getenv('CONTAINER_APP_NAME'),  # Container Apps
            os.getenv('FUNCTIONS_WORKER_RUNTIME'),  # Functions
        ])
    
    def get_service_name(self) -> Optional[str]:
        """Get the Azure service name if running in Azure."""
        import os
        return (
            os.getenv('WEBSITE_SITE_NAME') or  # App Service
            os.getenv('CONTAINER_APP_NAME') or  # Container Apps
            os.getenv('FUNCTIONS_APP_NAME')  # Functions
        )
