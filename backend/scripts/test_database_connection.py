"""
Test PostgreSQL database connection to diagnose connection issues.

This script tests the database connection and provides detailed diagnostics.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir.parent))

import socket
from urllib.parse import urlparse


def test_database_dns(database_url: str) -> bool:
    """Test if the database hostname can be resolved."""
    try:
        parsed = urlparse(database_url)
        hostname = parsed.hostname
        port = parsed.port or 5432
        
        print(f"🔍 Testing DNS resolution for database: {hostname}")
        
        ip_address = socket.gethostbyname(hostname)
        print(f"✅ DNS Resolution successful: {hostname} -> {ip_address}")
        
        # Test if port is reachable
        print(f"\n🔍 Testing TCP connection to: {hostname}:{port}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((hostname, port))
        sock.close()
        
        if result == 0:
            print(f"✅ TCP Connection successful: Port {port} is open")
            return True
        else:
            print(f"❌ TCP Connection failed: Port {port} is closed or unreachable")
            return False
            
    except socket.gaierror as e:
        print(f"❌ DNS Resolution failed: {e}")
        print(f"   Error code: {e.errno}")
        print(f"   Error message: {e.strerror}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_database_connection(database_url: str) -> bool:
    """Test actual database connection using asyncpg."""
    try:
        import asyncio
        import asyncpg
        
        print(f"\n🔍 Testing PostgreSQL connection...")
        
        async def connect():
            try:
                conn = await asyncpg.connect(database_url, timeout=10)
                version = await conn.fetchval('SELECT version()')
                await conn.close()
                print(f"✅ Database connection successful!")
                print(f"   PostgreSQL version: {version.split(',')[0]}")
                return True
            except asyncpg.InvalidPasswordError:
                print(f"❌ Database connection failed: Invalid password")
                return False
            except asyncpg.InvalidCatalogNameError:
                print(f"❌ Database connection failed: Database does not exist")
                return False
            except Exception as e:
                print(f"❌ Database connection failed: {e}")
                return False
        
        return asyncio.run(connect())
        
    except ImportError:
        print("⚠️  asyncpg not installed, skipping database connection test")
        return None
    except Exception as e:
        print(f"❌ Unexpected error during database connection: {e}")
        return False


def main():
    """Main test function."""
    print("=" * 60)
    print("PostgreSQL Database Connection Diagnostics")
    print("=" * 60)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        print("\nPlease set DATABASE_URL in your .env file:")
        print("  DATABASE_URL=postgresql://user:pass@host:5432/database")
        return False
    
    # Parse and display (hide password)
    parsed = urlparse(database_url)
    safe_url = f"{parsed.scheme}://{parsed.username}:***@{parsed.hostname}:{parsed.port or 5432}{parsed.path}"
    
    print(f"\n📋 Configuration:")
    print(f"   DATABASE_URL: {safe_url}")
    print(f"   Hostname: {parsed.hostname}")
    print(f"   Port: {parsed.port or 5432}")
    print(f"   Database: {parsed.path.lstrip('/')}")
    print(f"   Username: {parsed.username}")
    
    # Test DNS and TCP connection
    print("\n" + "=" * 60)
    dns_ok = test_database_dns(database_url)
    
    if not dns_ok:
        print("\n" + "=" * 60)
        print("❌ DIAGNOSIS: Database Connection Failed")
        print("=" * 60)
        print("\nPossible causes:")
        print("1. The database hostname is incorrect")
        print("2. The database server is down or unreachable")
        print("3. Firewall blocking PostgreSQL port (5432)")
        print("4. Network connectivity issues")
        print("\nSolutions:")
        print("1. Verify your DATABASE_URL in Supabase Dashboard:")
        print("   Project Settings > Database > Connection String")
        print("2. Make sure you're using the correct connection pooler URL")
        print("3. Check if your IP is allowed in Supabase network restrictions")
        return False
    
    # Test actual database connection
    print("\n" + "=" * 60)
    db_ok = test_database_connection(database_url)
    
    if db_ok is None:
        print("\n⚠️  Could not test database connection (asyncpg not installed)")
        print("   But DNS and TCP connection are working!")
    elif not db_ok:
        print("\n" + "=" * 60)
        print("❌ DIAGNOSIS: Database Authentication Failed")
        print("=" * 60)
        print("\nDNS and TCP work but authentication failed.")
        print("Possible causes:")
        print("1. Invalid database password")
        print("2. Database user doesn't exist")
        print("3. Database doesn't exist")
        print("4. Insufficient permissions")
        print("\nSolutions:")
        print("1. Get the correct connection string from Supabase:")
        print("   Project Settings > Database > Connection String")
        print("2. Make sure you're using the 'postgres' user")
        print("3. Reset your database password if needed")
        return False
    else:
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nYour database connection is working correctly!")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
