"""
Quick script to promote ganna@gmail.com to admin.

This script will:
1. Check if user exists
2. Promote to admin role
3. Verify the promotion

Usage:
    python backend/scripts/promote_ganna.py
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

# User to promote
USER_EMAIL = "ganna@gmail.com"
USER_NAME = "Ganna Mansour"


def main():
    """Promote Ganna to admin."""
    print("=" * 70)
    print("  Promoting Ganna Mansour to Admin")
    print("=" * 70)
    print()
    
    # Get Supabase credentials
    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not service_key:
        print("❌ ERROR: Supabase credentials not configured!")
        print()
        print("Please update backend/.env with real Supabase credentials.")
        print("See COMPLETE_FIX_GUIDE.md for instructions.")
        print()
        sys.exit(1)
    
    # Check for test values
    if "test-project" in url or "test_service" in service_key:
        print("❌ ERROR: Supabase credentials are test/placeholder values!")
        print()
        print("You need to:")
        print("  1. Go to https://supabase.com/dashboard")
        print("  2. Get your real project credentials")
        print("  3. Update backend/.env")
        print("  4. Run this script again")
        print()
        sys.exit(1)
    
    print(f"📧 User: {USER_EMAIL}")
    print(f"👤 Name: {USER_NAME}")
    print(f"🔗 Supabase: {url}")
    print()
    
    # Create Supabase client
    try:
        supabase = create_client(url, service_key)
        print("✅ Connected to Supabase")
        print()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print()
        sys.exit(1)
    
    # Check if user exists
    try:
        print("🔍 Checking if user exists...")
        response = supabase.table("profiles").select("*").eq("email", USER_EMAIL).execute()
        
        if not response.data:
            print(f"❌ User not found: {USER_EMAIL}")
            print()
            print("The user needs to be registered first!")
            print()
            print("Option 1: Register via API")
            print("  curl -X POST http://localhost:8000/api/v1/users/ \\")
            print("    -H 'Content-Type: application/json' \\")
            print(f"    -d '{{\"email\":\"{USER_EMAIL}\",\"password\":\"Ganna@12345\",\"full_name\":\"{USER_NAME}\"}}'")
            print()
            print("Option 2: Register via Supabase Dashboard")
            print("  1. Go to https://supabase.com/dashboard")
            print("  2. Select your project")
            print("  3. Go to Authentication > Users")
            print("  4. Click 'Add user'")
            print()
            sys.exit(1)
        
        user = response.data[0]
        user_id = user["id"]
        current_role = user.get("role", "user")
        
        print(f"✅ User found!")
        print(f"   ID: {user_id}")
        print(f"   Current Role: {current_role}")
        print()
        
        if current_role == "admin":
            print("✅ User is already an admin!")
            print()
            print("=" * 70)
            print("  Admin Access Confirmed")
            print("=" * 70)
            print(f"  Email: {USER_EMAIL}")
            print(f"  Role: admin")
            print()
            print("Admin capabilities:")
            print("  ✓ List all users")
            print("  ✓ Manage any user account")
            print("  ✓ Access admin dashboard")
            print("  ✓ View system metrics")
            print()
            sys.exit(0)
        
        # Promote to admin
        print("🔄 Promoting to admin role...")
        update_response = supabase.table("profiles").update({
            "role": "admin"
        }).eq("id", user_id).execute()
        
        if update_response.data:
            print("✅ SUCCESS! User promoted to admin!")
            print()
            print("=" * 70)
            print("  🎉 Admin Promotion Complete!")
            print("=" * 70)
            print(f"  Email: {USER_EMAIL}")
            print(f"  Name: {USER_NAME}")
            print(f"  Role: admin → SUPERUSER")
            print()
            print("Admin Privileges Granted:")
            print("  ✓ Full user management access")
            print("  ✓ System administration")
            print("  ✓ Dashboard access")
            print("  ✓ Metrics and monitoring")
            print()
            print("Next Steps:")
            print("  1. Login with admin credentials")
            print("  2. Access admin endpoints")
            print("  3. Manage users and system")
            print()
            print("=" * 70)
        else:
            print("❌ Failed to promote user")
            print()
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
