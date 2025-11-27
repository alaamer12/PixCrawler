from typing import Optional
from supabase import Client, create_client
from backend.core.config import get_settings

_supabase_client: Optional[Client] = None

def get_supabase_client() -> Optional[Client]:
    """
    Get or create a Supabase client instance.
    """
    global _supabase_client
    
    if _supabase_client is None:
        try:
            settings = get_settings()
            if settings.supabase_url and settings.supabase_service_role_key:
                _supabase_client = create_client(
                    settings.supabase_url,
                    settings.supabase_service_role_key
                )
        except Exception:
            # Return None if configuration is missing or invalid
            return None
            
    return _supabase_client
