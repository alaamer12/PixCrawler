"""
Super nuclear option: Drop EVERYTHING including extensions and recreate.
"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text, create_engine
from backend.core.config import get_settings
from backend.database.connection import get_engine
from backend.models import Base


async def super_nuclear_reset():
    """Drop everything and start completely fresh."""
    settings = get_settings()
    engine = get_engine()
    
    print("\n" + "=" * 70)
    print("💣 SUPER NUCLEAR DATABASE RESET 💣")
    print("=" * 70)
    print(f"Database: {settings.database.host}/{settings.database.name}")
    print("\n⚠️  WARNING: This will delete ABSOLUTELY EVERYTHING!")
    print("=" * 70)
    
    async with engine.begin() as conn:
        print("\n1. Dropping public schema...")
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        print("   ✓ Public schema dropped")
        
        print("\n2. Recreating public schema...")
        await conn.execute(text("CREATE SCHEMA public"))
        print("   ✓ Public schema created")
        
        print("\n3. Granting permissions...")
        await conn.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
        print("   ✓ Permissions granted")
    
    await engine.dispose()
    print("\n✅ Database completely wiped!")


async def create_all_tables():
    """Create all tables from SQLAlchemy models."""
    settings = get_settings()
    
    print("\n" + "=" * 70)
    print("CREATING ALL TABLES FROM MODELS")
    print("=" * 70)
    
    database_url = settings.database.get_connection_url()
    sync_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    sync_engine = create_engine(sync_url, echo=False)
    
    try:
        Base.metadata.create_all(sync_engine)
        print("\n✅ All tables created successfully!")
        print("\nCreated tables:")
        for table_name in sorted(Base.metadata.tables.keys()):
            print(f"  ✓ {table_name}")
    finally:
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
    
    print(f"\nFound {len(tables)} tables in database:")
    for table in tables:
        print(f"  ✓ {table}")
    
    await engine.dispose()
    return tables


async def main():
    """Main function."""
    print("\n" + "=" * 70)
    print("PIXCRAWLER - SUPER NUCLEAR DATABASE RESET")
    print("=" * 70)
    
    try:
        await super_nuclear_reset()
        await create_all_tables()
        tables = await verify_tables()
        
        print("\n" + "=" * 70)
        print("✅ DATABASE RESET COMPLETE!")
        print("=" * 70)
        print(f"\nTotal tables created: {len(tables)}")
        print("\n🎉 Your database is now completely clean and ready!")
        print("\nNext steps:")
        print("1. Restart your backend server")
        print("2. Test the API endpoints")
        print("3. Create your first dataset")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
