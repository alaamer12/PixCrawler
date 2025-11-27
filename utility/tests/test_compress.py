"""
Comprehensive tests for the compress module.

This module provides full test coverage for compression, archiving,
and decompression functionality with mocked data.
"""

import tarfile
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from utility.compress import (
    Archiver,
    ArchiveSettings,
    CompressionSettings,
    ImageCompressor,
    compress,
    decompress,
    get_compression_settings,
)


class TestCompressionSettings:
    """Test CompressionSettings configuration."""

    def test_default_settings(self) -> None:
        """Test default configuration values."""
        settings = CompressionSettings()

        assert settings.input_dir == Path("./images")
        assert settings.output_dir == Path("./compressed")
        assert settings.format == "webp"
        assert settings.quality == 85
        assert settings.lossless is False
        assert settings.workers == 0

    def test_archive_composition(self) -> None:
        """Test nested ArchiveSettings composition."""
        settings = CompressionSettings()

        assert isinstance(settings.archive, ArchiveSettings)
        assert settings.archive.enable is True
        assert settings.archive.type == "zstd"
        assert settings.archive.level == 10

    def test_quality_validation(self) -> None:
        """Test quality parameter validation."""
        # Valid quality
        settings = CompressionSettings(quality=90)
        assert settings.quality == 90

        # Invalid quality should raise error (Pydantic V2 ValidationError)
        from pydantic import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            CompressionSettings(quality=150)
        assert "quality" in str(exc_info.value).lower()
        assert "less than or equal to 100" in str(exc_info.value).lower()

    def test_resolved_workers(self) -> None:
        """Test worker count resolution."""
        # Auto-detect (0)
        settings = CompressionSettings(workers=0)
        assert settings.resolved_workers >= 1

        # Explicit worker count
        settings = CompressionSettings(workers=4)
        assert settings.resolved_workers == 4

    def test_cached_settings(self) -> None:
        """Test settings caching."""
        settings1 = get_compression_settings()
        settings2 = get_compression_settings()

        # Should return same cached instance
        assert settings1 is settings2


class TestArchiveSettings:
    """Test ArchiveSettings configuration."""

    def test_default_archive_settings(self) -> None:
        """Test default archive configuration."""
        settings = ArchiveSettings()

        assert settings.enable is True
        assert settings.tar is True
        assert settings.type == "zstd"
        assert settings.level == 10
        assert settings.output == Path("./dataset.zst")

    def test_compression_level_validation(self) -> None:
        """Test compression level validation."""
        # Valid level
        settings = ArchiveSettings(level=15)
        assert settings.level == 15

        # Invalid level should raise error (Pydantic V2 ValidationError)
        from pydantic import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            ArchiveSettings(level=25)
        assert "level" in str(exc_info.value).lower()
        assert "less than or equal to 19" in str(exc_info.value).lower()


