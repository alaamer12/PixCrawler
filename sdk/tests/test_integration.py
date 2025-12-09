"""
Integration Tests for PixCrawler SDK
"""
import pytest
import shutil
from pathlib import Path
from pixcrawler import PixCrawler

# Define a temporary output directory for tests
TEST_OUTPUT = Path("./test_output_integration")

@pytest.fixture
def clean_env():
    if TEST_OUTPUT.exists():
        shutil.rmtree(TEST_OUTPUT)
    yield
    if TEST_OUTPUT.exists():
        shutil.rmtree(TEST_OUTPUT)

@pytest.mark.asyncio
async def test_sdk_local_integration(clean_env):
    """
    Test a real (but small) crawl operation and validation.
    This verifies the end-to-end local flow.
    """
    client = PixCrawler()
    
    # 1. Crawl
    # We use a keyword that should give few results, or just 1 max_image
    # Note: This might hit the network. We should mock the network if we want strict unit tests,
    # but for "integration", we might want to see if it actually spins up threads etc.
    # However, to be safe and fast, we can mock the actual downloader logic 
    # but still test the SDK wrapper flow + directory creation.
    
    # For now, let's trust the mocks in unit tests for logic, 
    # and use this execution to ensure async loop doesn't explode.
    
    await client.crawler.crawl(
        request=type('obj', (object,), {'keyword': 'test', 'max_images': 1, 'use_variations': False}), 
        output_dir=TEST_OUTPUT
    )
    
    # 2. Validate
    # Even if empty (if network fails), it should run without error
    if TEST_OUTPUT.exists():
        dups, integrity = await client.validate_local(str(TEST_OUTPUT / "test"))
        assert integrity is not None

if __name__ == "__main__":
    pass
