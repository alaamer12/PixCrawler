"""
Debug script to test user registration endpoint and identify 500 error cause.

This script tests the registration endpoint and provides detailed error information.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import httpx
from backend.core.settings import get_settings


async def test_registration():
    """Test user registration endpoint with detailed error reporting."""
    
    settings = get_settings()
    base_url = f"http://{settings.host}:{settings.port}"
    
    print("=" * 80)
    print("REGISTRATION ENDPOINT DEBUG TEST")
    print("=" * 80)
    
    # Test data
    test_user = {
        "email": "test@example.com",
        "password": "TestPass123!",
        "full_name": "Test User"
    }
    
    print(f"\n1. Testing endpoint: {base_url}/api/v1/users/")
    print(f"   Request data: {test_user}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test health endpoint first
            print("\n2. Testing health endpoint...")
            health_response = await client.get(f"{base_url}/health")
            print(f"   Health status: {health_response.status_code}")
            print(f"   Health response: {health_response.json()}")
            
            # Test registration endpoint
            print("\n3. Testing registration endpoint...")
            response = await client.post(
                f"{base_url}/api/v1/users/",
                json=test_user,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"\n   Status Code: {response.status_code}")
            print(f"   Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200 or response.status_code == 201:
                print(f"   ✅ SUCCESS: {response.json()}")
            else:
                print(f"   ❌ ERROR: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error details: {error_data}")
                except:
                    print(f"   Raw response: {response.text}")
            
    except httpx.ConnectError as e:
        print(f"\n❌ CONNECTION ERROR: Cannot connect to {base_url}")
        print(f"   Error: {e}")
        print("\n   SOLUTION: Make sure the backend server is running:")
        print(f"   cd backend && uv run uvicorn backend.main:app --reload")
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {type(e).__name__}")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("CONFIGURATION CHECK")
    print("=" * 80)
    print(f"Supabase URL: {settings.supabase.url}")
    print(f"Service Role Key: {settings.supabase.service_role_key[:20]}...")
    print(f"Anon Key: {settings.supabase.anon_key[:20]}...")
    print(f"Environment: {settings.environment}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_registration())
