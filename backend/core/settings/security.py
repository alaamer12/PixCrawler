"""Security and CORS configuration settings."""

from typing import Any, List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["SecuritySettings"]


class SecuritySettings(BaseSettings):
    """
    Security, CORS, and host configuration.
    
    Environment variables:
        SECURITY_ALLOWED_ORIGINS: Comma-separated CORS origins
        SECURITY_ALLOWED_HOSTS: Comma-separated allowed hosts
        SECURITY_FORCE_HTTPS: Force HTTPS redirect
    """
    
    model_config = SettingsConfigDict(
        env_prefix="SECURITY_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000"],
        min_length=1,
        description="Allowed CORS origins",
        examples=[["http://localhost:3000"], ["https://app.example.com", "https://admin.example.com"]]
    )
    allowed_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        min_length=1,
        description="Allowed host headers (production)",
        examples=[["localhost"], ["app.example.com", "www.app.example.com"]]
    )
    force_https: bool = Field(
        default=False,
        description="Force HTTPS redirect in production",
        examples=[True, False]
    )
    
    @field_validator('allowed_origins', mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator('allowed_origins')
    @classmethod
    def validate_origins(cls, v: List[str]) -> List[str]:
        """Validate CORS origins format."""
        validated = []
        for origin in v:
            origin = origin.strip()
            if not origin:
                continue
            if not (origin.startswith('http://') or origin.startswith('https://')):
                raise ValueError(f"Origin '{origin}' must start with http:// or https://")
            validated.append(origin)
        
        if not validated:
            raise ValueError("At least one valid origin is required")
        return validated
