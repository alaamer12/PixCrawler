#!/usr/bin/env python3
"""
Test the token generation endpoint.
"""

import requests

BASE_URL = "http://127.0.0.1:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6IlVpZkx5YzF4d3FQMnBSaTUiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3lmZGFkcGdzeHVkZm96Z2RlZmdzLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiIyY2RkNTE3OC0yNmM2LTQ5ZTAtODdhYi03MjZiZTQ1ZTNmNWEiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzY1NDY1NDI2LCJpYXQiOjE3NjU0NjE4MjYsImVtYWlsIjoidXNlckBleGFtcGxlLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWwiOiJ1c2VyQGV4YW1wbGUuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZ1bGxfbmFtZSI6IkpvaG4gRG9lIiwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJzdWIiOiIyY2RkNTE3OC0yNmM2LTQ5ZTAtODdhYi03MjZiZTQ1ZTNmNWEifSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc2NTQ2MTgyNn0sInNlc3Npb25faWQiOiJkZDQ0NDcyMC01MTQ3LTQ2MDQtYWE3NS1hOTQ1MmNkZGU5NWYiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.v_KAI6T826_7EUbkbHmJF2nzDto4dkYIgdWBXZUSoxU"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def test_token_generation():
    """Test token generation endpoint."""
    
    print("🔑 Testing Token Generation")
    print("=" * 40)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/tokens/generate",
            headers=headers,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            token = data.get('token')
            
            print(f"✅ Token generated successfully!")
            print(f"Token: {token}")
            print(f"Type: {data.get('token_type')}")
            print(f"Expires: {data.get('expires_at')}")
            
            # Verify token format
            if token.startswith('pk_live_'):
                print(f"✅ Token format is correct")
            else:
                print(f"❌ Token format is incorrect")
                
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_get_current_token():
    """Test get current token endpoint."""
    
    print(f"\n🔍 Testing Get Current Token")
    print("=" * 40)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/tokens/current",
            headers=headers,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            
            print(f"✅ Current token retrieved!")
            print(f"Token: {token}")
            
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run token tests."""
    
    print("🧪 Testing Token Generation System")
    print("=" * 50)
    
    # Test token generation
    generate_success = test_token_generation()
    
    # Test get current token
    current_success = test_get_current_token()
    
    print(f"\n🎉 Test Results:")
    print(f"   Generate Token: {'✅' if generate_success else '❌'}")
    print(f"   Get Current Token: {'✅' if current_success else '❌'}")
    
    if generate_success and current_success:
        print(f"   ✅ SUCCESS! Token system is working!")
    else:
        print(f"   ❌ Token system needs debugging")

if __name__ == "__main__":
    main()