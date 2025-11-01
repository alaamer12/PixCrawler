"""
Resource management settings for PixCrawler.

This module provides Pydantic Settings for managing resource limits
and orchestration configuration across different environments.

Classes:
    ResourceSettings: Configuration for resource limits and chunk orchestration

Functions:
    get_resource_settings: Get cached resource settings instance

Features:
    - Configuration-based resource management (no psutil dependency)
    - Environment-specific limits (local, Azure, AWS)
    - Chunk size and concurrency configuration
    - Safe defaults with validation
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = [
    'ResourceSettings',
    'get_resource_settings',
]


class ResourceSettings(BaseSettings):
    """
    Resource management settings for chunk orchestration.
    
    Provides configuration-based resource limits that work across
    all environments without relying on psutil or runtime metrics.
    
    Environment Detection:
        - local: Development environment
        - azure: Azure App Service / Azure Functions
        - aws: AWS Lambda / ECS
    
    Attributes:
        environment: Deployment environment
        max_concurrent_chunks: Maximum concurrent processing chunks
        max_temp_storage_mb: Maximum temp storage in MB
        chunk_size_images: Images per processing chunk
        estimated_image_size_mb: Estimated average image size
        enable_auto_scaling: Enable dynamic chunk allocation
    """
    
    model_config = SettingsConfigDict(
        env_prefix="PIXCRAWLER_RESOURCE_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
        str_strip_whitespace=True,
    )
    
    # Environment Detection
    environment: Literal["local", "azure", "aws"] = Field(
        default="local",
        description="Deployment environment",
        examples=["local", "azure", "aws"],
    )
    
    # Chunk Processing Limits
    max_concurrent_chunks: int = Field(
        default=35,
        ge=1,
        le=100,
        description="Maximum concurrent chunks to process",
        examples=[10, 35, 50],
    )
    
    # Storage Limits (MB)
    max_temp_storage_mb: int = Field(
        default=20000,  # 20GB for local development
        ge=100,
        le=100000,
        description="Maximum temp storage in MB",
        examples=[400, 8000, 20000],
    )
    
    # Chunk Configuration
    chunk_size_images: int = Field(
        default=500,
        ge=100,
        le=10000,
        description="Number of images per processing chunk",
        examples=[500, 1000, 2000],
    )
    
    estimated_image_size_mb: float = Field(
        default=0.5,  # 500KB average
        ge=0.1,
        le=10.0,
        description="Estimated average image size in MB",
        examples=[0.5, 1.0, 2.0],
    )
    
    # Auto-scaling
    enable_auto_scaling: bool = Field(
        default=True,
        description="Enable dynamic chunk allocation based on load",
    )
    
    # Safety Margins
    storage_safety_margin: float = Field(
        default=0.2,  # 20% safety margin
        ge=0.0,
        le=0.5,
        description="Storage safety margin (0.2 = 20%)",
        examples=[0.1, 0.2, 0.3],
    )
    
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        valid_envs = {"local", "azure", "aws"}
        if v not in valid_envs:
            raise ValueError(f"Environment must be one of {valid_envs}")
        return v
    
    @computed_field
    @property
    def max_chunks_by_storage(self) -> int:
        """
        Calculate maximum chunks based on storage capacity.
        
        Formula: (max_storage * (1 - safety_margin)) / (chunk_size * image_size)
        
        Returns:
            Maximum number of chunks that fit in storage
        """
        available_storage = self.max_temp_storage_mb * (1 - self.storage_safety_margin)
        chunk_storage_mb = self.chunk_size_images * self.estimated_image_size_mb
        return int(available_storage / chunk_storage_mb)
    
    @computed_field
    @property
    def effective_max_chunks(self) -> int:
        """
        Get effective maximum chunks (smaller of config and storage limits).
        
        Returns:
            Effective maximum concurrent chunks
        """
        return min(self.max_concurrent_chunks, self.max_chunks_by_storage)
    
    @computed_field
    @property
    def chunk_storage_mb(self) -> float:
        """
        Calculate storage required per chunk.
        
        Returns:
            Storage in MB required for one chunk
        """
        return self.chunk_size_images * self.estimated_image_size_mb
    
    def get_environment_config(self) -> dict:
        """
        Get environment-specific configuration summary.
        
        Returns:
            Dictionary with environment configuration
        """
        return {
            "environment": self.environment,
            "max_concurrent_chunks": self.max_concurrent_chunks,
            "effective_max_chunks": self.effective_max_chunks,
            "max_temp_storage_mb": self.max_temp_storage_mb,
            "chunk_size_images": self.chunk_size_images,
            "chunk_storage_mb": self.chunk_storage_mb,
            "storage_safety_margin": f"{self.storage_safety_margin * 100}%",
        }


@lru_cache()
def get_resource_settings() -> ResourceSettings:
    """
    Get cached resource settings instance.
    
    Returns:
        ResourceSettings instance
    
    Example:
        >>> settings = get_resource_settings()
        >>> print(settings.effective_max_chunks)
        35
    """
    return ResourceSettings()
