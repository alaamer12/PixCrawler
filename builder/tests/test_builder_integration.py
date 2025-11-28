"""
Integration tests for the builder package using pytest.

This module provides integration tests that verify end-to-end workflows
for the builder package, including keyword generation, label generation,
and error handling with retry mechanisms.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image


def _write_png_image(path: Path, size=(8, 8), color=(255, 0, 0)) -> None:
    """Create a small PNG image for testing."""
    img = Image.new("RGB", size, color)
    # Ensure parent exists
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(path), format="PNG")


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    import shutil
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def sample_config():
    """Create a sample configuration for testing."""
    return {
        "dataset_name": "test_dataset",
        "categories": {
            "cats": ["cat", "kitten"],
            "dogs": ["dog", "puppy"]
        },
        "options": {
            "max_images": 5,
            "generate_labels": True
        }
    }

@pytest.mark.parametrize("fmt", ["txt", "json", "csv", "yaml"])
def test_label_generation_formats(temp_dir, fmt):
    """Test label generation in multiple formats."""
    try:
        from builder._generator import LabelGenerator

        # Create test dataset structure
        dataset_dir = temp_dir / "dataset"
        cat_kw_dir = dataset_dir / "cats" / "cute_cat"
        dog_kw_dir = dataset_dir / "dogs" / "puppy"

        _write_png_image(cat_kw_dir / "img1.png")
        _write_png_image(cat_kw_dir / "img2.png")
        _write_png_image(dog_kw_dir / "imgA.png")

        # Generate labels
        lg = LabelGenerator(format_type=fmt)
        lg.generate_dataset_labels(str(dataset_dir))

        # Verify labels directory exists
        labels_root = dataset_dir / "labels"
        assert labels_root.exists()

        # Verify per-image label files exist (with fallback for YAML)
        def _expected_label_path(keyword_dir: Path, name: str) -> Path:
            ext = fmt
            if fmt == "yaml":
                try:
                    import yaml  # noqa: F401
                except Exception:
                    ext = "txt"  # fallback
            return labels_root / keyword_dir.parts[-2] / keyword_dir.parts[-1] / f"{name}.{ext}"

        assert _expected_label_path(cat_kw_dir, "img1").exists()
        assert _expected_label_path(cat_kw_dir, "img2").exists()
        assert _expected_label_path(dog_kw_dir, "imgA").exists()

    except ImportError:
        pytest.skip("LabelGenerator not available - missing dependencies")
    except Exception as e:
        pytest.fail(f"Label generation test failed: {e}")


@patch('builder._generator.ImageDownloader')
@patch('builder._generator.download_images_ddgs')
def test_retry_download_success(mock_ddgs, mock_downloader, temp_dir):
    """Test retry download mechanism with successful fallback."""
    try:
        from builder._generator import retry_download

        # Mock ImageDownloader to fail initially
        mock_downloader.return_value.download.return_value = (False, 0)

        # Mock DDGS to succeed on retry
        def fake_ddgs(keyword, out_dir, max_num):
            Path(out_dir).mkdir(parents=True, exist_ok=True)
            for i in range(max_num):
                _write_png_image(Path(out_dir) / f"ddgs_{i+1:03d}.png")
            return True, max_num

        mock_ddgs.side_effect = fake_ddgs

        # Test retry download
        success, count = retry_download(
            "test keyword",
            str(temp_dir / "out"),
            max_num=3,
            max_retries=2
        )

        assert success is True
        assert count >= 1

        # Verify files were created
        out_dir = temp_dir / "out"
        files = list(out_dir.glob("*"))
        assert len(files) > 0

    except ImportError:
        pytest.skip("retry_download not available - missing dependencies")
    except Exception as e:
        pytest.fail(f"Retry download test failed: {e}")


@patch('builder._generator.ImageDownloader')
@patch('builder._generator.download_images_ddgs')
def test_retry_download_failure(mock_ddgs, mock_downloader, temp_dir):
    """Test retry download mechanism with complete failure."""
    try:
        from builder._generator import retry_download

        # Mock both to always fail
        mock_downloader.return_value.download.return_value = (False, 0)
        mock_ddgs.return_value = (False, 0)

        # Test that exception is raised after exhausted retries
        with pytest.raises(Exception):
            retry_download(
                "no images",
                str(temp_dir / "out"),
                max_num=2,
                max_retries=1
            )

    except ImportError:
        pytest.skip("retry_download not available - missing dependencies")
    except Exception as e:
        pytest.fail(f"Retry download failure test failed: {e}")


def test_keyword_management_basic():
    """Test basic keyword management functionality."""
    try:
        from _keywords import KeywordManagement

        # Test instantiation
        km = KeywordManagement(ai_model="gpt4-mini", keyword_generation="auto")
        assert km is not None
        assert km.ai_model == "gpt4-mini"
        assert km.keyword_generation == "auto"

    except ImportError:
        pytest.skip("KeywordManagement not available - missing dependencies")
    except Exception as e:
        pytest.fail(f"Keyword management test failed: {e}")


def test_builder_configuration_methods(temp_dir):
    """Test Builder configuration methods."""
    try:
        from builder import Builder

        # Create minimal config
        config_data = {
            "dataset_name": "test_dataset",
            "categories": {"test": ["test_keyword"]}
        }

        config_path = temp_dir / "test_config.json"
        with open(config_path, 'w') as f:
            json.dump(config_data, f)

        builder = Builder(config_path=str(config_path))

        # Test configuration methods
        builder.set_maxi(20)
        assert builder.config.max_images == 20

        builder.enable_label_generation(True)
        assert builder.config.generate_labels is True

    except ImportError:
        pytest.skip("Builder not available - missing dependencies")
    except Exception as e:
        pytest.fail(f"Builder configuration test failed: {e}")
