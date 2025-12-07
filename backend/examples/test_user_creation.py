"""
Test script for user creation endpoint.

This script helps debug user creation issues.

Usage:
    python backend/examples/test_user_creation.py
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

def print_section(title):
    """Print section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_health():
    """Test if server is running."""
    print_section("1. Testing Server Health")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print("   Make sure the server is running:")
        print("   cd backend && uv run uvicorn backend.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_login():
    """Test admin login."""
    print_section("2. Testing Admin Login")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful")
            print(f"   Token: {data['access_token'][:50]}...")
            return data['access_token']
        elif response.status_code == 401:
            print("❌ Login failed: Invalid credentials")
            print(f"   Email: {ADMIN_EMAIL}")
            print("   Password: ********")
            print("\n   Solutions:")
            print("   1. Create admin user in Supabase Dashboard")
            print("   2. Set ADMIN_EMAIL and ADMIN_PASSWORD in .env")
            print("   3. Make sure user has 'admin' role in profiles table")
            return None
        else:
            print(f"❌ Login failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_user_creation(token):
    """Test user creation."""
    print_section("3. Testing User Creation")
    
    if not token:
        print("❌ Skipping: No admin token available")
        return False
    
    test_user = {
        "email": "testuser@example.com",
        "password": "TestPass123!",
        "full_name": "Test User",
        "is_active": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/users/",
            headers={"Authorization": f"Bearer {token}"},
            json=test_user,
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            print("✅ User created successfully")
            print(f"   ID: {data['id']}")
            print(f"   Email: {data['email']}")
            print(f"   Name: {data['full_name']}")
            print(f"   Active: {data['is_active']}")
            return True
        elif response.status_code == 403:
            print("❌ Permission denied")
            print("   The authenticated user is not an admin")
            print("\n   Solution:")
            print("   UPDATE profiles SET role = 'admin' WHERE email = 'admin@example.com';")
            return False
        elif response.status_code == 409:
            print("⚠️  User already exists")
            print(f"   Email: {test_user['email']}")
            print("\n   This is OK - user was created previously")
            return True
        elif response.status_code == 422:
            print("❌ Validation error")
            print(f"   Response: {response.json()}")
            return False
        elif response.status_code == 500:
            print("❌ Internal server error")
            print(f"   Response: {response.text}")
            print("\n   Common causes:")
            print("   1. Supabase credentials not set in .env")
            print("   2. Supabase client not initialized")
            print("   3. profiles table doesn't exist")
            return False
        elif response.status_code == 501:
            print("❌ Endpoint not implemented")
            print("   The endpoint code may not be loaded")
            print("\n   Solution:")
            print("   1. Restart the server")
            print("   2. Check backend/api/v1/endpoints/users.py")
            return False
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_supabase_config():
    """Test Supabase configuration."""
    print_section("4. Testing Supabase Configuration")
    
    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    anon_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not url:
        print("❌ SUPABASE_URL not set")
        return False
    else:
        print(f"✅ SUPABASE_URL: {url}")
    
    if not service_key:
        print("❌ SUPABASE_SERVICE_ROLE_KEY not set")
        return False
    else:
        print(f"✅ SUPABASE_SERVICE_ROLE_KEY: {service_key[:20]}...")
    
    if not anon_key:
        print("❌ SUPABASE_ANON_KEY not set")
        return False
    else:
        print(f"✅ SUPABASE_ANON_KEY: {anon_key[:20]}...")
    
    return True

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  PixCrawler User Creation Test")
    print("=" * 60)
    print(f"\nBase URL: {BASE_URL}")
    print(f"Admin Email: {ADMIN_EMAIL}")
    
    # Test 1: Server health
    if not test_health():
        print("\n❌ Server is not running. Exiting.")
        sys.exit(1)
    
    # Test 2: Supabase config
    if not test_supabase_config():
        print("\n❌ Supabase not configured. Exiting.")
        print("\nAdd to .env file:")
        print("SUPABASE_URL=https://your-project.supabase.co")
        print("SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...")
        print("SUPABASE_ANON_KEY=eyJhbGc...")
        sys.exit(1)
    
    # Test 3: Admin login
    token = test_login()
    
    # Test 4: User creation
    test_user_creation(token)
    
    print("\n" + "=" * 60)
    print("  Test Complete")
    print("=" * 60)
    
    if token:
        print("\n✅ All tests passed!")
        print("\nYou can now create users via:")
        print(f"  POST {BASE_URL}/api/v1/users/")
        print(f"  Authorization: Bearer {token[:30]}...")
    else:
        print("\n⚠️  Some tests failed. See above for details.")
        print("\nFor help, see:")
        print("  backend/docs/USER_CREATION_TROUBLESHOOTING.md")

if __name__ == "__main__":
    main()
