"""Supabase configuration settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["SupabaseSettings"]


class SupabaseSettings(BaseSettings):
    """
    Supabase connection configuration.
    
    Environment variables:
        SUPABASE_URL: Supabase project URL
        SUPABASE_SERVICE_ROLE_KEY: Service role key (backend)
        SUPABASE_ANON_KEY: Anonymous key (frontend)
    """
    
    model_config = SettingsConfigDict(
        env_prefix="SUPABASE_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    url: str = Field(
        ...,
        min_length=1,
        pattern=r'^https://[a-zA-Z0-9-]+\.supabase\.co$',
        description="Supabase project URL",
        examples=["https://your-project.supabase.co"]
    )
    service_role_key: str = Field(
        ...,
        min_length=50,
        description="Supabase service role key"
    )
    anon_key: str = Field(
        ...,
        min_length=50,
        description="Supabase anonymous key"
    )
