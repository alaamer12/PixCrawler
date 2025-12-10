"""Test Supabase database connection.

NOTE: This is a manual integration test for Supabase connection.
It is skipped in automated test runs to avoid external dependencies.
Run manually with: python tests/test_supabase_connection.py
"""

import asyncio
import os
import socket
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Get project root and change to it
project_root = Path(__file__).parent.parent
os.chdir(project_root)
sys.path.insert(0, str(project_root))

from backend.core.config import get_settings
from backend.database.connection import get_engine


def check_dns_resolution(hostname: str) -> dict:
    """Check DNS resolution for a hostname."""
    try:
        # Try to resolve the hostname
        addr_info = socket.getaddrinfo(hostname, None)
        ipv4_addresses = [info[4][0] for info in addr_info if info[0] == socket.AF_INET]
        ipv6_addresses = [info[4][0] for info in addr_info if info[0] == socket.AF_INET6]

        return {"success": True, "ipv4": ipv4_addresses, "ipv6": ipv6_addresses, "all": addr_info}
    except socket.gaierror as e:
        return {"success": False, "error": str(e)}


async def test_connection():
    """Test Supabase connection using current settings."""
    settings = get_settings()

    print(f"Testing connection to: {settings.database.provider}")
    print(f"Host: {settings.database.host}")
    print(f"Database: {settings.database.name}")
    print(f"User: {settings.database.user}")
    print(f"Connection mode: {settings.database.connection_mode}")
    print()

    # Check DNS resolution first
    print("Checking DNS resolution...")
    dns_result = check_dns_resolution(settings.database.host)
    if not dns_result["success"]:
        print(f"[FAIL] DNS resolution failed: {dns_result['error']}")
        print("\nPossible solutions:")
        print("1. Check your internet connection")
        print("2. Try using a different DNS server (e.g., 8.8.8.8)")
        print("3. Check if your firewall is blocking DNS queries")
        print("4. Verify the Supabase hostname is correct")
        return False

    print("[OK] DNS resolved successfully")
    if dns_result["ipv4"]:
        print(f"  IPv4 addresses: {', '.join(dns_result['ipv4'])}")
    if dns_result["ipv6"]:
        print(f"  IPv6 addresses: {', '.join(dns_result['ipv6'][:2])}...")  # Show first 2
    print()

    try:
        engine = get_engine()

        async with engine.begin() as conn:
            # Test basic query
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print("[OK] Connection successful!")
            print(f"  PostgreSQL version: {version[:50]}...")

            # Test another query
            result = await conn.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            print(f"  Current database: {db_name}")

            # Test user
            result = await conn.execute(text("SELECT current_user"))
            user = result.scalar()
            print(f"  Current user: {user}")

        await engine.dispose()
        return True

    except Exception as e:
        print("[FAIL] Connection failed!")
        print(f"  Error: {type(e).__name__}: {e}")
        print("\nPossible solutions:")
        print("1. Check if Supabase project is active")
        print("2. Verify database credentials in backend/.env")
        print("3. Check if your IP is allowed in Supabase settings")
        print("4. Try using port 6543 (transaction pooler) instead of 5432")
        print("5. Ensure DATABASE_CONNECTION_MODE matches the port (session_pooler=5432, transaction_pooler=6543)")
        return False


