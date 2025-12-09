# PixCrawler SDK

The official Python SDK for PixCrawler, providing a unified interface for automated image dataset building, validation, and pipeline orchestration.

## Features

- **Unified Client**: Single entry point (`PixCrawler`) for all operations.
- **Async Support**: Native `async/await` support for non-blocking integration.
- **Local Mode**: run crawlers and validators directly on your machine.
- **Modern**: Pydantic models, Loguru logging, and Type hints.

## Installation

```bash
uv pip install -e sdk
# or
pip install pixcrawler-sdk
```

## Quick Start

### 1. Basic Crawl (Local)

```python
import asyncio
from pixcrawler import PixCrawler

async def main():
    # Initialize client
    client = PixCrawler()
    
    # Run a crawl job
    print("Crawling...")
    results = await client.crawl_local(
        keyword="golden retriever running", 
        max_images=50,
        output_dir="./datasets"
    )
    
    # results is a list of EngineResult objects
    print(f"Downloaded {sum(r.total_downloaded for r in results)} images.")

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Validation

```python
import asyncio
from pixcrawler import PixCrawler

async def main():
    client = PixCrawler()
    
    # Validate existing dataset (checks duplicates and integrity)
    duplicates, integrity = await client.validate_local("./datasets/golden_retriever_running")
    
    print(f"Removed {duplicates.duplicates_removed} duplicates.")
    print(f"Valid images: {integrity.valid_images}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

The SDK uses `pydantic-settings`. You can configure it via environment variables in a `.env` file or directly in the shell.

| Variable | Description | Default |
|----------|-------------|---------|
| `PIXCRAWLER_LOG_LEVEL` | Logging verbosity | `INFO` |
| `PIXCRAWLER_DEFAULT_OUTPUT_DIR` | Default download path | `./datasets` |
| `PIXCRAWLER_REDIS_URL` | Redis URL for caching | `redis://localhost:6379/0` |

## Advanced Usage

### Custom Crawl Request

```python
from pixcrawler import CrawlRequest

request = CrawlRequest(
    keyword="futuristic city",
    max_images=200,
    use_variations=True
)
# Access the internal engine directly if needed
await client.crawler.crawl(request)
```

### Async & Concurrency

The SDK wraps blocking I/O (like file system operations and legacy sync HTTP calls) in threads internally, so you can safely use it in an `asyncio` loop without blocking your main application.
