"""Supabase client initialization and management."""

from functools import lru_cache
from typing import Optional

from supabase import Client, create_client

from backend.core.config import get_settings
from utility.logging_config import get_logger

logger = get_logger(__name__)

_supabase_client: Optional[Client] = None


@lru_cache()
def get_supabase_client() -> Optional[Client]:
    """
    Get or create a Supabase client instance.
    
    This function creates a singleton Supabase client using the service role key
    for backend operations that bypass Row Level Security (RLS).
    
    Returns:
        Supabase Client instance or None if initialization fails
    """
    global _supabase_client
    
    if _supabase_client is not None:
        return _supabase_client
    
    try:
        settings = get_settings()
        _supabase_client = create_client(
            settings.supabase.url,
            settings.supabase.service_role_key
        )
        logger.info(f"✅ Supabase client initialized for {settings.supabase.url}")
        return _supabase_client
    except Exception as e:
        logger.error(f"❌ Failed to initialize Supabase client: {e}")
        return None


def close_supabase_client() -> None:
    """Close the Supabase client connection."""
    global _supabase_client
    if _supabase_client is not None:
        # Supabase client doesn't have an explicit close method
        # but we can clear the reference
        _supabase_client = None
        logger.info("Supabase client connection closed")
