import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from pixcrawler.chunk_worker.src.tasks.process_chunk import process_chunk_task

class TestChunkPipeline(unittest.TestCase):
    def setUp(self):
        # Configure Celery to run tasks locally and synchronously
        process_chunk_task.app.conf.task_always_eager = True
        process_chunk_task.app.conf.task_eager_propagates = True
        
        # Set mock env vars
        self.env_patcher = patch.dict(os.environ, {
            "AZURE_STORAGE_CONNECTION_STRING": "DefaultEndpointsProtocol=https;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;",
            "AZURE_CONTAINER_NAME": "test-container"
        })
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    @patch('pixcrawler.chunk_worker.src.tasks.process_chunk.ChunkDownloader')
    @patch('pixcrawler.chunk_worker.src.tasks.process_chunk.ChunkValidator')
    @patch('pixcrawler.chunk_worker.src.tasks.process_chunk.ChunkCompressor')
    @patch('pixcrawler.chunk_worker.src.tasks.process_chunk.ChunkUploader')
    @patch('pixcrawler.chunk_worker.src.tasks.process_chunk.ChunkCleanup')
    @patch('pixcrawler.chunk_worker.src.tasks.process_chunk.get_logger')
    @patch('pixcrawler.chunk_worker.src.tasks.process_chunk.StatusManager')
    def test_pipeline_success(self, mock_status_manager, mock_get_logger, mock_cleanup, mock_uploader, mock_compressor, mock_validator, mock_downloader):
        """Test the successful execution of the chunk processing pipeline."""
        print("\nTesting Pipeline Success...")
        
        # Setup mocks
        mock_downloader.return_value.download_chunk.return_value = 500
        mock_validator.return_value.validate_chunk.return_value = 500
        mock_compressor.return_value.compress_chunk.return_value = "/tmp/fake.zip"
        mock_uploader.return_value.upload_chunk.return_value = "http://azure/fake.zip"
        
        # Mock logger
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Run task
        # We use .apply() to execute the task with eager mode
        result = process_chunk_task.apply(args=("chunk-123", "cat")).get()
        
        # Verify result
        self.assertEqual(result, "http://azure/fake.zip")
        print("Result matched expected URL.")
        
        # Verify calls
        mock_downloader.return_value.download_chunk.assert_called_once()
        mock_validator.return_value.validate_chunk.assert_called_once()
        mock_compressor.return_value.compress_chunk.assert_called_once()
        mock_uploader.return_value.upload_chunk.assert_called_once()
        mock_cleanup.return_value.cleanup.assert_called_once()
        
        # Verify status updates
        mock_status_manager.return_value.update_status.assert_any_call("chunk-123", "PROCESSING")
        mock_status_manager.return_value.update_status.assert_any_call("chunk-123", "COMPLETED", details={"url": "http://azure/fake.zip"})
        print("Pipeline steps verified successfully.")

    @patch('pixcrawler.chunk_worker.src.tasks.process_chunk.ChunkDownloader')
    @patch('pixcrawler.chunk_worker.src.tasks.process_chunk.ChunkCleanup')
    @patch('pixcrawler.chunk_worker.src.tasks.process_chunk.get_logger')
    @patch('pixcrawler.chunk_worker.src.tasks.process_chunk.StatusManager')
    def test_pipeline_failure_cleanup(self, mock_status_manager, mock_get_logger, mock_cleanup, mock_downloader):
        """Test that cleanup runs even when the pipeline fails."""
        print("\nTesting Pipeline Failure & Cleanup...")
        
        # Setup mocks to fail at download
        mock_downloader.return_value.download_chunk.side_effect = Exception("Download failed")
        
        # Mock logger
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Run task and expect exception
        with self.assertRaises(Exception):
            process_chunk_task.apply(args=("chunk-fail", "dog")).get()
            
        # Verify cleanup was called
        mock_cleanup.return_value.cleanup.assert_called_once()
        print("Cleanup verified after failure.")
        
        # Verify status update to FAILED
        mock_status_manager.return_value.update_status.assert_any_call("chunk-fail", "FAILED", details={"error": "Download failed"})
        print("Status update to FAILED verified.")

if __name__ == "__main__":
    unittest.main()
