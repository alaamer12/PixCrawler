"""
Quick test to verify the 500 error fix.

Run this after restarting the backend server.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 80)
print("QUICK REGISTRATION TEST")
print("=" * 80)

# Test data
test_user = {
    "email": "quicktest@example.com",
    "password": "TestPass123!",
    "full_name": "Quick Test User"
}

print(f"\n1. Testing: POST {BASE_URL}/api/v1/users/")
print(f"   Data: {json.dumps(test_user, indent=2)}")

try:
    response = requests.post(
        f"{BASE_URL}/api/v1/users/",
        json=test_user,
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    
    print(f"\n2. Response Status: {response.status_code}")
    
    if response.status_code in [200, 201]:
        print("   ✅ SUCCESS! Registration works!")
        print(f"\n   Response:")
        print(json.dumps(response.json(), indent=2))
        
    elif response.status_code == 409:
        print("   ⚠️  Email already registered (this is OK)")
        print("   Try with a different email or delete the existing user")
        
    elif response.status_code == 500:
        print("   ❌ STILL GETTING 500 ERROR")
        print("\n   Possible causes:")
        print("   1. Server not restarted after fix")
        print("   2. Supabase credentials not configured")
        print("   3. Supabase project not active")
        print(f"\n   Error details:")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)
            
    else:
        print(f"   ❌ Unexpected status code: {response.status_code}")
        print(f"\n   Response:")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)
            
except requests.exceptions.ConnectionError:
    print("\n❌ CONNECTION ERROR")
    print("   Backend server is not running!")
    print("\n   Start the server:")
    print("   cd backend")
    print("   uv run uvicorn backend.main:app --reload")
    
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}")
    print(f"   {e}")

print("\n" + "=" * 80)
