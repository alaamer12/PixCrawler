"""
Configuration checker script for PixCrawler backend.

This script checks if all required environment variables are properly configured
and provides guidance on what needs to be fixed.
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir.parent))

def check_env_var(name: str, example_value: str = None) -> tuple[bool, str]:
    """Check if an environment variable is set and not a placeholder."""
    value = os.getenv(name)
    
    if not value:
        return False, f"❌ {name}: NOT SET"
    
    # Check for common placeholder patterns
    placeholders = ["test", "your-", "YOUR_", "xxx", "example", "placeholder"]
    if any(placeholder in value for placeholder in placeholders):
        return False, f"⚠️  {name}: PLACEHOLDER VALUE (needs real credentials)"
    
    return True, f"✅ {name}: Configured"


def main():
    """Check all required environment variables."""
    print("=" * 70)
    print("PixCrawler Backend Configuration Checker")
    print("=" * 70)
    print()
    
    # Load .env file if it exists
    env_file = backend_dir / ".env"
    if env_file.exists():
        print(f"📄 Found .env file: {env_file}")
        print()
        
        # Simple .env parser
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value
    else:
        print(f"⚠️  No .env file found at: {env_file}")
        print("   Copy .env.example to .env and configure it")
        print()
    
    # Check critical environment variables
    checks = []
    
    print("🔍 Checking Supabase Configuration:")
    print("-" * 70)
    checks.append(check_env_var("SUPABASE_URL"))
    checks.append(check_env_var("SUPABASE_SERVICE_ROLE_KEY"))
    checks.append(check_env_var("SUPABASE_ANON_KEY"))
    
    for status, message in checks[-3:]:
        print(f"  {message}")
    print()
    
    print("🔍 Checking Database Configuration:")
    print("-" * 70)
    checks.append(check_env_var("DATABASE_URL"))
    print(f"  {checks[-1][1]}")
    print()
    
    print("🔍 Checking Redis Configuration (Optional for development):")
    print("-" * 70)
    checks.append(check_env_var("REDIS_URL"))
    checks.append(check_env_var("CELERY_BROKER_URL"))
    
    for status, message in checks[-2:]:
        print(f"  {message}")
    print()
    
    # Summary
    print("=" * 70)
    print("Summary:")
    print("=" * 70)
    
    all_passed = all(status for status, _ in checks[:4])  # Only check critical ones
    
    if all_passed:
        print("✅ All critical configuration checks passed!")
        print()
        print("Next steps:")
        print("  1. Start the backend server:")
        print("     .venv\\Scripts\\python.exe -m uvicorn backend.main:app --reload")
        print()
        print("  2. Test registration:")
        print("     .venv\\Scripts\\python.exe backend\\scripts\\quick_test.py")
        print()
    else:
        print("❌ Configuration issues found!")
        print()
        print("To fix:")
        print("  1. Go to https://supabase.com/dashboard")
        print("  2. Select your project")
        print("  3. Go to Project Settings > API")
        print("  4. Copy the following to backend/.env:")
        print("     - Project URL → SUPABASE_URL")
        print("     - service_role key → SUPABASE_SERVICE_ROLE_KEY")
        print("     - anon public key → SUPABASE_ANON_KEY")
        print()
        print("  5. Go to Project Settings > Database")
        print("  6. Copy Connection string (URI) → DATABASE_URL")
        print("     (Change postgresql:// to postgresql+asyncpg://)")
        print()
    
    print("=" * 70)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
