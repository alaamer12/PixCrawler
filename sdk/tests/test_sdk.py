"""
Tests for PixCrawler SDK
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path

from pixcrawler import PixCrawler, CrawlRequest, PixCrawlerError
from pixcrawler.services.builder import CrawlerEngine
from pixcrawler.services.validator import ValidationEngine

# Mock config to avoid env vars issues
@pytest.fixture
def mock_config():
    with patch("pixcrawler.services.builder.get_config") as mock:
        mock.return_value.DEFAULT_OUTPUT_DIR = Path("/tmp/pixcrawler")
        mock.return_value.DEFAULT_FEEDER_THREADS = 1
        mock.return_value.DEFAULT_PARSER_THREADS = 1
        mock.return_value.DEFAULT_DOWNLOADER_THREADS = 1
        yield mock

@pytest.fixture
def client():
    return PixCrawler()

@pytest.mark.asyncio
async def test_crawl_local_wrapper(client, mock_config):
    """Test that crawl_local calls the underlying crawler engine."""
    
    # Mock the internal sync runner
    with patch.object(CrawlerEngine, '_run_crawler_sync') as mock_run:
        mock_run.return_value = [] # Mock return list
        
        results = await client.crawl_local("test_keyword", max_images=10)
        
        assert isinstance(results, list)
        mock_run.assert_called_once()
        args = mock_run.call_args
        assert args[0][0].keyword == "test_keyword"
        assert args[0][0].max_images == 10

@pytest.mark.asyncio
async def test_validate_local_wrapper(client):
    """Test that validate_local calls the underlying validator engine."""
    
    # Mock the internal sync runner
    with patch.object(ValidationEngine, '_run_validation_sync') as mock_run:
        # Mock tuple return (duplicates, integrity)
        mock_run.return_value = (MagicMock(), MagicMock())
        
        await client.validate_local("/tmp/test_dir")
        
        mock_run.assert_called_once() 

def test_crawl_request_validation():
    """Test Pydantic validation for CrawlRequest."""
    req = CrawlRequest(keyword="cat")
    assert req.max_images == 100 # Default
    
    req = CrawlRequest(keyword="dog", max_images=50)
    assert req.max_images == 50
