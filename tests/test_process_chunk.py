import os
import shutil
import tempfile
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Import the task
from pixcrawler.chunk_worker.src.tasks.process_chunk import process_chunk_task
from pixcrawler.chunk_worker.src.services.downloader import ChunkDownloader
from pixcrawler.chunk_worker.src.services.validator import ChunkValidator
from pixcrawler.chunk_worker.src.services.uploader import ChunkUploader

@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("AZURE_STORAGE_CONNECTION_STRING", "DefaultEndpointsProtocol=https;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;")
    monkeypatch.setenv("AZURE_CONTAINER_NAME", "test-container")

@pytest.fixture
def mock_services():
    with patch("pixcrawler.chunk_worker.src.tasks.process_chunk.ChunkDownloader") as mock_downloader, \
         patch("pixcrawler.chunk_worker.src.tasks.process_chunk.ChunkValidator") as mock_validator, \
         patch("pixcrawler.chunk_worker.src.tasks.process_chunk.Archiver") as mock_archiver, \
         patch("pixcrawler.chunk_worker.src.tasks.process_chunk.ChunkUploader") as mock_uploader, \
         patch("pixcrawler.chunk_worker.src.tasks.process_chunk.StatusManager") as mock_status_manager, \
         patch("pixcrawler.chunk_worker.src.tasks.process_chunk.ChunkCleanup") as mock_cleanup:
        
        # Setup mocks
        mock_downloader_instance = mock_downloader.return_value
        mock_downloader_instance.download_chunk.return_value = 5
        
        mock_validator_instance = mock_validator.return_value
        mock_validator_instance.validate_chunk.return_value = 5
        
        mock_archiver_instance = mock_archiver.return_value
        mock_archiver_instance.create.return_value = Path("/tmp/test.zip")
        
        mock_uploader_instance = mock_uploader.return_value
        mock_uploader_instance.upload_chunk.return_value = "https://azure/blob/url"
        
        yield {
            "downloader": mock_downloader_instance,
            "validator": mock_validator_instance,
            "archiver": mock_archiver_instance,
            "uploader": mock_uploader_instance,
            "status_manager": mock_status_manager.return_value,
            "cleanup": mock_cleanup.return_value
        }

def test_process_chunk_happy_path(mock_env, mock_services):
    """Test the happy path of the process_chunk_task."""
    
    # Mock the task request
    process_chunk_task.request.id = "test-task-id"
    
    # Mock os.listdir to avoid "empty directory" error in compress_directory
    with patch("os.listdir", return_value=["dummy.jpg"]):
        # Run the task
        result = process_chunk_task(chunk_id=123, metadata={"keyword": "cat"})
    
    # Verify result
    assert result == "https://azure/blob/url"
    
    # Verify calls
    mock_services["downloader"].download_chunk.assert_called_once()
    mock_services["validator"].validate_chunk.assert_called_once()
    mock_services["archiver"].create.assert_called_once()
    mock_services["uploader"].upload_chunk.assert_called_once()
    mock_services["status_manager"].update_status.assert_any_call(123, "PROCESSING")
    mock_services["status_manager"].update_status.assert_any_call(123, "COMPLETED", details={"url": "https://azure/blob/url"})
    mock_services["cleanup"].cleanup.assert_called_once()

def test_process_chunk_validation_failure(mock_env, mock_services):
    """Test that validation failure raises ValueError and updates status to FAILED."""
    
    # Mock validation failure
    mock_services["validator"].validate_chunk.side_effect = ValueError("No valid images")
    
    process_chunk_task.request.id = "test-task-id"
    
    with pytest.raises(ValueError, match="No valid images"):
        process_chunk_task(chunk_id=123, metadata={"keyword": "cat"})
        
    mock_services["status_manager"].update_status.assert_any_call(123, "FAILED", details={"error": "No valid images"})
    # Cleanup should still be called
    mock_services["cleanup"].cleanup.assert_called_once()

def test_process_chunk_download_retry_integration():
    """Test retry logic in services (integration-like test with mocks)."""
    
    # We test the ChunkDownloader retry logic specifically
    with patch("pixcrawler.chunk_worker.src.services.downloader.ImageDownloader") as mock_builder_downloader:
        mock_builder_instance = mock_builder_downloader.return_value
        # Fail twice, then succeed
        mock_builder_instance.download.side_effect = [
            (False, 0), # Fail 1
            (False, 0), # Fail 2
            (True, 5)   # Success
        ]
        
        logger = MagicMock()
        downloader = ChunkDownloader(logger)
        
        # We need to patch sleep to avoid waiting
        with patch("time.sleep", return_value=None):
             # Depending on tenacity version, it might use different sleep
             # But we are testing if it retries.
             # Actually, since we use tenacity, we can't easily patch sleep unless we configure tenacity to not sleep.
             # But we can check if it calls the underlying method multiple times.
             
             count = downloader.download_chunk("cat", "/tmp", 5)
             assert count == 5
             assert mock_builder_instance.download.call_count == 3

