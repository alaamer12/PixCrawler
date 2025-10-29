"""
Unit tests for storage providers.

This module contains unit tests for storage provider implementations,
focusing on individual method behavior, error handling, and edge cases.

Test Coverage:
    - LocalStorageProvider: All operations (upload, download, delete, list, presigned URL)
    - Path validation and security (directory traversal prevention)
    - Error handling for various failure scenarios
    - File operations with different file types and sizes
"""

import os
import tempfile
import time
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

from backend.storage.local import LocalStorageProvider
from backend.storage.config import StorageSettings


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing.
    
    Yields:
        Path to temporary directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def local_storage(temp_dir: Path) -> LocalStorageProvider:
    """Create LocalStorageProvider instance with temp directory.
    
    Args:
        temp_dir: Temporary directory fixture
        
    Returns:
        LocalStorageProvider instance
    """
    return LocalStorageProvider(base_directory=temp_dir)


@pytest.fixture
def sample_file(temp_dir: Path) -> Path:
    """Create a sample file for testing (outside storage directory).
    
    Args:
        temp_dir: Temporary directory fixture
        
    Returns:
        Path to sample file
    """
    # Create in a separate directory to avoid interfering with list tests
    source_dir = temp_dir.parent / "source_files"
    source_dir.mkdir(exist_ok=True)
    file_path = source_dir / "sample.txt"
    file_path.write_text("Sample content for testing")
    return file_path


@pytest.fixture
def sample_image(temp_dir: Path) -> Path:
    """Create a sample image file for testing (outside storage directory).
    
    Args:
        temp_dir: Temporary directory fixture
        
    Returns:
        Path to sample image file
    """
    # Create in a separate directory to avoid interfering with list tests
    source_dir = temp_dir.parent / "source_files"
    source_dir.mkdir(exist_ok=True)
    # Create a minimal valid PNG file (1x1 transparent pixel)
    png_data = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
        b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    file_path = source_dir / "sample.png"
    file_path.write_bytes(png_data)
    return file_path


# ============================================================================
# LocalStorageProvider Tests
# ============================================================================

class TestLocalStorageProviderInit:
    """Test LocalStorageProvider initialization."""
    
    def test_init_with_custom_directory(self, temp_dir: Path):
        """Test initialization with custom directory."""
        provider = LocalStorageProvider(base_directory=temp_dir)
        assert provider.base_directory == temp_dir
        assert provider.base_directory.exists()
        assert provider.base_directory.is_dir()
    
    def test_init_with_none_uses_platformdirs(self):
        """Test initialization with None uses platformdirs."""
        provider = LocalStorageProvider(base_directory=None)
        assert provider.base_directory.exists()
        assert "pixcrawler" in str(provider.base_directory).lower()
    
    def test_init_creates_directory_if_not_exists(self, temp_dir: Path):
        """Test initialization creates directory if it doesn't exist."""
        new_dir = temp_dir / "new_storage"
        assert not new_dir.exists()
        
        provider = LocalStorageProvider(base_directory=new_dir)
        assert new_dir.exists()
        assert new_dir.is_dir()
    
    def test_init_with_string_path(self, temp_dir: Path):
        """Test initialization with string path."""
        provider = LocalStorageProvider(base_directory=str(temp_dir))
        assert provider.base_directory == temp_dir


