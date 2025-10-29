"""
Integration tests for storage service.

This module contains integration tests that verify end-to-end storage workflows,
factory patterns, configuration integration, and cross-component interactions.

Test Coverage:
    - Storage factory with different configurations
    - End-to-end workflows with real file operations
    - Configuration loading from environment
    - Error recovery and retry mechanisms
    - Performance and concurrency scenarios
"""

import os
import tempfile
import time
from pathlib import Path
from typing import Generator
from unittest.mock import patch

import pytest

from backend.storage.config import StorageSettings
from backend.storage.factory import create_storage_provider, get_storage_provider
from backend.storage.local import LocalStorageProvider


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_storage_dir() -> Generator[Path, None, None]:
    """Create temporary storage directory for integration tests.
    
    Yields:
        Path to temporary storage directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_files_dir(temp_storage_dir: Path) -> Path:
    """Create directory with test files (outside storage directory).
    
    Args:
        temp_storage_dir: Temporary storage directory
        
    Returns:
        Path to test files directory
    """
    # Create in a separate directory to avoid interfering with storage tests
    test_dir = temp_storage_dir.parent / "source_test_files"
    test_dir.mkdir(exist_ok=True)
    
    # Create various test files
    (test_dir / "text.txt").write_text("Text file content")
    (test_dir / "data.json").write_text('{"key": "value"}')
    (test_dir / "image.png").write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
    
    return test_dir


@pytest.fixture
def local_storage_settings(temp_storage_dir: Path) -> StorageSettings:
    """Create storage settings for local provider.
    
    Args:
        temp_storage_dir: Temporary storage directory
        
    Returns:
        StorageSettings instance
    """
    return StorageSettings(
        storage_provider="local",
        local_storage_path=str(temp_storage_dir)
    )


# ============================================================================
# Storage Factory Integration Tests
# ============================================================================

class TestStorageFactory:
    """Test storage factory integration."""
    
    def test_create_local_provider_from_settings(self, local_storage_settings: StorageSettings):
        """Test creating local provider from settings."""
        provider = create_storage_provider(local_storage_settings)
        
        assert isinstance(provider, LocalStorageProvider)
        assert provider.base_directory == Path(local_storage_settings.local_storage_path)
    
    def test_create_provider_with_default_settings(self):
        """Test creating provider with default settings."""
        settings = StorageSettings(storage_provider="local")
        provider = create_storage_provider(settings)
        
        assert isinstance(provider, LocalStorageProvider)
        assert provider.base_directory.exists()
    
    def test_get_storage_provider_convenience_function(self, local_storage_settings: StorageSettings):
        """Test get_storage_provider convenience function."""
        provider = get_storage_provider(local_storage_settings)
        
        assert isinstance(provider, LocalStorageProvider)
    
    def test_get_storage_provider_without_settings(self):
        """Test get_storage_provider creates default settings."""
        provider = get_storage_provider()
        
        assert isinstance(provider, LocalStorageProvider)
    
    def test_factory_raises_error_for_invalid_provider(self):
        """Test factory raises error for invalid provider type."""
        settings = StorageSettings(storage_provider="local")
        settings.storage_provider = "invalid"  # Bypass validation
        
        with pytest.raises(ValueError, match="Invalid storage provider"):
            create_storage_provider(settings)
    
    def test_factory_with_environment_variables(self, temp_storage_dir: Path):
        """Test factory uses environment variables."""
        with patch.dict(os.environ, {
            "STORAGE_PROVIDER": "local",
            "STORAGE_LOCAL_STORAGE_PATH": str(temp_storage_dir)
        }):
            settings = StorageSettings()
            provider = create_storage_provider(settings)
            
            assert isinstance(provider, LocalStorageProvider)
            assert provider.base_directory == temp_storage_dir


# ============================================================================
# End-to-End Workflow Tests
# ============================================================================

class TestEndToEndWorkflows:
    """Test complete end-to-end storage workflows."""
    
    def test_complete_dataset_workflow(self, local_storage_settings: StorageSettings, test_files_dir: Path, temp_storage_dir: Path):
        """Test complete dataset upload, organization, and download workflow."""
        provider = create_storage_provider(local_storage_settings)
        
        # Step 1: Upload dataset files
        dataset_files = {
            "datasets/project1/images/img1.png": test_files_dir / "image.png",
            "datasets/project1/images/img2.png": test_files_dir / "image.png",
            "datasets/project1/metadata.json": test_files_dir / "data.json",
            "datasets/project1/readme.txt": test_files_dir / "text.txt"
        }
        
        for dest_path, source_file in dataset_files.items():
            provider.upload(source_file, dest_path)
        
        # Step 2: Verify all files uploaded
        all_files = provider.list_files()
        assert len(all_files) == 4
        
        # Step 3: List files by category
        image_files = provider.list_files(prefix="datasets/project1/images/")
        assert len(image_files) == 2
        
        # Step 4: Download specific files
        download_dir = temp_storage_dir / "downloads"
        download_dir.mkdir()
        
        provider.download("datasets/project1/metadata.json", download_dir / "metadata.json")
        assert (download_dir / "metadata.json").exists()
        
        # Step 5: Generate presigned URLs
        for file_path in image_files:
            url = provider.generate_presigned_url(file_path)
            assert url.startswith("file://")
        
        # Step 6: Cleanup - delete old images
        provider.delete("datasets/project1/images/img1.png")
        remaining_images = provider.list_files(prefix="datasets/project1/images/")
        assert len(remaining_images) == 1
    
    def test_multi_project_isolation(self, local_storage_settings: StorageSettings, test_files_dir: Path):
        """Test multiple projects with isolated storage."""
        provider = create_storage_provider(local_storage_settings)
        
        # Upload files for multiple projects
        projects = ["project_a", "project_b", "project_c"]
        
        for project in projects:
            provider.upload(test_files_dir / "text.txt", f"{project}/data.txt")
            provider.upload(test_files_dir / "data.json", f"{project}/config.json")
        
        # Verify isolation - each project has its files
        for project in projects:
            project_files = provider.list_files(prefix=f"{project}/")
            assert len(project_files) == 2
            assert all(f.startswith(f"{project}/") for f in project_files)
        
        # Verify total files
        all_files = provider.list_files()
        assert len(all_files) == 6
    
    def test_backup_and_restore_workflow(self, local_storage_settings: StorageSettings, test_files_dir: Path, temp_storage_dir: Path):
        """Test backup and restore workflow."""
        provider = create_storage_provider(local_storage_settings)
        
        # Original files
        original_files = {
            "data/file1.txt": test_files_dir / "text.txt",
            "data/file2.json": test_files_dir / "data.json"
        }
        
        # Upload original files
        for dest, source in original_files.items():
            provider.upload(source, dest)
        
        # Create backup (outside storage directory)
        backup_dir = temp_storage_dir.parent / "backup"
        backup_dir.mkdir(exist_ok=True)
        
        for file_path in provider.list_files():
            backup_path = backup_dir / file_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            provider.download(file_path, backup_path)
        
        # Simulate data loss - delete all files
        for file_path in provider.list_files():
            provider.delete(file_path)
        
        assert len(provider.list_files()) == 0
        
        # Restore from backup
        for backup_file in backup_dir.rglob("*"):
            if backup_file.is_file():
                relative_path = backup_file.relative_to(backup_dir)
                provider.upload(backup_file, str(relative_path).replace("\\", "/"))
        
        # Verify restoration
        restored_files = provider.list_files()
        assert len(restored_files) == 2
    
    def test_versioning_workflow(self, local_storage_settings: StorageSettings, test_files_dir: Path):
        """Test file versioning workflow."""
        provider = create_storage_provider(local_storage_settings)
        
        file_path = "documents/report.txt"
        
        # Version 1
        version1_content = "Version 1 content"
        v1_file = test_files_dir / "v1.txt"
        v1_file.write_text(version1_content)
        provider.upload(v1_file, file_path)
        
        # Create backup of v1
        provider.upload(v1_file, f"{file_path}.v1")
        
        # Version 2 (overwrite)
        version2_content = "Version 2 content"
        v2_file = test_files_dir / "v2.txt"
        v2_file.write_text(version2_content)
        provider.upload(v2_file, file_path)
        
        # Create backup of v2
        provider.upload(v2_file, f"{file_path}.v2")
        
        # Verify versions exist
        files = provider.list_files()
        assert file_path in files
        assert f"{file_path}.v1" in files
        assert f"{file_path}.v2" in files
        
        # Verify current version
        download_path = test_files_dir / "current.txt"
        provider.download(file_path, download_path)
        assert download_path.read_text() == version2_content


# ============================================================================
# Configuration Integration Tests
# ============================================================================

class TestConfigurationIntegration:
    """Test configuration integration with storage."""
    
    def test_settings_from_environment(self, temp_storage_dir: Path):
        """Test loading settings from environment variables."""
        env_vars = {
            "STORAGE_PROVIDER": "local",
            "STORAGE_LOCAL_STORAGE_PATH": str(temp_storage_dir),
            "STORAGE_AZURE_CONTAINER_NAME": "test-container",
            "STORAGE_AZURE_MAX_RETRIES": "5",
            "STORAGE_AZURE_DEFAULT_TIER": "cool"
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            settings = StorageSettings()
            
            assert settings.storage_provider == "local"
            assert settings.local_storage_path == str(temp_storage_dir)
            assert settings.azure_container_name == "test-container"
            assert settings.azure_max_retries == 5
            assert settings.azure_default_tier == "cool"
    
    def test_settings_validation_integration(self):
        """Test settings validation in integration context."""
        # Valid configuration
        settings = StorageSettings(
            storage_provider="local",
            azure_lifecycle_cool_after_days=30,
            azure_lifecycle_archive_after_days=90,
            azure_lifecycle_delete_after_days=365
        )
        
        assert settings.azure_lifecycle_cool_after_days == 30
        assert settings.azure_lifecycle_archive_after_days == 90
        assert settings.azure_lifecycle_delete_after_days == 365
    
    def test_provider_creation_with_various_configs(self, temp_storage_dir: Path):
        """Test provider creation with various configurations."""
        configs = [
            {"storage_provider": "local"},
            {"storage_provider": "local", "local_storage_path": str(temp_storage_dir)},
            {"storage_provider": "local", "azure_enable_archive_tier": False},
        ]
        
        for config in configs:
            settings = StorageSettings(**config)
            provider = create_storage_provider(settings)
            assert isinstance(provider, LocalStorageProvider)


# ============================================================================
# Error Recovery Tests
# ============================================================================

class TestErrorRecovery:
    """Test error recovery and resilience."""
    
    def test_recovery_from_partial_upload(self, local_storage_settings: StorageSettings, test_files_dir: Path):
        """Test recovery from partial upload failure."""
        provider = create_storage_provider(local_storage_settings)
        
        files_to_upload = [
            "batch/file1.txt",
            "batch/file2.txt",
            "batch/file3.txt"
        ]
        
        # Upload first two files
        provider.upload(test_files_dir / "text.txt", files_to_upload[0])
        provider.upload(test_files_dir / "text.txt", files_to_upload[1])
        
        # Simulate failure before third file
        uploaded_files = provider.list_files(prefix="batch/")
        assert len(uploaded_files) == 2
        
        # Retry - upload remaining files
        for file_path in files_to_upload:
            try:
                provider.upload(test_files_dir / "text.txt", file_path)
            except Exception:
                pass  # File might already exist
        
        # Verify all files uploaded
        final_files = provider.list_files(prefix="batch/")
        assert len(final_files) == 3
    
    def test_graceful_handling_of_missing_files(self, local_storage_settings: StorageSettings):
        """Test graceful handling of missing files."""
        provider = create_storage_provider(local_storage_settings)
        
        # Try to download non-existent file
        with pytest.raises(FileNotFoundError):
            provider.download("nonexistent.txt", "/tmp/output.txt")
        
        # Try to delete non-existent file
        with pytest.raises(FileNotFoundError):
            provider.delete("nonexistent.txt")
        
        # List files should work even if empty
        files = provider.list_files()
        assert files == []
    
    def test_handling_of_corrupted_operations(self, local_storage_settings: StorageSettings, test_files_dir: Path):
        """Test handling of corrupted or invalid operations."""
        provider = create_storage_provider(local_storage_settings)
        
        # Upload valid file
        provider.upload(test_files_dir / "text.txt", "valid.txt")
        
        # Try invalid operations (should raise IOError, not ValueError)
        with pytest.raises(IOError, match="Upload failed.*directory traversal detected"):
            provider.upload(test_files_dir / "text.txt", "../../../etc/passwd")
        
        # Verify valid file still exists
        files = provider.list_files()
        assert "valid.txt" in files


# ============================================================================
# Performance and Concurrency Tests
# ============================================================================

class TestPerformanceAndConcurrency:
    """Test performance and concurrency scenarios."""
    
    def test_large_file_operations(self, local_storage_settings: StorageSettings, temp_storage_dir: Path):
        """Test operations with larger files."""
        provider = create_storage_provider(local_storage_settings)
        
        # Create a larger file (1MB)
        large_file = temp_storage_dir / "large_file.bin"
        large_file.write_bytes(b'\x00' * (1024 * 1024))
        
        # Upload
        start_time = time.time()
        provider.upload(large_file, "large/file.bin")
        upload_time = time.time() - start_time
        
        # Should complete reasonably fast (< 1 second for 1MB)
        assert upload_time < 1.0
        
        # Download
        download_path = temp_storage_dir / "downloaded_large.bin"
        start_time = time.time()
        provider.download("large/file.bin", download_path)
        download_time = time.time() - start_time
        
        assert download_time < 1.0
        assert download_path.stat().st_size == large_file.stat().st_size
    
    def test_many_small_files(self, local_storage_settings: StorageSettings, test_files_dir: Path):
        """Test operations with many small files."""
        provider = create_storage_provider(local_storage_settings)
        
        # Upload 100 small files
        num_files = 100
        start_time = time.time()
        
        for i in range(num_files):
            provider.upload(test_files_dir / "text.txt", f"batch/file_{i:03d}.txt")
        
        upload_time = time.time() - start_time
        
        # Should complete in reasonable time (< 5 seconds for 100 files)
        assert upload_time < 5.0
        
        # List all files
        start_time = time.time()
        files = provider.list_files(prefix="batch/")
        list_time = time.time() - start_time
        
        assert len(files) == num_files
        assert list_time < 1.0
    
    def test_sequential_operations_performance(self, local_storage_settings: StorageSettings, test_files_dir: Path, temp_storage_dir: Path):
        """Test performance of sequential operations."""
        provider = create_storage_provider(local_storage_settings)
        
        file_path = "perf/test.txt"
        
        # Upload
        provider.upload(test_files_dir / "text.txt", file_path)
        
        # Multiple reads should be fast
        download_path = temp_storage_dir / "download.txt"
        
        start_time = time.time()
        for _ in range(10):
            provider.download(file_path, download_path)
        total_time = time.time() - start_time
        
        # 10 downloads should complete quickly (< 1 second)
        assert total_time < 1.0
    
    def test_list_files_with_large_directory(self, local_storage_settings: StorageSettings, test_files_dir: Path):
        """Test list_files performance with large directory."""
        provider = create_storage_provider(local_storage_settings)
        
        # Create nested structure with many files
        for i in range(50):
            provider.upload(test_files_dir / "text.txt", f"dir{i % 5}/file_{i}.txt")
        
        # List all files
        start_time = time.time()
        all_files = provider.list_files()
        list_time = time.time() - start_time
        
        assert len(all_files) == 50
        assert list_time < 1.0
        
        # List with prefix should be fast
        start_time = time.time()
        dir0_files = provider.list_files(prefix="dir0/")
        prefix_time = time.time() - start_time
        
        assert len(dir0_files) == 10
        assert prefix_time < 0.5


# ============================================================================
# Real-World Scenario Tests
# ============================================================================

class TestRealWorldScenarios:
    """Test real-world usage scenarios."""
    
    def test_image_dataset_management(self, local_storage_settings: StorageSettings, test_files_dir: Path):
        """Test managing an image dataset."""
        provider = create_storage_provider(local_storage_settings)
        
        # Simulate dataset structure
        categories = ["cats", "dogs", "birds"]
        images_per_category = 5
        
        # Upload images
        for category in categories:
            for i in range(images_per_category):
                provider.upload(
                    test_files_dir / "image.png",
                    f"datasets/animals/{category}/image_{i:03d}.png"
                )
        
        # Upload metadata
        provider.upload(test_files_dir / "data.json", "datasets/animals/metadata.json")
        
        # Verify structure
        total_files = provider.list_files(prefix="datasets/animals/")
        assert len(total_files) == (len(categories) * images_per_category) + 1
        
        # Get images for specific category
        cat_images = provider.list_files(prefix="datasets/animals/cats/")
        assert len(cat_images) == images_per_category
        
        # Generate URLs for all images
        urls = []
        for file_path in provider.list_files(prefix="datasets/animals/"):
            if file_path.endswith(".png"):
                url = provider.generate_presigned_url(file_path, expires_in=3600)
                urls.append(url)
        
        assert len(urls) == len(categories) * images_per_category
    
    def test_temporary_file_cleanup(self, local_storage_settings: StorageSettings, test_files_dir: Path):
        """Test cleanup of temporary files."""
        provider = create_storage_provider(local_storage_settings)
        
        # Upload temporary processing files
        temp_files = [
            "temp/processing_1.tmp",
            "temp/processing_2.tmp",
            "temp/cache_1.tmp"
        ]
        
        for temp_file in temp_files:
            provider.upload(test_files_dir / "text.txt", temp_file)
        
        # Upload permanent files
        provider.upload(test_files_dir / "text.txt", "results/final.txt")
        
        # Cleanup temp files
        temp_file_list = provider.list_files(prefix="temp/")
        for temp_file in temp_file_list:
            provider.delete(temp_file)
        
        # Verify only permanent files remain
        all_files = provider.list_files()
        assert len(all_files) == 1
        assert "results/final.txt" in all_files
    
    def test_user_quota_simulation(self, local_storage_settings: StorageSettings, test_files_dir: Path):
        """Test simulating user storage quota."""
        provider = create_storage_provider(local_storage_settings)
        
        # Simulate user uploading files
        user_id = "user123"
        max_files = 10
        
        # Upload files up to quota
        for i in range(max_files):
            provider.upload(test_files_dir / "text.txt", f"users/{user_id}/file_{i}.txt")
        
        # Check user's file count
        user_files = provider.list_files(prefix=f"users/{user_id}/")
        assert len(user_files) == max_files
        
        # Simulate quota exceeded (application logic would prevent this)
        # But storage layer should still work
        provider.upload(test_files_dir / "text.txt", f"users/{user_id}/file_{max_files}.txt")
        
        user_files = provider.list_files(prefix=f"users/{user_id}/")
        assert len(user_files) == max_files + 1
