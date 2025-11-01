"""File storage configuration settings."""

from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["StorageSettings"]


class StorageSettings(BaseSettings):
    """
    File upload and storage configuration.
    
    Environment variables:
        STORAGE_UPLOAD_MAX_SIZE: Max upload size in bytes
        STORAGE_UPLOAD_ALLOWED_EXTENSIONS: Comma-separated extensions
    """
    
    model_config = SettingsConfigDict(
        env_prefix="STORAGE_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    upload_max_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        ge=1024,  # 1KB minimum
        le=100 * 1024 * 1024,  # 100MB maximum
        description="Maximum upload file size in bytes",
        examples=[1048576, 10485760, 52428800]  # 1MB, 10MB, 50MB
    )
    upload_allowed_extensions: List[str] = Field(
        default=[".jpg", ".jpeg", ".png", ".gif", ".webp"],
        min_length=1,
        description="Allowed file extensions for uploads",
        examples=[[".jpg", ".png"], [".jpg", ".jpeg", ".png", ".gif", ".webp"]]
    )
    
    @field_validator('upload_allowed_extensions')
    @classmethod
    def validate_extensions(cls, v: List[str]) -> List[str]:
        """Validate file extensions format."""
        validated = []
        for ext in v:
            ext = ext.strip().lower()
            if not ext.startswith('.'):
                raise ValueError(f"Extension '{ext}' must start with a dot")
            if len(ext) < 2:
                raise ValueError(f"Extension '{ext}' is too short")
            validated.append(ext)
        return validated
