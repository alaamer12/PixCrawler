"""
Get a test bearer token for API testing.

This script creates a test user in Supabase and returns a valid JWT token
for use in Postman or other API testing tools.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.core.supabase import get_supabase_client

async def get_test_token():
    """Get or create a test user and return JWT token."""
    
    supabase = get_supabase_client()
    
    # Test credentials
    test_email = "test@pixcrawler.dev"
    test_password = "TestPassword123!"
    
    print("🔐 Getting test token from Supabase...")
    print(f"   Email: {test_email}")
    
    try:
        # Try to sign in
        response = supabase.auth.sign_in_with_password({
            "email": test_email,
            "password": test_password
        })
        
        if response.session:
            token = response.session.access_token
            print(f"\n✅ Token retrieved successfully!")
            print(f"\n📋 Bearer Token:")
            print(f"{token}")
            
            # Save to file
            with open('bearer_token.txt', 'w') as f:
                f.write(token)
            print(f"\n💾 Token saved to: bearer_token.txt")
            
            return token
            
    except Exception as e:
        print(f"\n⚠️  Sign in failed: {e}")
        print(f"\n💡 Attempting to create test user...")
        
        try:
            # Try to sign up
            response = supabase.auth.sign_up({
                "email": test_email,
                "password": test_password
            })
            
            if response.session:
                token = response.session.access_token
                print(f"\n✅ Test user created and token retrieved!")
                print(f"\n📋 Bearer Token:")
                print(f"{token}")
                
                # Save to file
                with open('bearer_token.txt', 'w') as f:
                    f.write(token)
                print(f"\n💾 Token saved to: bearer_token.txt")
                
                return token
            else:
                print(f"\n❌ Failed to create test user")
                print(f"   Response: {response}")
                return None
                
        except Exception as signup_error:
            print(f"\n❌ Sign up failed: {signup_error}")
            print(f"\n💡 Note: Make sure Supabase is configured correctly in .env")
            print(f"   Required variables:")
            print(f"   - SUPABASE_URL")
            print(f"   - SUPABASE_SERVICE_ROLE_KEY")
            print(f"   - SUPABASE_ANON_KEY")
            return None

if __name__ == "__main__":
    token = asyncio.run(get_test_token())
    
    if token:
        print(f"\n🎉 Success! Use this token in Postman:")
        print(f"   1. Open Postman")
        print(f"   2. Import postman_collection_enhanced.json")
        print(f"   3. Import postman_environment.json")
        print(f"   4. Set bearerToken variable to the token above")
        print(f"   5. Start testing!")
    else:
        print(f"\n❌ Failed to get token")
        sys.exit(1)
