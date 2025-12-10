"""Database configuration settings."""

from typing import Optional
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["DatabaseSettings"]


class DatabaseSettings(BaseSettings):
    """
    PostgreSQL database configuration with Supabase support.
    
    Supports two configuration modes:
    1. Connection URL: DATABASE_URL=postgresql://user:pass@host:port/db
    2. Individual parameters: DATABASE_HOST, DATABASE_PORT, DATABASE_USER, etc.
    
    Environment variables:
        DATABASE_PROVIDER: Database provider (supabase, postgresql)
        DATABASE_CONNECTION_MODE: Connection mode (session_pooler, transaction_pooler, direct)
        DATABASE_URL: PostgreSQL connection URL (optional if using individual params)
        DATABASE_HOST: Database host
        DATABASE_PORT: Database port
        DATABASE_USER: Database user
        DATABASE_PASSWORD: Database password
        DATABASE_NAME: Database name
        DATABASE_POOL_SIZE: Connection pool size
        DATABASE_MAX_OVERFLOW: Max overflow connections
        DATABASE_POOL_PRE_PING: Enable connection health checks
        DATABASE_ECHO: Enable SQL query logging
        DATABASE_DISABLE_POOLER_WARNING: Disable pooler warnings
    """
    
    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        env_file=[".env", "backend/.env"],
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Provider and connection mode
    provider: str = Field(
        default="postgresql",
        description="Database provider (supabase, postgresql)",
        examples=["supabase", "postgresql"]
    )
    connection_mode: str = Field(
        default="direct",
        description="Connection mode (session_pooler, transaction_pooler, direct)",
        examples=["session_pooler", "transaction_pooler", "direct"]
    )
    
    # Connection URL (optional if using individual parameters)
    url: Optional[str] = Field(
        default=None,
        description="PostgreSQL database connection URL",
        examples=["postgresql://user:pass@localhost:5432/pixcrawler"]
    )
    
    # Individual connection parameters
    host: Optional[str] = Field(
        default=None,
        description="Database host",
        examples=["localhost", "aws-1-eu-west-3.pooler.supabase.com"]
    )
    port: int = Field(
        default=5432,
        ge=1,
        le=65535,
        description="Database port",
        examples=[5432, 6543]
    )
    user: Optional[str] = Field(
        default=None,
        description="Database user",
        examples=["postgres", "postgres.projectid"]
    )
    password: Optional[str] = Field(
        default=None,
        description="Database password"
    )
    name: Optional[str] = Field(
        default="postgres",
        description="Database name",
        examples=["postgres", "pixcrawler"]
    )
    
    # Connection pool settings
    pool_size: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Database connection pool size",
        examples=[5, 10, 20]
    )
    max_overflow: int = Field(
        default=5,
        ge=0,
        le=200,
        description="Database connection pool max overflow",
        examples=[5, 10, 20]
    )
    pool_pre_ping: bool = Field(
        default=True,
        description="Enable connection health checks before using from pool"
    )
    echo: bool = Field(
        default=False,
        description="Enable SQL query logging (verbose)"
    )
    disable_pooler_warning: bool = Field(
        default=True,
        description="Disable SQLAlchemy pooler warnings"
    )
    
    @model_validator(mode='after')
    def validate_connection_config(self):
        """Validate that either URL or individual parameters are provided."""
        if not self.url and not all([self.host, self.user, self.password]):
            raise ValueError(
                "Either DATABASE_URL or all of (DATABASE_HOST, DATABASE_USER, DATABASE_PASSWORD) must be provided"
            )
        return self
    
    def get_connection_url(self) -> str:
        """
        Get the database connection URL.
        
        Returns the provided URL or constructs one from individual parameters.
        
        Returns:
            PostgreSQL connection URL
        """
        if self.url:
            return self.url
        
        # Construct URL from individual parameters
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
