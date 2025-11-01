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
        default="https://development.supabase.co",
        min_length=1,
        pattern=r'^https://[a-zA-Z0-9-]+\.supabase\.co$',
        description="Supabase project URL",
        examples=["https://your-project.supabase.co"]
    )
    service_role_key: str = Field(
        default="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRldmVsb3BtZW50Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTY0NTE5MjgwMCwiZXhwIjoxOTYwNzY4ODAwfQ.dev_placeholder_key_for_local_development_only",
        min_length=50,
        description="Supabase service role key (use real key in production)"
    )
    anon_key: str = Field(
        default="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRldmVsb3BtZW50Iiwicm9sZSI6ImFub24iLCJpYXQiOjE2NDUxOTI4MDAsImV4cCI6MTk2MDc2ODgwMH0.dev_placeholder_key_for_local_development_only",
        min_length=50,
        description="Supabase anonymous key (use real key in production)"
    )