class TestLocalStorageProviderUpload:
    """Test LocalStorageProvider upload operations."""
    
    def test_upload_file_success(self, local_storage: LocalStorageProvider, sample_file: Path):
        """Test successful file upload."""
        destination = "uploads/test.txt"
        local_storage.upload(sample_file, destination)
        
        uploaded_file = local_storage.base_directory / destination
        assert uploaded_file.exists()
        assert uploaded_file.read_text() == "Sample content for testing"
    
    def test_upload_creates_subdirectories(self, local_storage: LocalStorageProvider, sample_file: Path):
        """Test upload creates nested subdirectories."""
        destination = "level1/level2/level3/test.txt"
        local_storage.upload(sample_file, destination)
        
        uploaded_file = local_storage.base_directory / destination
        assert uploaded_file.exists()
        assert uploaded_file.parent.exists()
    
    def test_upload_overwrites_existing_file(self, local_storage: LocalStorageProvider, sample_file: Path):
        """Test upload overwrites existing file."""
        destination = "test.txt"
        
        # First upload
        local_storage.upload(sample_file, destination)
        
        # Modify source file
        sample_file.write_text("Updated content")
        
        # Second upload (should overwrite)
        local_storage.upload(sample_file, destination)
        
        uploaded_file = local_storage.base_directory / destination
        assert uploaded_file.read_text() == "Updated content"
    
    def test_upload_preserves_file_metadata(self, local_storage: LocalStorageProvider, sample_file: Path):
        """Test upload preserves file metadata (using copy2)."""
        destination = "test.txt"
        original_mtime = sample_file.stat().st_mtime
        
        local_storage.upload(sample_file, destination)
        
        uploaded_file = local_storage.base_directory / destination
        uploaded_mtime = uploaded_file.stat().st_mtime
        
        # Modification times should be very close (within 1 second)
        assert abs(uploaded_mtime - original_mtime) < 1
    
    def test_upload_nonexistent_file_raises_error(self, local_storage: LocalStorageProvider):
        """Test upload with nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Source file not found"):
            local_storage.upload("nonexistent.txt", "destination.txt")
    
    def test_upload_directory_raises_error(self, local_storage: LocalStorageProvider, temp_dir: Path):
        """Test upload with directory raises ValueError."""
        directory = temp_dir / "test_dir"
        directory.mkdir()
        
        with pytest.raises(ValueError, match="Source path is not a file"):
            local_storage.upload(directory, "destination.txt")
    
    def test_upload_with_path_object(self, local_storage: LocalStorageProvider, sample_file: Path):
        """Test upload with Path object."""
        destination = "test.txt"
        local_storage.upload(sample_file, destination)
        
        uploaded_file = local_storage.base_directory / destination
        assert uploaded_file.exists()
    
    def test_upload_image_file(self, local_storage: LocalStorageProvider, sample_image: Path):
        """Test upload of binary image file."""
        destination = "images/test.png"
        local_storage.upload(sample_image, destination)
        
        uploaded_file = local_storage.base_directory / destination
        assert uploaded_file.exists()
        assert uploaded_file.read_bytes() == sample_image.read_bytes()


class TestLocalStorageProviderDownload:
    """Test LocalStorageProvider download operations."""
    
    def test_download_file_success(self, local_storage: LocalStorageProvider, sample_file: Path, temp_dir: Path):
        """Test successful file download."""
        # Upload file first
        storage_path = "test.txt"
        local_storage.upload(sample_file, storage_path)
        
        # Download to different location
        download_path = temp_dir / "downloaded.txt"
        local_storage.download(storage_path, download_path)
        
        assert download_path.exists()
        assert download_path.read_text() == "Sample content for testing"
    
    def test_download_creates_destination_directory(self, local_storage: LocalStorageProvider, sample_file: Path, temp_dir: Path):
        """Test download creates destination directory if needed."""
        # Upload file first
        storage_path = "test.txt"
        local_storage.upload(sample_file, storage_path)
        
        # Download to nested directory
        download_path = temp_dir / "nested" / "dir" / "file.txt"
        local_storage.download(storage_path, download_path)
        
        assert download_path.exists()
        assert download_path.parent.exists()
    
    def test_download_nonexistent_file_raises_error(self, local_storage: LocalStorageProvider, temp_dir: Path):
        """Test download of nonexistent file raises FileNotFoundError."""
        download_path = temp_dir / "downloaded.txt"
        
        with pytest.raises(FileNotFoundError, match="File not found in storage"):
            local_storage.download("nonexistent.txt", download_path)
    
    def test_download_overwrites_existing_file(self, local_storage: LocalStorageProvider, sample_file: Path, temp_dir: Path):
        """Test download overwrites existing destination file."""
        # Upload file
        storage_path = "test.txt"
        local_storage.upload(sample_file, storage_path)
        
        # Create existing file at destination
        download_path = temp_dir / "existing.txt"
        download_path.write_text("Old content")
        
        # Download (should overwrite)
        local_storage.download(storage_path, download_path)
        
        assert download_path.read_text() == "Sample content for testing"
    
    def test_download_with_path_object(self, local_storage: LocalStorageProvider, sample_file: Path, temp_dir: Path):
        """Test download with Path object."""
        storage_path = "test.txt"
        local_storage.upload(sample_file, storage_path)
        
        download_path = temp_dir / "downloaded.txt"
        local_storage.download(storage_path, download_path)
        
        assert download_path.exists()


class TestLocalStorageProviderDelete:
    """Test LocalStorageProvider delete operations."""
    
    def test_delete_file_success(self, local_storage: LocalStorageProvider, sample_file: Path):
        """Test successful file deletion."""
        storage_path = "test.txt"
        local_storage.upload(sample_file, storage_path)
        
        full_path = local_storage.base_directory / storage_path
        assert full_path.exists()
        
        local_storage.delete(storage_path)
        assert not full_path.exists()
    
    def test_delete_nonexistent_file_raises_error(self, local_storage: LocalStorageProvider):
        """Test delete of nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            local_storage.delete("nonexistent.txt")
    
    def test_delete_file_in_subdirectory(self, local_storage: LocalStorageProvider, sample_file: Path):
        """Test deletion of file in subdirectory."""
        storage_path = "subdir/nested/test.txt"
        local_storage.upload(sample_file, storage_path)
        
        local_storage.delete(storage_path)
        
        full_path = local_storage.base_directory / storage_path
        assert not full_path.exists()
    
    def test_delete_does_not_remove_parent_directories(self, local_storage: LocalStorageProvider, sample_file: Path):
        """Test delete only removes file, not parent directories."""
        storage_path = "subdir/test.txt"
        local_storage.upload(sample_file, storage_path)
        
        local_storage.delete(storage_path)
        
        parent_dir = local_storage.base_directory / "subdir"
        assert parent_dir.exists()  # Parent directory should still exist


