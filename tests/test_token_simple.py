#!/usr/bin/env python3
"""
Test token generation without authentication.
"""

import requests

BASE_URL = "http://127.0.0.1:8000"

def test_token_generation():
    """Test token generation endpoint without auth."""
    
    print("🔑 Testing Token Generation (No Auth)")
    print("=" * 40)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/tokens/generate",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            data = response.json()
            token = data.get('token')
            
            print(f"✅ Token generated successfully!")
            print(f"Token: {token}")
            print(f"Type: {data.get('token_type')}")
            print(f"Expires: {data.get('expires_at')}")
            
            # Verify token format
            if token and token.startswith('pk_live_'):
                print(f"✅ Token format is correct")
                return True
            else:
                print(f"❌ Token format is incorrect")
                return False
        else:
            print(f"❌ Failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_token_generation()