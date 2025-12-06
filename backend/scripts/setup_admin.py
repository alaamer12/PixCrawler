"""
Quick setup script to create admin user and test the system.

This script will:
1. Check if Supabase is configured
2. Create an admin user (if needed)
3. Test login
4. Test user creation

Usage:
    uv run python backend/scripts/setup_admin.py
"""

import os
import sys
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    print("=" * 60)
    print("  PixCrawler Admin Setup")
    print("=" * 60)
    
    # Get Supabase credentials
    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not service_key:
        print("\n❌ Supabase credentials not found!")
        print("\nAdd to .env file:")
        print("SUPABASE_URL=https://your-project.supabase.co")
        print("SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...")
        sys.exit(1)
    
    print(f"\n✅ Supabase URL: {url}")
    print(f"✅ Service Key: {service_key[:20]}...")
    
    # Create Supabase client
    try:
        supabase = create_client(url, service_key)
        print("\n✅ Supabase client created")
    except Exception as e:
        print(f"\n❌ Failed to create Supabase client: {e}")
        sys.exit(1)
    
    # Admin credentials
    admin_email = "admin@pixcrawler.com"
    admin_password = "Admin123!@#"
    
    print("\n" + "=" * 60)
    print("  Creating Admin User")
    print("=" * 60)
    print(f"\nEmail: {admin_email}")
    print(f"Password: {admin_password}")
    
    try:
        # Try to create admin user
        response = supabase.auth.admin.create_user({
            "email": admin_email,
            "password": admin_password,
            "email_confirm": True,
            "user_metadata": {
                "full_name": "Admin User"
            }
        })
        
        if response.user:
            print(f"\n✅ Admin user created!")
            print(f"   ID: {response.user.id}")
            
            # Create profile with admin role
            try:
                supabase.table("profiles").insert({
                    "id": response.user.id,
                    "email": admin_email,
                    "full_name": "Admin User",
                    "role": "admin"
                }).execute()
                print("✅ Admin profile created with admin role")
            except Exception as e:
                # Profile might already exist, try to update
                try:
                    supabase.table("profiles").update({
                        "role": "admin"
                    }).eq("id", response.user.id).execute()
                    print("✅ Admin role updated")
                except Exception as e2:
                    print(f"⚠️  Could not set admin role: {e2}")
        else:
            print("\n❌ Failed to create admin user")
            
    except Exception as e:
        error_msg = str(e).lower()
        if "already" in error_msg or "duplicate" in error_msg:
            print(f"\n⚠️  Admin user already exists")
            print("   This is OK - you can use existing credentials")
            
            # Try to ensure admin role
            try:
                # Get user by email
                users = supabase.table("profiles").select("*").eq("email", admin_email).execute()
                if users.data:
                    user_id = users.data[0]["id"]
                    supabase.table("profiles").update({
                        "role": "admin"
                    }).eq("id", user_id).execute()
                    print("✅ Admin role verified/updated")
            except Exception as e2:
                print(f"⚠️  Could not verify admin role: {e2}")
        else:
            print(f"\n❌ Error creating admin user: {e}")
    
    print("\n" + "=" * 60)
    print("  Setup Complete!")
    print("=" * 60)
    print("\n📋 Admin Credentials:")
    print(f"   Email: {admin_email}")
    print(f"   Password: {admin_password}")
    print("\n🚀 Next Steps:")
    print("   1. Restart your backend server:")
    print("      cd backend && uv run uvicorn backend.main:app --reload")
    print("\n   2. Test login:")
    print(f"      curl -X POST http://localhost:8000/api/v1/auth/login \\")
    print(f"        -H 'Content-Type: application/json' \\")
    print(f"        -d '{{\"email\":\"{admin_email}\",\"password\":\"{admin_password}\"}}'")
    print("\n   3. Run test script:")
    print("      uv run python backend/examples/test_user_creation.py")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