class TestLocalStorageProviderListFiles:
    """Test LocalStorageProvider list_files operations."""
    
    def test_list_files_empty_storage(self, local_storage: LocalStorageProvider):
        """Test list_files on empty storage."""
        files = local_storage.list_files()
        assert files == []
    
    def test_list_files_returns_all_files(self, local_storage: LocalStorageProvider, sample_file: Path):
        """Test list_files returns all files."""
        # Upload multiple files
        local_storage.upload(sample_file, "file1.txt")
        local_storage.upload(sample_file, "file2.txt")
        local_storage.upload(sample_file, "subdir/file3.txt")
        
        files = local_storage.list_files()
        assert len(files) == 3
        assert "file1.txt" in files
        assert "file2.txt" in files
        assert "subdir/file3.txt" in files
    
    def test_list_files_with_prefix_filter(self, local_storage: LocalStorageProvider, sample_file: Path):
        """Test list_files with prefix filter."""
        # Upload files with different prefixes
        local_storage.upload(sample_file, "images/photo1.jpg")
        local_storage.upload(sample_file, "images/photo2.jpg")
        local_storage.upload(sample_file, "documents/doc1.pdf")
        
        # List only images
        image_files = local_storage.list_files(prefix="images/")
        assert len(image_files) == 2
        assert all(f.startswith("images/") for f in image_files)
    
    def test_list_files_returns_sorted_results(self, local_storage: LocalStorageProvider, sample_file: Path):
        """Test list_files returns sorted results."""
        # Upload files in random order
        local_storage.upload(sample_file, "c.txt")
        local_storage.upload(sample_file, "a.txt")
        local_storage.upload(sample_file, "b.txt")
        
        files = local_storage.list_files()
        assert files == ["a.txt", "b.txt", "c.txt"]
    
    def test_list_files_uses_forward_slashes(self, local_storage: LocalStorageProvider, sample_file: Path):
        """Test list_files uses forward slashes regardless of OS."""
        local_storage.upload(sample_file, "subdir/nested/file.txt")
        
        files = local_storage.list_files()
        assert "subdir/nested/file.txt" in files
        assert "\\" not in files[0]  # No backslashes
    
    def test_list_files_excludes_directories(self, local_storage: LocalStorageProvider, sample_file: Path):
        """Test list_files only returns files, not directories."""
        local_storage.upload(sample_file, "dir1/file.txt")
        
        # Create empty directory
        empty_dir = local_storage.base_directory / "empty_dir"
        empty_dir.mkdir()
        
        files = local_storage.list_files()
        assert len(files) == 1
        assert "dir1/file.txt" in files