class TestImageCompressor:
    """Test ImageCompressor class."""

    def test_compressor_initialization(self, mock_image_dir: Path, output_dir: Path) -> None:
        """Test compressor initialization."""
        cfg = CompressionSettings(
            input_dir=mock_image_dir,
            output_dir=output_dir,
        )
        compressor = ImageCompressor(cfg)

        assert compressor.cfg == cfg

    def test_compress_images(self, mock_image_dir: Path, output_dir: Path) -> None:
        """Test batch image compression."""
        cfg = CompressionSettings(
            input_dir=mock_image_dir,
            output_dir=output_dir,
            format="webp",
            quality=85,
        )
        compressor = ImageCompressor(cfg)
        compressor.run()

        # Check output directory exists
        assert output_dir.exists()

        # Check images were compressed
        output_files = list(output_dir.rglob("*.webp"))
        assert len(output_files) > 0

    def test_compress_with_subdirectories(self, mock_image_dir: Path, output_dir: Path) -> None:
        """Test compression preserves directory structure."""
        cfg = CompressionSettings(
            input_dir=mock_image_dir,
            output_dir=output_dir,
        )
        compressor = ImageCompressor(cfg)
        compressor.run()

        # Check subdirectory structure is preserved
        subdir = output_dir / "subdir"
        assert subdir.exists()
        assert len(list(subdir.glob("*.webp"))) > 0

    def test_compress_empty_directory(self, temp_dir: Path, output_dir: Path) -> None:
        """Test compression with no images."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()

        cfg = CompressionSettings(
            input_dir=empty_dir,
            output_dir=output_dir,
        )
        compressor = ImageCompressor(cfg)
        compressor.run()

        # Should handle gracefully
        assert output_dir.exists()


class TestArchiver:
    """Test Archiver class."""

    def test_archiver_initialization(self, mock_compressed_dir: Path) -> None:
        """Test archiver initialization."""
        archiver = Archiver(mock_compressed_dir)
        assert archiver.root == mock_compressed_dir

    def test_create_zip_archive(self, mock_compressed_dir: Path, output_dir: Path) -> None:
        """Test ZIP archive creation."""
        archiver = Archiver(mock_compressed_dir)
        archive_path = output_dir / "test.zip"

        result = archiver.create(archive_path, use_tar=False, kind="zip", level=10)

        assert result.exists()
        assert result.suffix == ".zip"

        # Verify archive contents
        with zipfile.ZipFile(result, "r") as zf:
            assert len(zf.namelist()) > 0

    def test_create_zstd_archive(self, mock_compressed_dir: Path, output_dir: Path) -> None:
        """Test Zstandard archive creation."""
        archiver = Archiver(mock_compressed_dir)
        archive_path = output_dir / "test.zst"

        result = archiver.create(archive_path, use_tar=True, kind="zstd", level=10)

        assert result.exists()
        assert result.suffix == ".zst"
        assert result.stat().st_size > 0

    def test_create_tar_archive(self, mock_compressed_dir: Path, output_dir: Path) -> None:
        """Test tar archive creation."""
        archiver = Archiver(mock_compressed_dir)
        archive_path = output_dir / "test.tar"

        result = archiver.create(archive_path, use_tar=True, kind="tar", level=10)

        assert result.exists()


class TestCompressFunction:
    """Test high-level compress() function."""

    def test_simple_compression(self, mock_image_dir: Path, output_dir: Path) -> None:
        """Test simple compression without archiving."""
        result = compress(
            input_dir=mock_image_dir,
            output_dir=output_dir,
            format_="webp",
            quality=85,
        )

        assert result == output_dir
        assert output_dir.exists()
        assert len(list(output_dir.rglob("*.webp"))) > 0

    def test_compression_with_archive(self, mock_image_dir: Path, output_dir: Path) -> None:
        """Test compression with archiving."""
        archive_output = output_dir / "dataset.zst"

        result = compress(
            input_dir=mock_image_dir,
            output_dir=output_dir / "compressed",
            format_="webp",
            quality=90,
            archive=True,
            archive_output=archive_output,
        )

        assert result == archive_output
        assert archive_output.exists()
        assert archive_output.suffix == ".zst"

    def test_compression_lossless(self, mock_image_dir: Path, output_dir: Path) -> None:
        """Test lossless compression."""
        result = compress(
            input_dir=mock_image_dir,
            output_dir=output_dir,
            format_="png",
            lossless=True,
        )

        assert result == output_dir
        assert len(list(output_dir.rglob("*.png"))) > 0

    def test_compression_different_formats(self, mock_image_dir: Path, output_dir: Path) -> None:
        """Test compression with different formats."""
        formats = ["webp", "png", "avif"]

        for fmt in formats:
            out = output_dir / fmt
            result = compress(
                input_dir=mock_image_dir,
                output_dir=out,
                format_=fmt,
            )

            assert result == out
            assert out.exists()

    @patch("builtins.print")
    def test_compression_debug_mode(
        self, mock_print: MagicMock, mock_image_dir: Path, output_dir: Path
    ) -> None:
        """Test compression with debug output."""
        compress(
            input_dir=mock_image_dir,
            output_dir=output_dir,
            debug=True,
        )

        # Verify debug output was printed
        assert mock_print.called
        print_calls = [str(call) for call in mock_print.call_args_list]
        debug_output = "".join(print_calls)

        assert "COMPRESSION DEBUG INFO" in debug_output
        assert "COMPRESSION RESULTS" in debug_output
        assert "Input Files:" in debug_output
        assert "Compression Ratio:" in debug_output

    @patch("builtins.print")
    def test_compression_debug_with_archive(
        self, mock_print: MagicMock, mock_image_dir: Path, output_dir: Path
    ) -> None:
        """Test compression with debug and archiving."""
        compress(
            input_dir=mock_image_dir,
            output_dir=output_dir / "compressed",
            archive=True,
            debug=True,
        )

        print_calls = [str(call) for call in mock_print.call_args_list]
        debug_output = "".join(print_calls)

        assert "ARCHIVE RESULTS" in debug_output
        assert "Total Compression:" in debug_output


class TestDecompressFunction:
    """Test high-level decompress() function."""

    def test_decompress_zip(self, mock_compressed_dir: Path, output_dir: Path) -> None:
        """Test ZIP archive decompression."""
        # Create ZIP archive
        archive_path = output_dir / "test.zip"
        with zipfile.ZipFile(archive_path, "w") as zf:
            for file in mock_compressed_dir.rglob("*"):
                if file.is_file():
                    zf.write(file, arcname=file.name)

        # Decompress
        extract_dir = output_dir / "extracted"
        result = decompress(archive_path, extract_dir)

        assert result == extract_dir
        assert extract_dir.exists()
        assert len(list(extract_dir.rglob("*"))) > 0

    def test_decompress_zstd(self, mock_compressed_dir: Path, output_dir: Path) -> None:
        """Test Zstandard archive decompression."""
        # Create tar+zstd archive
        archiver = Archiver(mock_compressed_dir)
        archive_path = output_dir / "test.zst"
        archiver.create(archive_path, use_tar=True, kind="zstd", level=10)

        # Decompress
        extract_dir = output_dir / "extracted"
        result = decompress(archive_path, extract_dir)

        assert result == extract_dir
        assert extract_dir.exists()

    def test_decompress_tar(self, mock_compressed_dir: Path, output_dir: Path) -> None:
        """Test tar archive decompression."""
        # Create tar archive
        archive_path = output_dir / "test.tar"
        with tarfile.open(archive_path, "w") as tf:
            tf.add(mock_compressed_dir, arcname=".")

        # Decompress
        extract_dir = output_dir / "extracted"
        result = decompress(archive_path, extract_dir)

        assert result == extract_dir
        assert extract_dir.exists()

    def test_decompress_unsupported_format(self, output_dir: Path) -> None:
        """Test decompression with unsupported format_."""
        archive_path = output_dir / "test.rar"
        archive_path.touch()

        with pytest.raises(ValueError, match="Unsupported archive format_"):
            decompress(archive_path, output_dir / "extracted")

    @patch("builtins.print")
    def test_decompress_debug_mode(
        self, mock_print: MagicMock, mock_compressed_dir: Path, output_dir: Path
    ) -> None:
        """Test decompression with debug output."""
        # Create archive
        archive_path = output_dir / "test.zip"
        with zipfile.ZipFile(archive_path, "w") as zf:
            for file in mock_compressed_dir.rglob("*"):
                if file.is_file():
                    zf.write(file, arcname=file.name)

        # Decompress with debug
        extract_dir = output_dir / "extracted"
        decompress(archive_path, extract_dir, debug=True)

        # Verify debug output
        print_calls = [str(call) for call in mock_print.call_args_list]
        debug_output = "".join(print_calls)

        assert "DECOMPRESSION DEBUG INFO" in debug_output
        assert "DECOMPRESSION RESULTS" in debug_output
        assert "Archive Size:" in debug_output
        assert "Extracted Files:" in debug_output


class TestIntegration:
    """Integration tests for full compression pipeline."""

    def test_full_compression_decompression_cycle(
        self, mock_image_dir: Path, temp_dir: Path
    ) -> None:
        """Test complete compress → archive → decompress cycle."""
        # Step 1: Compress images
        compressed_dir = temp_dir / "compressed"
        archive_path = compress(
            input_dir=mock_image_dir,
            output_dir=compressed_dir,
            format_="webp",
            quality=85,
            archive=True,
            archive_output=temp_dir / "dataset.zst",
        )

        assert archive_path.exists()

        # Step 2: Decompress archive
        extracted_dir = temp_dir / "extracted"
        result = decompress(archive_path, extracted_dir)

        assert result.exists()
        assert len(list(extracted_dir.rglob("*.webp"))) > 0

    def test_compression_preserves_quality(
        self, mock_image_dir: Path, output_dir: Path
    ) -> None:
        """Test that compressed images maintain reasonable quality."""
        compress(
            input_dir=mock_image_dir,
            output_dir=output_dir,
            format_="webp",
            quality=95,
        )

        # Verify output images can be opened
        for img_path in output_dir.rglob("*.webp"):
            with Image.open(img_path) as img:
                assert img.size[0] > 0
                assert img.size[1] > 0

    def test_multiple_compression_formats(
        self, mock_image_dir: Path, temp_dir: Path
    ) -> None:
        """Test compression with multiple formats in sequence."""
        formats = ["webp", "png"]

        for fmt in formats:
            out_dir = temp_dir / fmt
            result = compress(
                input_dir=mock_image_dir,
                output_dir=out_dir,
                format_=fmt,
                quality=85,
            )

            assert result.exists()
            assert len(list(out_dir.rglob(f"*.{fmt}"))) > 0
