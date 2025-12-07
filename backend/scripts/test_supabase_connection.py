"""
Test Supabase connection to diagnose DNS/connection issues.

This script tests the Supabase connection and provides detailed diagnostics.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir.parent))

import socket
import requests
from urllib.parse import urlparse


def test_dns_resolution(url: str) -> bool:
    """Test if the hostname can be resolved."""
    try:
        parsed = urlparse(url)
        hostname = parsed.netloc
        print(f"🔍 Testing DNS resolution for: {hostname}")
        
        ip_address = socket.gethostbyname(hostname)
        print(f"✅ DNS Resolution successful: {hostname} -> {ip_address}")
        return True
    except socket.gaierror as e:
        print(f"❌ DNS Resolution failed: {e}")
        print(f"   Error code: {e.errno}")
        print(f"   Error message: {e.strerror}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during DNS resolution: {e}")
        return False


def test_http_connection(url: str) -> bool:
    """Test if we can make an HTTP connection."""
    try:
        print(f"\n🔍 Testing HTTP connection to: {url}")
        response = requests.get(f"{url}/rest/v1/", timeout=10)
        print(f"✅ HTTP Connection successful: Status {response.status_code}")
        return True
    except requests.exceptions.ConnectionError as e:
        print(f"❌ HTTP Connection failed: {e}")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ HTTP Connection timeout")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during HTTP connection: {e}")
        return False


def main():
    """Main test function."""
    print("=" * 60)
    print("Supabase Connection Diagnostics")
    print("=" * 60)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    supabase_url = os.getenv("SUPABASE_URL")
    
    if not supabase_url:
        print("❌ SUPABASE_URL not found in environment variables")
        print("\nPlease set SUPABASE_URL in your .env file:")
        print("  SUPABASE_URL=https://your-project.supabase.co")
        return False
    
    print(f"\n📋 Configuration:")
    print(f"   SUPABASE_URL: {supabase_url}")
    
    # Test DNS resolution
    print("\n" + "=" * 60)
    dns_ok = test_dns_resolution(supabase_url)
    
    if not dns_ok:
        print("\n" + "=" * 60)
        print("❌ DIAGNOSIS: DNS Resolution Failed")
        print("=" * 60)
        print("\nPossible causes:")
        print("1. The Supabase project URL is incorrect")
        print("2. The Supabase project has been deleted or suspended")
        print("3. Network/firewall is blocking DNS queries")
        print("4. You're offline or have network connectivity issues")
        print("\nSolutions:")
        print("1. Verify your Supabase project URL at https://app.supabase.com")
        print("2. Check if the project exists and is active")
        print("3. Try accessing the URL in your browser")
        print("4. Check your internet connection")
        return False
    
    # Test HTTP connection
    print("\n" + "=" * 60)
    http_ok = test_http_connection(supabase_url)
    
    if not http_ok:
        print("\n" + "=" * 60)
        print("❌ DIAGNOSIS: HTTP Connection Failed")
        print("=" * 60)
        print("\nDNS works but HTTP connection failed.")
        print("Possible causes:")
        print("1. Firewall blocking HTTPS connections")
        print("2. Supabase service is down")
        print("3. Invalid SSL certificate")
        return False
    
    # All tests passed
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
    print("\nYour Supabase connection is working correctly!")
    print("If you're still getting errors, the issue might be:")
    print("1. Invalid Supabase credentials (service role key)")
    print("2. Database connection issues")
    print("3. Application-level configuration problems")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