class TestLocalStorageProviderPresignedURL:
    """Test LocalStorageProvider presigned URL generation."""
    
    def test_generate_presigned_url_success(self, local_storage: LocalStorageProvider, sample_file: Path):
        """Test successful presigned URL generation."""
        storage_path = "test.txt"
        local_storage.upload(sample_file, storage_path)
        
        url = local_storage.generate_presigned_url(storage_path)
        
        assert url.startswith("file://")
        assert "expires_at=" in url
        # URL-encoded path should contain the file
        assert "test.txt" in url
    
    def test_generate_presigned_url_with_custom_expiry(self, local_storage: LocalStorageProvider, sample_file: Path):
        """Test presigned URL with custom expiration time."""
        storage_path = "test.txt"
        local_storage.upload(sample_file, storage_path)
        
        expires_in = 7200  # 2 hours
        url = local_storage.generate_presigned_url(storage_path, expires_in=expires_in)
        
        # Extract expires_at from URL
        expires_at = int(url.split("expires_at=")[1])
        current_time = int(time.time())
        
        # Check expiration is approximately correct (within 5 seconds)
        assert abs((expires_at - current_time) - expires_in) < 5
    
    def test_generate_presigned_url_nonexistent_file_raises_error(self, local_storage: LocalStorageProvider):
        """Test presigned URL for nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            local_storage.generate_presigned_url("nonexistent.txt")
    
    def test_generate_presigned_url_encodes_special_characters(self, local_storage: LocalStorageProvider, sample_file: Path):
        """Test presigned URL properly encodes special characters."""
        storage_path = "files/test file with spaces.txt"
        local_storage.upload(sample_file, storage_path)
        
        url = local_storage.generate_presigned_url(storage_path)
        
        # URL should be properly encoded
        assert "%20" in url or "+" in url  # Space encoding


class TestLocalStorageProviderSecurity:
    """Test LocalStorageProvider security features."""
    
    def test_path_traversal_prevention_upload(self, local_storage: LocalStorageProvider, sample_file: Path):
        """Test prevention of directory traversal in upload."""
        with pytest.raises(IOError, match="Upload failed.*directory traversal detected"):
            local_storage.upload(sample_file, "../../../etc/passwd")
    
    def test_path_traversal_prevention_download(self, local_storage: LocalStorageProvider, temp_dir: Path):
        """Test prevention of directory traversal in download."""
        download_path = temp_dir / "downloaded.txt"
        
        with pytest.raises(IOError, match="Download failed.*directory traversal detected"):
            local_storage.download("../../../etc/passwd", download_path)
    
    def test_path_traversal_prevention_delete(self, local_storage: LocalStorageProvider):
        """Test prevention of directory traversal in delete."""
        with pytest.raises(IOError, match="Deletion failed.*directory traversal detected"):
            local_storage.delete("../../../etc/passwd")
    
    def test_path_traversal_prevention_list(self, local_storage: LocalStorageProvider):
        """Test list_files with traversal prefix still works safely."""
        # This should not raise error but should return empty list
        files = local_storage.list_files(prefix="../")
        assert files == []
    
    def test_absolute_path_rejection(self, local_storage: LocalStorageProvider, sample_file: Path):
        """Test rejection of absolute paths."""
        with pytest.raises(IOError, match="Upload failed.*directory traversal detected"):
            local_storage.upload(sample_file, "/absolute/path/file.txt")


class TestLocalStorageProviderErrorHandling:
    """Test LocalStorageProvider error handling."""
    
    def test_upload_io_error_handling(self, local_storage: LocalStorageProvider, sample_file: Path):
        """Test upload handles IO errors gracefully."""
        # Make destination path read-only (simulate permission error)
        destination = "readonly/test.txt"
        readonly_dir = local_storage.base_directory / "readonly"
        readonly_dir.mkdir()
        
        # Make directory read-only on Unix systems
        if os.name != 'nt':  # Skip on Windows
            readonly_dir.chmod(0o444)
            
            with pytest.raises(IOError, match="Upload failed"):
                local_storage.upload(sample_file, destination)
            
            # Restore permissions for cleanup
            readonly_dir.chmod(0o755)
    
    def test_download_io_error_propagation(self, local_storage: LocalStorageProvider, temp_dir: Path):
        """Test download propagates IO errors."""
        with pytest.raises(FileNotFoundError):
            local_storage.download("nonexistent.txt", temp_dir / "output.txt")
    
    def test_delete_io_error_propagation(self, local_storage: LocalStorageProvider):
        """Test delete propagates IO errors."""
        with pytest.raises(FileNotFoundError):
            local_storage.delete("nonexistent.txt")


# ============================================================================
# StorageSettings Tests
# ============================================================================

class TestStorageSettings:
    """Test StorageSettings configuration."""
    
    def test_default_settings(self):
        """Test default settings values."""
        settings = StorageSettings()
        assert settings.storage_provider == "local"
        assert settings.local_storage_path is None
        assert settings.azure_container_name == "pixcrawler-storage"
        assert settings.azure_max_retries == 3
        assert settings.azure_enable_archive_tier is True
        assert settings.azure_default_tier == "hot"
    
    def test_local_provider_validation(self):
        """Test local provider validation."""
        settings = StorageSettings(storage_provider="local")
        assert settings.storage_provider == "local"
    
    def test_azure_provider_validation(self):
        """Test Azure provider validation."""
        settings = StorageSettings(
            storage_provider="azure",
            azure_connection_string="DefaultEndpointsProtocol=https;AccountName=test;AccountKey=test123"
        )
        assert settings.storage_provider == "azure"
    
    def test_invalid_provider_raises_error(self):
        """Test invalid provider raises validation error."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError, match="string_pattern_mismatch"):
            StorageSettings(storage_provider="invalid")
    
    def test_azure_requires_connection_string(self):
        """Test Azure provider requires connection string."""
        with pytest.raises(ValueError, match="azure_connection_string is required"):
            StorageSettings(storage_provider="azure")
    
    def test_azure_container_name_validation(self):
        """Test Azure container name validation."""
        # Valid names
        StorageSettings(
            storage_provider="local",
            azure_container_name="valid-container-123"
        )
        
        # Invalid name (uppercase)
        with pytest.raises(ValueError):
            StorageSettings(
                storage_provider="local",
                azure_container_name="Invalid-Container"
            )
    
    def test_tier_validation(self):
        """Test tier validation."""
        # Valid tiers
        for tier in ["hot", "cool", "archive"]:
            settings = StorageSettings(
                storage_provider="local",
                azure_default_tier=tier
            )
            assert settings.azure_default_tier == tier
        
        # Invalid tier
        from pydantic import ValidationError
        with pytest.raises(ValidationError, match="string_pattern_mismatch"):
            StorageSettings(
                storage_provider="local",
                azure_default_tier="invalid"
            )
    
    def test_rehydrate_priority_validation(self):
        """Test rehydration priority validation."""
        # Valid priorities
        for priority in ["standard", "high"]:
            settings = StorageSettings(
                storage_provider="local",
                azure_rehydrate_priority=priority
            )
            assert settings.azure_rehydrate_priority == priority
        
        # Invalid priority
        from pydantic import ValidationError
        with pytest.raises(ValidationError, match="string_pattern_mismatch"):
            StorageSettings(
                storage_provider="local",
                azure_rehydrate_priority="invalid"
            )
    
    def test_lifecycle_days_validation(self):
        """Test lifecycle days validation."""
        # Valid: archive > cool
        settings = StorageSettings(
            storage_provider="local",
            azure_lifecycle_cool_after_days=30,
            azure_lifecycle_archive_after_days=90
        )
        assert settings.azure_lifecycle_cool_after_days == 30
        assert settings.azure_lifecycle_archive_after_days == 90
        
        # Invalid: archive <= cool
        with pytest.raises(ValueError, match="archive_after_days must be greater"):
            StorageSettings(
                storage_provider="local",
                azure_lifecycle_cool_after_days=90,
                azure_lifecycle_archive_after_days=30
            )
    
    def test_local_path_normalization(self):
        """Test local storage path normalization."""
        settings = StorageSettings(
            storage_provider="local",
            local_storage_path="./relative/path"
        )
        # Path should be converted to absolute
        assert Path(settings.local_storage_path).is_absolute()


