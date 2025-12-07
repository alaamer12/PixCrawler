"""
Promote a user to admin/superuser role.

This script promotes an existing user to admin role in the profiles table.

Usage:
    python backend/scripts/promote_to_admin.py <email>
    
Example:
    python backend/scripts/promote_to_admin.py ganna@gmail.com
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir.parent))

from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
env_file = backend_dir / ".env"
load_dotenv(env_file)


def promote_user_to_admin(email: str):
    """Promote a user to admin role."""
    print("=" * 70)
    print("  PixCrawler - Promote User to Admin")
    print("=" * 70)
    print()
    
    # Get Supabase credentials
    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not service_key:
        print("❌ ERROR: Supabase credentials not found!")
        print()
        print("Make sure backend/.env has:")
        print("  SUPABASE_URL=https://your-project.supabase.co")
        print("  SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...")
        print()
        return False
    
    # Check for test/placeholder values
    if "test-project" in url or "test_service" in service_key:
        print("❌ ERROR: Supabase credentials are test/placeholder values!")
        print()
        print("Please update backend/.env with real Supabase credentials.")
        print("See COMPLETE_FIX_GUIDE.md for instructions.")
        print()
        return False
    
    print(f"📧 Email to promote: {email}")
    print(f"🔗 Supabase URL: {url}")
    print()
    
    # Create Supabase client
    try:
        supabase = create_client(url, service_key)
        print("✅ Connected to Supabase")
        print()
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        print()
        return False
    
    # Find user in profiles table
    try:
        print(f"🔍 Looking for user: {email}")
        response = supabase.table("profiles").select("*").eq("email", email).execute()
        
        if not response.data:
            print(f"❌ User not found: {email}")
            print()
            print("Make sure the user is registered first:")
            print(f"  1. Register via API: POST /api/v1/users/")
            print(f"  2. Or use Supabase dashboard to create user")
            print()
            return False
        
        user = response.data[0]
        user_id = user["id"]
        current_role = user.get("role", "user")
        
        print(f"✅ User found!")
        print(f"   ID: {user_id}")
        print(f"   Email: {user['email']}")
        print(f"   Name: {user.get('full_name', 'N/A')}")
        print(f"   Current Role: {current_role}")
        print()
        
        if current_role == "admin":
            print("ℹ️  User is already an admin!")
            print()
            return True
        
        # Promote to admin
        print("🔄 Promoting user to admin...")
        update_response = supabase.table("profiles").update({
            "role": "admin"
        }).eq("id", user_id).execute()
        
        if update_response.data:
            print("✅ SUCCESS! User promoted to admin!")
            print()
            print("=" * 70)
            print("  Admin User Details")
            print("=" * 70)
            print(f"  Email: {email}")
            print(f"  Role: admin")
            print(f"  User ID: {user_id}")
            print()
            print("🎉 The user now has admin privileges!")
            print()
            print("Admin capabilities:")
            print("  ✓ List all users (GET /api/v1/users)")
            print("  ✓ View any user (GET /api/v1/users/{id})")
            print("  ✓ Update any user (PATCH /api/v1/users/{id})")
            print("  ✓ Delete any user (DELETE /api/v1/users/{id})")
            print("  ✓ Access admin dashboard")
            print()
            print("=" * 70)
            return True
        else:
            print("❌ Failed to update user role")
            print()
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        return False


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python backend/scripts/promote_to_admin.py <email>")
        print()
        print("Example:")
        print("  python backend/scripts/promote_to_admin.py ganna@gmail.com")
        print()
        sys.exit(1)
    
    email = sys.argv[1]
    success = promote_user_to_admin(email)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
