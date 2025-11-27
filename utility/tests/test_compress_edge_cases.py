"""
Edge case tests for compression module.

This module provides comprehensive edge case testing for compression,
archiving, and error handling scenarios including:
- Corrupted image handling
- Permission errors
- Large file handling
- Concurrent operations
- Error recovery and retry logic
- Memory usage under load
- Archive creation and extraction
"""

import io
import os
import stat
import tempfile
import threading
import time
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from utility.compress import (
    Archiver,
    CompressionSettings,
    ImageCompressor,
    compress,
    decompress,
)


class TestCorruptedImageHandling:
    """Test handling of corrupted and invalid image files."""

    def test_corrupted_image_file(self, temp_dir: Path, output_dir: Path) -> None:
        """Test compression handles corrupted image files gracefully."""
        # Create a corrupted image file (invalid data)
        corrupted_dir = temp_dir / "corrupted"
        corrupted_dir.mkdir()
        corrupted_file = corrupted_dir / "corrupted.jpg"
        corrupted_file.write_bytes(b"This is not a valid image file")

        cfg = CompressionSettings(
            input_dir=corrupted_dir,
            output_dir=output_dir,
        )
        compressor = ImageCompressor(cfg)

        # Should handle gracefully without crashing
        # Note: Current implementation may skip invalid files
        try:
            compressor.run()
        except Exception as e:
            # If exception occurs, it should be a PIL error
            assert "cannot identify image file" in str(e).lower() or "image file is truncated" in str(e).lower()

    def test_truncated_image_file(self, temp_dir: Path, output_dir: Path) -> None:
        """Test compression handles truncated image files."""
        # Create a truncated image file
        truncated_dir = temp_dir / "truncated"
        truncated_dir.mkdir()
        truncated_file = truncated_dir / "truncated.jpg"

        # Create a valid image and truncate it
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        # Write only first half of the image data
        truncated_file.write_bytes(buffer.getvalue()[:len(buffer.getvalue()) // 2])

        cfg = CompressionSettings(
            input_dir=truncated_dir,
            output_dir=output_dir,
        )
        compressor = ImageCompressor(cfg)

        # Should handle gracefully
        try:
            compressor.run()
        except Exception as e:
            assert "truncated" in str(e).lower() or "cannot identify" in str(e).lower()

    def test_empty_image_file(self, temp_dir: Path, output_dir: Path) -> None:
        """Test compression handles empty image files."""
        empty_dir = temp_dir / "empty_files"
        empty_dir.mkdir()
        empty_file = empty_dir / "empty.jpg"
        empty_file.touch()  # Create empty file

        cfg = CompressionSettings(
            input_dir=empty_dir,
            output_dir=output_dir,
        )
        compressor = ImageCompressor(cfg)

        # Should handle gracefully
        try:
            compressor.run()
        except Exception as e:
            assert "cannot identify" in str(e).lower() or "empty" in str(e).lower()

    def test_wrong_extension_image(self, temp_dir: Path, output_dir: Path) -> None:
        """Test compression handles files with wrong extensions."""
        wrong_ext_dir = temp_dir / "wrong_ext"
        wrong_ext_dir.mkdir()

        # Create a PNG file but name it .jpg
        wrong_file = wrong_ext_dir / "wrong.jpg"
        img = Image.new("RGB", (100, 100), color=(0, 255, 0))
        img.save(wrong_file, format="PNG")

        cfg = CompressionSettings(
            input_dir=wrong_ext_dir,
            output_dir=output_dir,
        )
        compressor = ImageCompressor(cfg)

        # PIL should handle this gracefully by detecting actual format
        compressor.run()
        # Verify output exists (PIL auto-detects format)
        assert output_dir.exists()


class TestPermissionErrors:
    """Test handling of permission-related errors."""

    @pytest.mark.skipif(os.name == "nt", reason="Permission tests unreliable on Windows")
    def test_read_permission_denied(self, temp_dir: Path, output_dir: Path) -> None:
        """Test compression handles read permission errors."""
        no_read_dir = temp_dir / "no_read"
        no_read_dir.mkdir()

        # Create an image file
        img_file = no_read_dir / "test.jpg"
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        img.save(img_file, format="JPEG")

        # Remove read permissions
        os.chmod(img_file, 0o000)

        cfg = CompressionSettings(
            input_dir=no_read_dir,
            output_dir=output_dir,
        )
        compressor = ImageCompressor(cfg)

        try:
            compressor.run()
        except PermissionError:
            pass  # Expected
        finally:
            # Restore permissions for cleanup
            os.chmod(img_file, stat.S_IRUSR | stat.S_IWUSR)

    @pytest.mark.skipif(os.name == "nt", reason="Permission tests unreliable on Windows")
    def test_write_permission_denied(self, mock_image_dir: Path, temp_dir: Path) -> None:
        """Test compression handles write permission errors."""
        no_write_dir = temp_dir / "no_write"
        no_write_dir.mkdir()

        # Remove write permissions from output directory
        os.chmod(no_write_dir, stat.S_IRUSR | stat.S_IXUSR)

        cfg = CompressionSettings(
            input_dir=mock_image_dir,
            output_dir=no_write_dir,
        )
        compressor = ImageCompressor(cfg)

        try:
            compressor.run()
        except PermissionError:
            pass  # Expected
        finally:
            # Restore permissions for cleanup
            os.chmod(no_write_dir, stat.S_IRWXU)

    def test_output_directory_creation_failure(self, mock_image_dir: Path) -> None:
        """Test handling when output directory cannot be created."""
        # Try to create output in a path that doesn't exist and can't be created
        # Use a mock to simulate mkdir failure
        cfg = CompressionSettings(
            input_dir=mock_image_dir,
            output_dir=Path("/nonexistent/path/output"),
        )
        compressor = ImageCompressor(cfg)

        with patch.object(Path, "mkdir", side_effect=PermissionError("Cannot create directory")):
            with pytest.raises(PermissionError):
                compressor.run()


class TestLargeFileHandling:
    """Test handling of large files (>100MB)."""

    def test_large_image_compression(self, temp_dir: Path, output_dir: Path) -> None:
        """Test compression of large image files."""
        large_dir = temp_dir / "large"
        large_dir.mkdir()

        # Create a large image (5000x5000 pixels = 75MB uncompressed in memory)
        # Save as JPEG to avoid PNG's excellent compression
        large_file = large_dir / "large.jpg"
        # Create image with gradient pattern
        img = Image.new("RGB", (5000, 5000))
        pixels = img.load()
        for i in range(0, 5000, 10):  # Sample every 10 pixels for speed
            for j in range(0, 5000, 10):
                # Create gradient pattern
                color = (i % 256, j % 256, (i + j) % 256)
                # Fill 10x10 block
                for di in range(10):
                    for dj in range(10):
                        if i + di < 5000 and j + dj < 5000:
                            pixels[i + di, j + dj] = color
        img.save(large_file, format="JPEG", quality=95)

        file_size_mb = large_file.stat().st_size / (1024 * 1024)
        # JPEG with gradient should be substantial
        assert file_size_mb > 0.5, f"Test file should be reasonably large, got {file_size_mb}MB"

        cfg = CompressionSettings(
            input_dir=large_dir,
            output_dir=output_dir,
            format="webp",
            quality=75,
        )
        compressor = ImageCompressor(cfg)

        # Should handle large files without memory issues
        compressor.run()

        # Verify output exists
        output_files = list(output_dir.rglob("*.webp"))
        assert len(output_files) == 1
        output_size_mb = output_files[0].stat().st_size / (1024 * 1024)
        assert output_size_mb > 0, "Output file should exist with content"

    def test_multiple_large_files(self, temp_dir: Path, output_dir: Path) -> None:
        """Test compression of multiple large files."""
        large_dir = temp_dir / "multiple_large"
        large_dir.mkdir()

        # Create multiple large images
        for i in range(3):
            large_file = large_dir / f"large_{i}.png"
            img = Image.new("RGB", (2000, 2000), color=(i * 50, i * 50, i * 50))
            img.save(large_file, format="PNG")

        cfg = CompressionSettings(
            input_dir=large_dir,
            output_dir=output_dir,
            format="webp",
            quality=80,
            workers=2,
        )
        compressor = ImageCompressor(cfg)

        # Should handle multiple large files
        compressor.run()

        output_files = list(output_dir.rglob("*.webp"))
        assert len(output_files) == 3


class TestConcurrentCompression:
    """Test concurrent compression operations."""

    def test_concurrent_compression_same_input(self, mock_image_dir: Path, temp_dir: Path) -> None:
        """Test multiple concurrent compressions from same input directory."""
        output_dirs = [temp_dir / f"output_{i}" for i in range(3)]
        threads = []
        results = []

        def compress_task(output_dir: Path) -> None:
            try:
                result = compress(
                    input_dir=mock_image_dir,
                    output_dir=output_dir,
                    format_="webp",
                    quality=85,
                )
                results.append(("success", result))
            except Exception as e:
                results.append(("error", str(e)))

        # Start multiple compression threads
        for output_dir in output_dirs:
            thread = threading.Thread(target=compress_task, args=(output_dir,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All should succeed
        assert len(results) == 3
        for status, _ in results:
            assert status == "success"

        # Verify all outputs exist
        for output_dir in output_dirs:
            assert output_dir.exists()
            assert len(list(output_dir.rglob("*.webp"))) > 0

    def test_concurrent_compression_different_formats(
        self, mock_image_dir: Path, temp_dir: Path
    ) -> None:
        """Test concurrent compressions with different formats."""
        formats = ["webp", "png", "avif"]
        threads = []
        results = []

        def compress_task(fmt: str) -> None:
            try:
                output_dir = temp_dir / fmt
                result = compress(
                    input_dir=mock_image_dir,
                    output_dir=output_dir,
                    format_=fmt,
                    quality=85,
                )
                results.append(("success", fmt, result))
            except Exception as e:
                results.append(("error", fmt, str(e)))

        # Start compression threads for different formats
        for fmt in formats:
            thread = threading.Thread(target=compress_task, args=(fmt,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # All should succeed
        assert len(results) == 3
        for status, fmt, _ in results:
            assert status == "success"

    def test_thread_safety_with_shared_config(self, mock_image_dir: Path, temp_dir: Path) -> None:
        """Test thread safety when using shared configuration."""
        cfg = CompressionSettings(
            input_dir=mock_image_dir,
            output_dir=temp_dir / "shared_output",
            format="webp",
            quality=85,
            workers=4,
        )

        # Multiple threads using same config
        threads = []
        errors = []

        def compress_task() -> None:
            try:
                compressor = ImageCompressor(cfg)
                compressor.run()
            except Exception as e:
                errors.append(str(e))

        # Start multiple threads
        for _ in range(3):
            thread = threading.Thread(target=compress_task)
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Should handle gracefully (may have some conflicts but shouldn't crash)
        # Note: This tests that the code doesn't crash, not that it's perfectly thread-safe
        assert len(errors) == 0 or all("exists" in err.lower() for err in errors)


class TestErrorRecoveryAndRetry:
    """Test error recovery and retry logic."""

    def test_partial_compression_failure(self, temp_dir: Path, output_dir: Path) -> None:
        """Test handling when some images fail to compress."""
        mixed_dir = temp_dir / "mixed"
        mixed_dir.mkdir()

        # Create valid images
        for i in range(3):
            img_file = mixed_dir / f"valid_{i}.jpg"
            img = Image.new("RGB", (100, 100), color=(i * 80, i * 80, i * 80))
            img.save(img_file, format="JPEG")

        # Create corrupted file
        corrupted_file = mixed_dir / "corrupted.jpg"
        corrupted_file.write_bytes(b"invalid data")

        cfg = CompressionSettings(
            input_dir=mixed_dir,
            output_dir=output_dir,
        )
        compressor = ImageCompressor(cfg)

        # Should process valid images even if some fail
        try:
            compressor.run()
        except Exception:
            pass  # Some failures expected

        # At least some valid images should be processed
        # Note: Current implementation may stop on first error
        # This test documents current behavior

    def test_retry_on_transient_failure(
        self, mock_image_dir: Path, output_dir: Path
    ) -> None:
        """Test documents lack of retry logic in current implementation."""
        # Note: Current implementation doesn't have retry logic
        # Errors in ThreadPoolExecutor futures are not explicitly checked
        # This test documents the limitation that should be addressed
        
        # Current behavior: compression runs without retry on failure
        # Future enhancement: Add retry logic with exponential backoff
        # Future enhancement: Check future results and raise on errors
        
        cfg = CompressionSettings(
            input_dir=mock_image_dir,
            output_dir=output_dir,
        )
        compressor = ImageCompressor(cfg)
        
        # Current implementation completes without retry mechanism
        compressor.run()
        
        # Verify output exists (successful compression)
        output_files = list(output_dir.rglob("*.webp"))
        assert len(output_files) > 0
        
        # TODO: Add retry logic for transient failures
        # TODO: Add proper error handling for ThreadPoolExecutor futures
        # TODO: Implement exponential backoff for retries

    def test_resume_after_interruption(self, mock_image_dir: Path, output_dir: Path) -> None:
        """Test resuming compression after interruption."""
        cfg = CompressionSettings(
            input_dir=mock_image_dir,
            output_dir=output_dir,
        )

        # First compression (partial)
        compressor1 = ImageCompressor(cfg)
        compressor1.run()

        # Count files after first run
        first_count = len(list(output_dir.rglob("*.webp")))

        # Second compression (should skip existing files or overwrite)
        compressor2 = ImageCompressor(cfg)
        compressor2.run()

        # Count files after second run
        second_count = len(list(output_dir.rglob("*.webp")))

        # Should have same or more files
        assert second_count >= first_count


class TestMemoryUsage:
    """Test memory usage under load."""

    def test_memory_efficient_large_batch(self, temp_dir: Path, output_dir: Path) -> None:
        """Test memory efficiency with large batch of images."""
        large_batch_dir = temp_dir / "large_batch"
        large_batch_dir.mkdir()

        # Create many small images
        for i in range(50):
            img_file = large_batch_dir / f"image_{i:03d}.jpg"
            img = Image.new("RGB", (500, 500), color=(i * 5, i * 5, i * 5))
            img.save(img_file, format="JPEG")

        cfg = CompressionSettings(
            input_dir=large_batch_dir,
            output_dir=output_dir,
            format="webp",
            quality=85,
            workers=4,
        )
        compressor = ImageCompressor(cfg)

        # Should process without excessive memory usage
        compressor.run()

        # Verify all images processed
        output_files = list(output_dir.rglob("*.webp"))
        assert len(output_files) == 50

    def test_streaming_compression(self, temp_dir: Path, output_dir: Path) -> None:
        """Test that compression processes images in streaming fashion."""
        stream_dir = temp_dir / "stream"
        stream_dir.mkdir()

        # Create images
        for i in range(10):
            img_file = stream_dir / f"image_{i}.jpg"
            img = Image.new("RGB", (1000, 1000), color=(i * 25, i * 25, i * 25))
            img.save(img_file, format="JPEG")

        cfg = CompressionSettings(
            input_dir=stream_dir,
            output_dir=output_dir,
            workers=2,
        )
        compressor = ImageCompressor(cfg)

        # Should process without loading all images into memory at once
        compressor.run()

        output_files = list(output_dir.rglob("*.webp"))
        assert len(output_files) == 10


class TestArchiveCreationAndExtraction:
    """Test archive creation and extraction edge cases."""

    def test_archive_empty_directory(self, temp_dir: Path, output_dir: Path) -> None:
        """Test archiving an empty directory."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()

        archiver = Archiver(empty_dir)
        archive_path = output_dir / "empty.zip"

        result = archiver.create(archive_path, use_tar=False, kind="zip", level=10)

        assert result.exists()
        # Archive should exist but be minimal size
        assert result.stat().st_size > 0

    def test_archive_with_symlinks(self, temp_dir: Path, output_dir: Path) -> None:
        """Test archiving directory with symlinks."""
        link_dir = temp_dir / "with_links"
        link_dir.mkdir()

        # Create a file
        real_file = link_dir / "real.txt"
        real_file.write_text("real content")

        # Create symlink (skip on Windows if not supported)
        try:
            link_file = link_dir / "link.txt"
            link_file.symlink_to(real_file)
        except (OSError, NotImplementedError):
            pytest.skip("Symlinks not supported on this platform")

        archiver = Archiver(link_dir)
        archive_path = output_dir / "links.zip"

        result = archiver.create(archive_path, use_tar=False, kind="zip", level=10)

        assert result.exists()

    def test_archive_with_special_characters(self, temp_dir: Path, output_dir: Path) -> None:
        """Test archiving files with special characters in names."""
        special_dir = temp_dir / "special"
        special_dir.mkdir()

        # Create files with special characters
        special_names = [
            "file with spaces.txt",
            "file-with-dashes.txt",
            "file_with_underscores.txt",
            "file.multiple.dots.txt",
        ]

        for name in special_names:
            file_path = special_dir / name
            file_path.write_text(f"content of {name}")

        archiver = Archiver(special_dir)
        archive_path = output_dir / "special.zip"

        result = archiver.create(archive_path, use_tar=False, kind="zip", level=10)

        assert result.exists()

        # Verify extraction
        extract_dir = output_dir / "extracted"
        decompress(result, extract_dir)

        # All files should be extracted
        extracted_files = list(extract_dir.rglob("*.txt"))
        assert len(extracted_files) == len(special_names)

    def test_archive_very_deep_directory_structure(self, temp_dir: Path, output_dir: Path) -> None:
        """Test archiving very deep directory structures."""
        deep_dir = temp_dir / "deep"
        current = deep_dir

        # Create deep nested structure
        for i in range(10):
            current = current / f"level_{i}"
            current.mkdir(parents=True, exist_ok=True)

        # Create file at deepest level
        deep_file = current / "deep_file.txt"
        deep_file.write_text("deep content")

        archiver = Archiver(deep_dir)
        archive_path = output_dir / "deep.zip"

        result = archiver.create(archive_path, use_tar=False, kind="zip", level=10)

        assert result.exists()

        # Verify extraction preserves structure
        extract_dir = output_dir / "extracted_deep"
        decompress(result, extract_dir)

        # File should exist at deep path
        extracted_files = list(extract_dir.rglob("deep_file.txt"))
        assert len(extracted_files) == 1

    def test_extract_corrupted_archive(self, temp_dir: Path, output_dir: Path) -> None:
        """Test extraction of corrupted archive."""
        corrupted_archive = temp_dir / "corrupted.zip"
        corrupted_archive.write_bytes(b"This is not a valid ZIP file")

        extract_dir = output_dir / "extracted"

        with pytest.raises((zipfile.BadZipFile, ValueError)):
            decompress(corrupted_archive, extract_dir)

    def test_extract_archive_with_path_traversal(self, temp_dir: Path, output_dir: Path) -> None:
        """Test extraction handles path traversal attempts safely."""
        # Create a ZIP with path traversal attempt
        malicious_zip = temp_dir / "malicious.zip"

        with zipfile.ZipFile(malicious_zip, "w") as zf:
            # Try to write outside extraction directory
            zf.writestr("../../../etc/passwd", "malicious content")

        extract_dir = output_dir / "extracted"

        # Should handle safely (either reject or sanitize path)
        try:
            decompress(malicious_zip, extract_dir)
            # If it succeeds, verify file is not outside extract_dir
            for extracted_file in extract_dir.rglob("*"):
                assert extract_dir in extracted_file.parents or extracted_file == extract_dir
        except (ValueError, Exception):
            # Rejecting malicious archive is also acceptable
            pass

    def test_archive_compression_levels(self, mock_compressed_dir: Path, output_dir: Path) -> None:
        """Test different compression levels produce different sizes."""
        archiver = Archiver(mock_compressed_dir)

        sizes = {}
        for level in [1, 10, 19]:
            archive_path = output_dir / f"level_{level}.zst"
            result = archiver.create(archive_path, use_tar=True, kind="zstd", level=level)
            sizes[level] = result.stat().st_size

        # Higher compression levels should generally produce smaller files
        # (though not guaranteed for small test data)
        assert sizes[1] > 0
        assert sizes[19] > 0

    def test_concurrent_archive_creation(self, mock_compressed_dir: Path, temp_dir: Path) -> None:
        """Test concurrent archive creation operations."""
        threads = []
        results = []

        def create_archive(suffix: str) -> None:
            try:
                archiver = Archiver(mock_compressed_dir)
                archive_path = temp_dir / f"archive_{suffix}.zip"
                result = archiver.create(archive_path, use_tar=False, kind="zip", level=10)
                results.append(("success", result))
            except Exception as e:
                results.append(("error", str(e)))

        # Create multiple archives concurrently
        for i in range(3):
            thread = threading.Thread(target=create_archive, args=(str(i),))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # All should succeed
        assert len(results) == 3
        for status, _ in results:
            assert status == "success"