# ============================================================================
# Integration-like Tests (Multiple Operations)
# ============================================================================

class TestStorageWorkflows:
    """Test complete storage workflows."""
    
    def test_upload_download_delete_workflow(self, local_storage: LocalStorageProvider, sample_file: Path, temp_dir: Path):
        """Test complete upload -> download -> delete workflow."""
        storage_path = "workflow/test.txt"
        download_path = temp_dir / "downloaded.txt"
        
        # Upload
        local_storage.upload(sample_file, storage_path)
        assert (local_storage.base_directory / storage_path).exists()
        
        # Download
        local_storage.download(storage_path, download_path)
        assert download_path.exists()
        assert download_path.read_text() == sample_file.read_text()
        
        # Delete
        local_storage.delete(storage_path)
        assert not (local_storage.base_directory / storage_path).exists()
    
    def test_multiple_file_operations(self, local_storage: LocalStorageProvider, sample_file: Path):
        """Test operations with multiple files."""
        files = ["file1.txt", "file2.txt", "file3.txt"]
        
        # Upload multiple files
        for file_path in files:
            local_storage.upload(sample_file, file_path)
        
        # List all files
        listed_files = local_storage.list_files()
        assert len(listed_files) == 3
        assert set(listed_files) == set(files)
        
        # Delete one file
        local_storage.delete("file2.txt")
        
        # Verify remaining files
        remaining_files = local_storage.list_files()
        assert len(remaining_files) == 2
        assert "file2.txt" not in remaining_files
    
    def test_nested_directory_operations(self, local_storage: LocalStorageProvider, sample_file: Path):
        """Test operations with nested directory structure."""
        files = [
            "level1/file1.txt",
            "level1/level2/file2.txt",
            "level1/level2/level3/file3.txt"
        ]
        
        # Upload files
        for file_path in files:
            local_storage.upload(sample_file, file_path)
        
        # Verify all uploaded
        all_files = local_storage.list_files()
        assert len(all_files) == 3
        
        # List with prefix
        level2_files = local_storage.list_files(prefix="level1/level2/")
        assert len(level2_files) == 2
        
        # Delete nested file
        local_storage.delete("level1/level2/level3/file3.txt")
        
        # Verify remaining files
        remaining_files = local_storage.list_files()
        assert len(remaining_files) == 2
        assert "level1/file1.txt" in remaining_files
        assert "level1/level2/file2.txt" in remaining_files