async def test_pooler_connections():
    """Test different Supabase pooler connection formats."""
    settings = get_settings()

    # Extract base info from settings
    base_host = settings.database.host
    user = settings.database.user
    password = settings.database.password
    database = settings.database.name

    # Determine pooler hostname (convert db.* to pooler.*)
    if base_host.startswith("db."):
        # Extract region and project from db.xxx.supabase.co
        parts = base_host.split(".")
        if len(parts) >= 3:
            project_ref = parts[1]
            # Try to determine region from project ref or use default
            pooler_host = f"aws-0-us-east-1.pooler.supabase.com"  # Default region
            print(f"Note: Using default pooler region. Update if your project is in a different region.")
        else:
            pooler_host = base_host
    else:
        pooler_host = base_host

    pooler_configs = [
        {"name": "Session Pooler", "port": 5432, "mode": "session_pooler", "prepared_statements": True},
        {"name": "Transaction Pooler", "port": 6543, "mode": "transaction_pooler", "prepared_statements": False},
    ]

    print("\n" + "=" * 70)
    print("Testing Supabase Pooler Connections")
    print("=" * 70)

    success_count = 0

    for config in pooler_configs:
        print(f"\nTest: {config['name']}")
        print("-" * 70)

        # Check DNS first
        print(f"Checking DNS for {pooler_host}...")
        dns_result = check_dns_resolution(pooler_host)
        if not dns_result["success"]:
            print(f"[FAIL] DNS resolution failed: {dns_result['error']}")
            continue

        print("[OK] DNS resolved successfully")
        if dns_result["ipv4"]:
            print(f"  IPv4: {', '.join(dns_result['ipv4'][:2])}")  # Show first 2 IPs

        # Build connection URL
        url = f"postgresql+asyncpg://{user}:{password}@{pooler_host}:{config['port']}/{database}"

        print(f"Connecting to port {config['port']} ({config['mode']})...")
        try:
            # Connection options
            connect_args = {
                "timeout": 10,
                "command_timeout": 10,
            }

            # Disable prepared statements for transaction pooler
            if not config['prepared_statements']:
                connect_args["statement_cache_size"] = 0

            engine = create_async_engine(
                url,
                echo=False,
                pool_pre_ping=True,
                connect_args=connect_args,
                execution_options={"prepared_statement_cache_size": 0} if not config['prepared_statements'] else {},
            )

            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT version()"))
                version = result.scalar()
                print("[OK] Connection successful!")
                print(f"  PostgreSQL: {version[:60]}...")

                # Test a simple query
                result = await conn.execute(text("SELECT current_database()"))
                db_name = result.scalar()
                print(f"  Database: {db_name}")

            await engine.dispose()
            print(f"[OK] {config['name']} test passed!")
            success_count += 1

        except Exception as e:
            print(f"[FAIL] Failed: {type(e).__name__}: {e}")

    print("\n" + "=" * 70)
    if success_count > 0:
        print(f"✅ {success_count}/{len(pooler_configs)} pooler tests passed")
    else:
        print("⚠ All pooler connection attempts failed")
        print("=" * 70)
        print("\nTroubleshooting steps:")
        print("1. Verify your Supabase project is active")
        print("2. Check database credentials in backend/.env")
        print("3. Ensure your IP is whitelisted in Supabase settings")
        print("4. Verify the pooler region matches your project")
        print("5. Try connecting from Supabase dashboard first")
    print("=" * 70)

    return success_count > 0


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("SUPABASE CONNECTION TEST")
    print("=" * 70)

    # Test 1: Current configuration
    print("\n[Test 1] Testing current configuration from backend/.env")
    print("=" * 70)
    success1 = asyncio.run(test_connection())

    # Test 2: Try different pooler modes
    print("\n[Test 2] Testing different pooler modes")
    print("=" * 70)
    success2 = asyncio.run(test_pooler_connections())

    # Final summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    if success1 or success2:
        print("✅ At least one connection method succeeded!")
        print("\nRecommendation:")
        if success1:
            print("- Your current configuration works. No changes needed.")
        else:
            print("- Update your backend/.env to use the working pooler configuration.")
    else:
        print("❌ All connection attempts failed")
        print("\n[WARNING] CONNECTION FAILED - Possible IPv6 Resolution Issue")
        print("=" * 70)
        print("\nThis is a known issue with Supabase IPv6-only addresses on Windows.")
        print("\nQuick fixes:")
        print("1. Enable IPv6 on Windows:")
        print("   Enable-NetAdapterBinding -Name '*' -ComponentID ms_tcpip6")
        print("\n2. Use transaction pooler (port 6543) instead of session pooler (port 5432)")
        print("   Update DATABASE_PORT=6543 and DATABASE_CONNECTION_MODE=transaction_pooler")
        print("\n3. Use local PostgreSQL for development")
        print("\n4. Check Supabase dashboard for connection details")
        print("=" * 70)

    exit(0 if (success1 or success2) else 1)
