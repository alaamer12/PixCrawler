"""
Integration tests for the validator package.

This module provides comprehensive integration testing for image integrity validation,
duplicate detection, batch processing, and quarantine functionality using pytest.
"""

import os
import shutil
import tempfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from validator import (
    CheckManager,
    CheckMode,
    DuplicateAction,
    ImageHasher,
    ImageValidator,
    IntegrityProcessor,
    ValidatorConfig,
    get_default_config,
    get_lenient_config,
    get_strict_config,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_dataset_dir():
    """Create a temporary directory for test datasets."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_images(temp_dataset_dir):
    """Create valid sample images."""
    image_paths = []
    for i in range(5):
        img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img = Image.fromarray(img_array, mode='RGB')
        img_path = os.path.join(temp_dataset_dir, f'image_{i}.jpg')
        img.save(img_path, 'JPEG')
        image_paths.append(img_path)
    return image_paths


# ============================================================================
# Integration Tests: Integrity Workflows
# ============================================================================

class TestIntegrityWorkflows:
    """Test image validation, duplicate detection, batch processing, and edge cases."""
    
    def test_valid_images(self, sample_images, temp_dataset_dir):
        """Test validation of valid images."""
        validator = ImageValidator()
        valid_count, total_count, corrupted_files = validator.count_valid(temp_dataset_dir)
        
        assert valid_count == 5
        assert total_count == 5
        assert len(corrupted_files) == 0
    
    def test_corrupted_images(self, temp_dataset_dir):
        """Test validation detects corrupted images."""
        valid_path = os.path.join(temp_dataset_dir, 'valid.jpg')
        img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img = Image.fromarray(img_array, mode='RGB')
        img.save(valid_path, 'JPEG')
        
        with open(os.path.join(temp_dataset_dir, 'corrupted.jpg'), 'wb') as f:
            f.write(b'invalid image data')
        
        validator = ImageValidator()
        valid_count, total_count, corrupted_files = validator.count_valid(temp_dataset_dir)
        
        assert valid_count == 1
        assert total_count == 2
        assert len(corrupted_files) == 1
    
    @pytest.mark.parametrize("img_size,min_width,min_height,expected_valid", [
        ((10, 10), 50, 50, 0),
        ((200, 200), 50, 50, 1),
        ((75, 75), 50, 50, 1),
    ])
    def test_dimension_constraints(self, temp_dataset_dir, img_size, min_width, min_height, expected_valid):
        """Test validation with dimension constraints."""
        img = Image.new('RGB', img_size, color='red')
        img.save(os.path.join(temp_dataset_dir, 'test.jpg'), 'JPEG')
        
        validator = ImageValidator(min_width=min_width, min_height=min_height)
        valid_count, _, _ = validator.count_valid(temp_dataset_dir)
        
        assert valid_count == expected_valid
    
    def test_empty_directory(self, temp_dataset_dir):
        """Test validation of empty directory."""
        validator = ImageValidator()
        valid_count, total_count, corrupted_files = validator.count_valid(temp_dataset_dir)
        
        assert valid_count == 0
        assert total_count == 0
        assert len(corrupted_files) == 0
    
    def test_duplicate_detection(self, temp_dataset_dir):
        """Test exact duplicate detection."""
        from validator.integrity import DuplicationManager
        
        img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img = Image.fromarray(img_array, mode='RGB')
        original_path = os.path.join(temp_dataset_dir, 'original.jpg')
        img.save(original_path, 'JPEG')
        
        duplicate_path = os.path.join(temp_dataset_dir, 'duplicate.jpg')
        shutil.copy(original_path, duplicate_path)
        
        dup_manager = DuplicationManager(ImageHasher())
        duplicates = dup_manager.detect_duplicates(temp_dataset_dir)
        
        assert len(duplicates) == 1
        assert len(list(duplicates.values())[0]) == 1
    
    @pytest.mark.parametrize("hash_type", ["content", "perceptual"])
    def test_hash_computation(self, sample_images, hash_type):
        """Test hash computation and consistency."""
        hasher = ImageHasher()
        
        if hash_type == "content":
            hash1 = hasher.compute_content_hash(sample_images[0])
            hash2 = hasher.compute_content_hash(sample_images[0])
            hash3 = hasher.compute_content_hash(sample_images[1])
        else:
            hash1 = hasher.compute_perceptual_hash(sample_images[0])
            hash2 = hasher.compute_perceptual_hash(sample_images[0])
            hash3 = hasher.compute_perceptual_hash(sample_images[1])
        
        assert hash1 == hash2
        assert hash1 is not None
        if hash_type == "content":
            assert hash1 != hash3
    
    @pytest.mark.parametrize("ext,fmt", [
        ('png', 'PNG'),
        ('jpg', 'JPEG'),
        ('bmp', 'BMP'),
    ])
    def test_multiple_formats(self, temp_dataset_dir, ext, fmt):
        """Test support for multiple image formats."""
        img = Image.new('RGB', (100, 100), color='red')
        img.save(os.path.join(temp_dataset_dir, f'image.{ext}'), fmt)
        
        validator = ImageValidator()
        valid_count, total_count, _ = validator.count_valid(temp_dataset_dir)
        
        assert valid_count == total_count == 1
    
    @pytest.mark.parametrize("dataset_type,expected", [
        ("large", (20, 20, 0)),
        ("mixed", (5, 3, 2)),
        ("single", (1, 1, 0)),
    ])
    def test_batch_processing(self, temp_dataset_dir, dataset_type, expected):
        """Test batch processing various dataset types."""
        if dataset_type == "large":
            for i in range(20):
                img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
                img = Image.fromarray(img_array, mode='RGB')
                img.save(os.path.join(temp_dataset_dir, f'batch_{i}.jpg'), 'JPEG')
        elif dataset_type == "mixed":
            for i in range(3):
                img = Image.new('RGB', (100, 100), color='red')
                img.save(os.path.join(temp_dataset_dir, f'valid_{i}.jpg'), 'JPEG')
            for i in range(2):
                with open(os.path.join(temp_dataset_dir, f'corrupt_{i}.jpg'), 'wb') as f:
                    f.write(b'bad data')
        else:
            img = Image.new('RGB', (100, 100), color='white')
            img.save(os.path.join(temp_dataset_dir, 'single.jpg'), 'JPEG')
        
        processor = IntegrityProcessor()
        results = processor.process_dataset(temp_dataset_dir, remove_duplicates=False, remove_corrupted=False)
        
        total, valid, corrupted = expected
        assert results['validation']['total_count'] == total
        assert results['validation']['valid_count'] == valid
        assert results['validation']['corrupted_count'] == corrupted
    
    def test_duplicate_removal_workflow(self, temp_dataset_dir):
        """Test duplicate removal workflow."""
        img = Image.new('RGB', (100, 100), color='blue')
        original = os.path.join(temp_dataset_dir, 'original.jpg')
        img.save(original, 'JPEG')
        
        duplicate = os.path.join(temp_dataset_dir, 'duplicate.jpg')
        shutil.copy(original, duplicate)
        
        processor = IntegrityProcessor()
        results = processor.process_dataset(temp_dataset_dir, remove_duplicates=True, remove_corrupted=False)
        
        assert results['duplicates']['removed_count'] == 1
        # One file should remain, one should be removed (order is non-deterministic)
        assert os.path.exists(original) != os.path.exists(duplicate)
    
    def test_invalid_paths(self):
        """Test handling of invalid paths."""
        validator = ImageValidator()
        hasher = ImageHasher()
        
        valid_count, total_count, _ = validator.count_valid('/nonexistent/path')
        assert (valid_count, total_count) == (0, 0)
        
        assert hasher.compute_content_hash('/nonexistent/file.jpg') is None
        assert hasher.compute_perceptual_hash('/nonexistent/file.jpg') is None


# ============================================================================
# Integration Tests: CheckManager and Validation Modes
# ============================================================================

class TestCheckManager:
    """Test CheckManager workflows, modes, and configuration."""
    
    def test_quarantine_workflow(self, temp_dataset_dir):
        """Test quarantine functionality."""
        quarantine_dir = Path(temp_dataset_dir) / 'quarantine'
        
        config = ValidatorConfig(
            duplicate_action=DuplicateAction.QUARANTINE,
            quarantine_dir=quarantine_dir,
            min_file_size_bytes=1
        )
        
        img = Image.new('RGB', (100, 100), color='green')
        original = os.path.join(temp_dataset_dir, 'original.jpg')
        img.save(original, 'JPEG')
        shutil.copy(original, os.path.join(temp_dataset_dir, 'duplicate.jpg'))
        
        manager = CheckManager(config)
        assert quarantine_dir.exists()
        
        result = manager.check_duplicates(temp_dataset_dir)
        assert result.duplicates_found == 1
        assert result.duplicates_removed == 1
    
    @pytest.mark.parametrize("mode,has_error,expected_valid", [
        ("strict", True, None),
        ("lenient", False, 1),
        ("report_only", False, None),
    ])
    def test_validation_modes(self, temp_dataset_dir, mode, has_error, expected_valid):
        """Test strict, lenient, and report-only modes."""
        valid_img = Image.new('RGB', (100, 100), color='red')
        valid_img.save(os.path.join(temp_dataset_dir, 'valid.jpg'), 'JPEG')
        
        with open(os.path.join(temp_dataset_dir, 'corrupt.jpg'), 'wb') as f:
            f.write(b'invalid')
        
        if mode == "strict":
            config = get_strict_config()
        elif mode == "lenient":
            config = get_lenient_config()
        else:
            config = ValidatorConfig(mode=CheckMode.REPORT_ONLY, duplicate_action=DuplicateAction.REPORT_ONLY)
        
        manager = CheckManager(config)
        
        if has_error:
            with pytest.raises(ValueError):
                manager.check_integrity(temp_dataset_dir)
        else:
            result = manager.check_integrity(temp_dataset_dir)
            if expected_valid:
                assert result.valid_images == expected_valid
                assert result.corrupted_images == 1
    
    def test_complete_workflow(self, sample_images, temp_dataset_dir):
        """Test complete validation workflow."""
        manager = CheckManager(get_default_config())
        
        dup_result, integrity_result = manager.check_all(temp_dataset_dir)
        
        assert integrity_result.total_images == 5
        assert integrity_result.valid_images == 5
        assert dup_result.total_images == 5
    
    def test_statistics_and_reporting(self, sample_images, temp_dataset_dir):
        """Test statistics tracking and report generation."""
        manager = CheckManager(get_default_config())
        
        manager.check_integrity(temp_dataset_dir)
        manager.check_duplicates(temp_dataset_dir)
        
        stats = manager.get_stats()
        assert stats.total_checks == 2
        assert stats.successful_checks == 2
        
        report = manager.get_summary_report()
        assert report['total_checks'] > 0
        assert 'success_rate' in report
        
        manager.reset_stats()
        assert manager.get_stats().total_checks == 0
    
    def test_config_management(self, temp_dataset_dir, sample_images):
        """Test configuration updates and presets."""
        manager = CheckManager(get_default_config()) 
        
        manager.update_config(batch_size=200, min_image_width=50)
        assert manager.config.batch_size == 200
        
        for preset_func, expected_mode in [
            (get_default_config, CheckMode.LENIENT),
            (get_strict_config, CheckMode.STRICT),
            (get_lenient_config, CheckMode.LENIENT),
        ]:
            config = preset_func()
            assert config.mode == expected_mode
            manager = CheckManager(config)
            result = manager.check_integrity(temp_dataset_dir)
            assert result.total_images == 5
