"""Quick test to verify settings are loading correctly."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.core.config import get_settings

def test_settings():
    """Test that settings load correctly."""
    print("=" * 70)
    print("SETTINGS CONFIGURATION TEST")
    print("=" * 70)
    
    try:
        settings = get_settings()
        
        print("\n[Application Settings]")
        print(f"  App Name: {settings.app_name}")
        print(f"  App Version: {settings.app_version}")
        print(f"  API Prefix: {settings.api_v1_prefix}")
        print(f"  Environment: {settings.environment}")
        print(f"  Debug: {settings.debug}")
        print(f"  Host: {settings.host}")
        print(f"  Port: {settings.port}")
        print(f"  Log Level: {settings.log_level}")
        
        print("\n[Database Settings]")
        print(f"  Provider: {settings.database.provider}")
        print(f"  Connection Mode: {settings.database.connection_mode}")
        print(f"  Host: {settings.database.host}")
        print(f"  Port: {settings.database.port}")
        print(f"  User: {settings.database.user}")
        print(f"  Database: {settings.database.name}")
        print(f"  Pool Size: {settings.database.pool_size}")
        print(f"  Max Overflow: {settings.database.max_overflow}")
        print(f"  Pool Pre-Ping: {settings.database.pool_pre_ping}")
        print(f"  Echo: {settings.database.echo}")
        
        # Test URL construction
        try:
            url = settings.database.get_connection_url()
            # Mask password
            if settings.database.password:
                url_masked = url.replace(settings.database.password, "***")
            else:
                url_masked = url
            print(f"  Connection URL: {url_masked}")
        except Exception as e:
            print(f"  Connection URL: ERROR - {e}")
        
        print("\n[Supabase Settings]")
        print(f"  URL: {settings.supabase.url}")
        print(f"  Anon Key: {settings.supabase.anon_key[:20]}...")
        print(f"  Service Role Key: {settings.supabase.service_role_key[:20]}...")
        
        print("\n[Security Settings]")
        print(f"  Secret Key: {settings.security.secret_key[:20]}...")
        print(f"  Algorithm: {settings.security.algorithm}")
        print(f"  Token Expire (min): {settings.security.access_token_expire_minutes}")
        print(f"  Allowed Origins: {settings.security.allowed_origins}")
        
        print("\n[Cache Settings]")
        print(f"  Enabled: {settings.cache.enabled}")
        print(f"  Redis Host: {settings.cache.redis_host}")
        print(f"  Redis Port: {settings.cache.redis_port}")
        
        print("\n[Rate Limit Settings]")
        print(f"  Enabled: {settings.rate_limit.enabled}")
        print(f"  Redis Host: {settings.rate_limit.redis_host}")
        print(f"  Redis Port: {settings.rate_limit.redis_port}")
        
        print("\n" + "=" * 70)
        print("✅ Settings loaded successfully!")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ Settings loading failed!")
        print("=" * 70)
        print(f"\nError: {type(e).__name__}: {e}")
        print("\nPlease check your backend/.env file configuration.")
        return False


if __name__ == "__main__":
    success = test_settings()
    exit(0 if success else 1)
