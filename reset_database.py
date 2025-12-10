"""
Create all database tables from SQLAlchemy models.

This script drops all existing tables and creates fresh ones
based on the current SQLAlchemy model definitions.

WARNING: This will delete ALL data in the database!
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from backend.core.config import get_settings
from backend.database.connection import get_engine
from backend.models import Base  # This imports all models


async def drop_all_tables():
    """Drop all tables in the database."""
    settings = get_settings()
    engine = get_engine()
    
    print("=" * 70)
    print("DROPPING ALL TABLES")
    print("=" * 70)
    print(f"Database: {settings.database.host}/{settings.database.name}")
    print("WARNING: This will delete ALL data!")
    print("=" * 70)
    
    # List of tables to drop in reverse dependency order
    tables_to_drop = [
        'policy_execution_logs',
        'archival_policies',
        'retention_policies',
        'job_chunks',
        'activity_logs',
        'images',
        'datasets',
        'crawl_jobs',
        'projects',
        'usage_metrics',
        'api_keys',
        'notifications',
        'notification_preferences',
        'credit_accounts',
        'profiles',
        'alembic_version'
    ]
    
    async with engine.begin() as conn:
        # First, drop all indexes
        print("\nDropping all indexes...")
        result = await conn.execute(text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE schemaname = 'public'
        """))
        indexes = [row[0] for row in result]
        for index in indexes:
            try:
                await conn.execute(text(f"DROP INDEX IF EXISTS {index} CASCADE"))
                print(f"✓ Dropped index: {index}")
            except Exception as e:
                print(f"✗ Error dropping index {index}: {e}")
        
        # Then drop all tables
        print("\nDropping all tables...")
        for table in tables_to_drop:
            try:
                await conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                print(f"✓ Dropped table: {table}")
            except Exception as e:
                print(f"✗ Error dropping {table}: {e}")
    
    print("\n✅ All tables dropped successfully!")
    await engine.dispose()


async def create_all_tables():
    """Create all tables from SQLAlchemy models."""
    settings = get_settings()
    
    # Get synchronous engine for table creation
    from sqlalchemy import create_engine
    database_url = settings.database.get_connection_url()
    # Use psycopg2 for synchronous operations
    sync_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    sync_engine = create_engine(sync_url)
    
    print("\n" + "=" * 70)
    print("CREATING ALL TABLES FROM MODELS")
    print("=" * 70)
    
    # Create all tables
    Base.metadata.create_all(sync_engine)
    
    print("\n✅ All tables created successfully!")
    print("\nCreated tables:")
    for table_name in sorted(Base.metadata.tables.keys()):
        print(f"  ✓ {table_name}")
    
    sync_engine.dispose()


async def verify_tables():
    """Verify that all tables were created."""
    engine = get_engine()
    
    print("\n" + "=" * 70)
    print("VERIFYING TABLE CREATION")
    print("=" * 70)
    
    async with engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """))
        tables = [row[0] for row in result]
    
    print(f"\nFound {len(tables)} tables:")
    for table in tables:
        print(f"  ✓ {table}")
    
    await engine.dispose()
    return tables


async def main():
    """Main function to recreate database schema."""
    print("\n" + "=" * 70)
    print("PIXCRAWLER DATABASE RESET")
    print("=" * 70)
    print("\nThis script will:")
    print("1. Drop all existing tables")
    print("2. Create fresh tables from SQLAlchemy models")
    print("3. Verify table creation")
    print("\n⚠️  WARNING: ALL DATA WILL BE LOST!")
    print("=" * 70)
    
    # Drop all tables
    await drop_all_tables()
    
    # Create all tables
    await create_all_tables()
    
    # Verify
    tables = await verify_tables()
    
    print("\n" + "=" * 70)
    print("✅ DATABASE RESET COMPLETE!")
    print("=" * 70)
    print(f"\nTotal tables created: {len(tables)}")
    print("\nYou can now:")
    print("1. Run the backend server")
    print("2. Create test data via API")
    print("3. Set up Alembic migrations for future changes")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
