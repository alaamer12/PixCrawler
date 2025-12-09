import asyncio
import sys
from pathlib import Path

# Add repo root to path so we can import 'sdk'
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))

# Also add sdk dir itself if needed, but 'sdk.pixcrawler' implies sdk is a namespace or root
sys.path.insert(0, str(repo_root / "sdk"))

try:
    from pixcrawler import PixCrawler, CrawlRequest
    print("SUCCESS: SDK Imported successfully")
except ImportError as e:
    print(f"ERROR: Import failed: {e}")
    sys.exit(1)

async def main():
    print("Initializing Client...")
    client = PixCrawler()
    
    print("Client initialized. SDK Structure verified.")
    # We won't actually crawl to avoid network usage/delays in smoke test, 
    # but we will check if methods exist.
    assert hasattr(client, 'crawl_local')
    assert hasattr(client, 'validate_local')
    print("SUCCESS: Client methods verified.")

if __name__ == "__main__":
    asyncio.run(main())
