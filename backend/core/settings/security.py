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

    # JWT Authentication
    secret_key: str = Field(
        default="dev-secret-key-change-in-production-min-32-characters-long",
        min_length=32,
        description="Secret key for JWT token signing (MUST be changed in production)",
        examples=["your-super-secret-key-min-32-chars"]
    )
    algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm",
        examples=["HS256", "RS256"]
    )
    access_token_expire_minutes: int = Field(
        default=30,
        ge=1,
        le=43200,  # Max 30 days
        description="JWT access token expiration time in minutes",
        examples=[30, 60, 1440]
    )

    # CORS Configuration
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
        """Validate CORS origins format_."""
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
