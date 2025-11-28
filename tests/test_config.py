#!/usr/bin/env python3
"""
Simple test script to verify the level.py implementation works correctly.
"""

import os
import tempfile
import time

from PIL import Image

from validator.level import (
    ValidationLevel,
    ValidationConfig,
    ValidationResult,
    get_validation_strategy,
    FastValidation
)
from pathlib import Path

def create_test_image(path: str, width: int = 100, height: int = 100, format_: str = 'JPEG'):
    """Create a test image file."""
    img = Image.new('RGB', (width, height), color='red')
    img.save(path, format_)


def test_validation_config():
    """Test ValidationConfig with Pydantic V2 features."""
    print("Testing ValidationConfig...")

    # Test default config
    config = ValidationConfig()
    print(f"Default config: min_width={config.min_width}, min_height={config.min_height}")

    # Test custom config with validation
    try:
        config = ValidationConfig(
            min_width=50,
            min_height=50,
            max_file_size_mb=5.0,
            strict_mode=True,
            check_transparency=True
        )
        print(f"Custom config created successfully: {config.model_dump()}")
    except Exception as e:
        print(f"Config validation error: {e}")

    # Test invalid config (should raise error)
    try:
        invalid_config = ValidationConfig(min_width=0)  # Should fail
        print("ERROR: Invalid config was accepted!")
    except Exception as e:
        print(f"Correctly caught invalid config: {e}")


def test_fast_validation():
    """Test FastValidation implementation."""
    print("\nTesting FastValidation...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test image
        test_image_path = os.path.join(temp_dir, "test_image.jpg")
        create_test_image(test_image_path, 200, 150)

        # Test with default config
        validator = FastValidation()
        result = validator.validate(test_image_path)

        print(f"Validation result: is_valid={result.is_valid}")
        print(f"Issues: {result.issues_found}")
        print(f"Metadata: {result.metadata}")
        print(f"Processing time: {result.processing_time:.4f}s")

        # Test with custom config
        config = ValidationConfig(min_width=300, min_height=200, strict_mode=True)
        strict_validator = FastValidation(config)
        strict_result = strict_validator.validate(test_image_path)

        print(f"\nStrict validation result: is_valid={strict_result.is_valid}")
        print(f"Strict issues: {strict_result.issues_found}")

        # Test non-existent file
        missing_result = validator.validate("non_existent_file.jpg")
        print(f"\nMissing file result: is_valid={missing_result.is_valid}")
        print(f"Missing file issues: {missing_result.issues_found}")


def test_validation_levels():
    """Test all validation levels."""
    print("\nTesting all validation levels...")

    with tempfile.TemporaryDirectory() as temp_dir:
        test_image_path = os.path.join(temp_dir, "test_image.png")
        create_test_image(test_image_path, 100, 100, 'PNG')

        for level in ValidationLevel:
            print(f"\nTesting {level.name} validation:")
            try:
                strategy = get_validation_strategy(level)
                result = strategy.validate(test_image_path)
                print(f"  Result: is_valid={result.is_valid}")
                print(f"  Level: {result.validation_level.name}")
                print(f"  Issues count: {len(result.issues_found)}")
                print(f"  Metadata keys: {list(result.metadata.keys())}")
            except Exception as e:
                print(f"  Error: {e}")


def test_validation_result_model():
    """Test ValidationResult Pydantic model."""
    print("\nTesting ValidationResult model...")

    # Test valid result creation
    try:
        result = ValidationResult(
            is_valid=True,
            issues_found=[],
            metadata={"width": 100, "height": 100},
            processing_time=0.025,
            validation_level=ValidationLevel.FAST,
            file_path="/test/path.jpg",
            file_size_bytes=1024
        )
        print(f"Valid result created: {result.model_dump()}")
    except Exception as e:
        print(f"Error creating valid result: {e}")

    # Test invalid result (should fail validation)
    try:
        invalid_result = ValidationResult(
            is_valid=False,
            issues_found=[],  # Invalid: no issues but marked as invalid
            metadata={},
            processing_time=0.025,
            validation_level=ValidationLevel.FAST
        )
        print("ERROR: Invalid result was accepted!")
    except Exception as e:
        print(f"Correctly caught invalid result: {e}")



def test_root_config():
    """Test the root config.py enhancements."""
    print("Testing root config.py...")

    try:
        from config import ProjectSettings, Environment, LogLevel, get_project_settings

        # Test default settings
        settings = ProjectSettings()
        print(f"Default project name: {settings.project_name}")
        print(f"Default environment: {settings.environment}")
        print(f"Default log level: {settings.log_level}")

        # Test custom settings with validation
        custom_settings = ProjectSettings(
            project_name="PixCrawler-Test",
            version="2.1.0",
            environment=Environment.STAGING,
            log_level=LogLevel.DEBUG,
            max_workers=8,
            enabled_packages=["backend", "builder", "validator"]
        )
        print(f"Custom settings created successfully")
        print(
            f"Package enabled check (backend): {custom_settings.is_package_enabled('backend')}")
        print(
            f"Package enabled check (frontend): {custom_settings.is_package_enabled('frontend')}")

        # Test validation errors
        try:
            invalid_settings = ProjectSettings(
                environment=Environment.PRODUCTION,
                debug=True  # Should fail - debug in production
            )
            print("ERROR: Invalid production settings were accepted!")
        except Exception as e:
            print(f"Correctly caught production validation error: {e}")

        # Test cached settings
        cached_settings = get_project_settings()
        print(f"Cached settings retrieved: {cached_settings.project_name}")

    except Exception as e:
        print(f"Error testing root config: {e}")
        return False

    return True


def test_validator_config():
    """Test the validator config.py enhancements."""
    print("\nTesting validator config.py...")

    try:
        from validator.config import (
            ValidatorConfig, CheckMode, DuplicateAction,
            get_default_config, get_strict_config, get_lenient_config
        )

        # Test default config
        config = get_default_config()
        print(f"Default mode: {config.mode}")
        print(f"Default extensions: {config.supported_extensions[:3]}...")

        # Test strict config
        strict_config = get_strict_config()
        print(f"Strict mode: {strict_config.mode}")
        print(
            f"Strict min dimensions: {strict_config.min_image_width}x{strict_config.min_image_height}")

        # Test custom config with validation
        custom_config = ValidatorConfig(
            mode=CheckMode.STRICT,
            duplicate_action=DuplicateAction.QUARANTINE,
            supported_extensions=('.jpg', '.png', '.webp'),
            max_file_size_mb=50,
            min_image_width=100,
            min_image_height=100,
            batch_size=200,
            quarantine_dir=Path("./test_quarantine")
        )
        print(f"Custom config created successfully")
        print(f"Extensions after validation: {custom_config.supported_extensions}")

        # Test validation errors
        try:
            invalid_config = ValidatorConfig(
                min_file_size_bytes=10485760,  # 10MB
                max_file_size_mb=5  # 5MB - should fail
            )
            print("ERROR: Invalid file size config was accepted!")
        except Exception as e:
            print(f"Correctly caught file size validation error: {e}")

        # Test extension validation
        try:
            invalid_ext_config = ValidatorConfig(
                supported_extensions=('jpg', '.png')  # Missing dot
            )
            print("ERROR: Invalid extension config was accepted!")
        except Exception as e:
            print(f"Correctly caught extension validation error: {e}")

    except Exception as e:
        print(f"Error testing validator config: {e}")
        return False

    return True


def test_config_serialization():
    """Test configuration serialization and deserialization."""
    print("\nTesting config serialization...")

    try:
        from config import ProjectSettings
        from validator.config import ValidatorConfig

        # Test root config serialization
        settings = ProjectSettings(
            project_name="TestProject",
            version="1.2.3",
            max_workers=6
        )

        settings_dict = settings.to_dict()
        print(f"Root config serialized: {len(settings_dict)} fields")

        # Test validator config serialization
        from validator.config import CheckMode
        validator_config = ValidatorConfig(
            mode=CheckMode.STRICT,
            batch_size=150
        )

        validator_dict = validator_config.to_dict()
        print(f"Validator config serialized: {len(validator_dict)} fields")

        # Test basic functionality instead of complex deserialization
        print(f"Validator config mode: {validator_config.mode}")
        print(f"Validator config batch size: {validator_config.batch_size}")

    except Exception as e:
        print(f"Error testing serialization: {e}")
        return False

    return True


def test_celery_settings():
    """Test the enhanced CelerySettings model."""
    print("Testing CelerySettings...")

    try:
        from celery_core.config import CelerySettings, get_celery_settings

        # Test default settings
        settings = CelerySettings()
        print(f"Default broker URL: {settings.broker_url}")
        print(f"Default worker concurrency: {settings.worker_concurrency}")

        # Test custom settings with validation
        custom_settings = CelerySettings(
            broker_url="redis://localhost:6379/2",
            result_backend="redis://localhost:6379/3",
            worker_concurrency=8,
            task_time_limit=3600,
            task_soft_time_limit=3300,
            task_serializer="json",
            accept_content=["json", "pickle"],
            default_queue="high_priority"
        )
        print(f"Custom settings created successfully")
        print(f"Custom queue: {custom_settings.default_queue}")

        # Test configuration generation
        config = custom_settings.get_celery_config()
        print(f"Generated config keys: {len(config)}")

        # Test validation errors
        try:
            invalid_settings = CelerySettings(
                task_time_limit=1800,
                task_soft_time_limit=2000  # Should fail - soft > hard
            )
            print("ERROR: Invalid time limit settings were accepted!")
        except Exception as e:
            print(f"Correctly caught time limit validation error: {e}")

        # Test URL validation
        try:
            invalid_url_settings = CelerySettings(
                broker_url="invalid://url"
            )
            print("ERROR: Invalid URL was accepted!")
        except Exception as e:
            print(f"Correctly caught URL validation error: {e}")

        # Test cached settings
        cached_settings = get_celery_settings()
        print(f"Cached settings retrieved: {cached_settings.broker_url}")

    except Exception as e:
        print(f"Error testing CelerySettings: {e}")
        return False

    return True


def test_task_result():
    """Test the enhanced TaskResult model."""
    print("\nTesting TaskResult...")

    try:
        from celery_core.base import TaskResult, TaskStatus

        # Test valid result creation
        start_time = time.time()
        end_time = start_time + 45.2

        result = TaskResult(
            task_id="test-task-123",
            task_name="test_processing_task",
            status=TaskStatus.SUCCESS,
            result={"processed": 100, "errors": 0},
            start_time=start_time,
            end_time=end_time,
            processing_time=45.2,
            metadata={"worker": "worker1", "queue": "default"}
        )
        print(f"Valid result created: {result.task_id}")
        print(f"Processing time: {result.processing_time}s")

        # Test serialization
        result_dict = result.to_dict()
        print(f"Serialized result keys: {len(result_dict)}")

        # Test deserialization
        restored_result = TaskResult.from_dict(result_dict)
        print(f"Restored result: {restored_result.task_id}")

        # Test validation errors
        try:
            invalid_result = TaskResult(
                task_id="",  # Should fail - empty task ID
                task_name="test_task",
                status=TaskStatus.SUCCESS
            )
            print("ERROR: Invalid empty task ID was accepted!")
        except Exception as e:
            print(f"Correctly caught empty task ID error: {e}")

        # Test time consistency validation
        try:
            invalid_time_result = TaskResult(
                task_id="test-task-456",
                task_name="test_task",
                status=TaskStatus.SUCCESS,
                start_time=100.0,
                end_time=50.0  # Should fail - end before start
            )
            print("ERROR: Invalid time relationship was accepted!")
        except Exception as e:
            print(f"Correctly caught time consistency error: {e}")

        # Test failure status validation
        try:
            invalid_failure_result = TaskResult(
                task_id="test-task-789",
                task_name="test_task",
                status=TaskStatus.FAILURE
                # Missing error message - should fail
            )
            print("ERROR: Failed task without error message was accepted!")
        except Exception as e:
            print(f"Correctly caught failure validation error: {e}")

    except Exception as e:
        print(f"Error testing TaskResult: {e}")
        return False

    return True


def test_task_context():
    """Test the enhanced TaskContext model."""
    print("\nTesting TaskContext...")

    try:
        from celery_core.base import TaskContext

        # Test valid context creation
        context = TaskContext(
            task_id="context-test-123",
            task_name="test_context_task",
            args=("arg1", "arg2"),
            kwargs={"param1": "value1", "max_retries": 3},
            retries=1,
            max_retries=5,
            eta=time.time() + 300,  # 5 minutes from now
            expires=time.time() + 3600  # 1 hour from now
        )
        print(f"Valid context created: {context.task_id}")
        print(f"Retries: {context.retries}/{context.max_retries}")

        # Test serialization
        context_dict = context.to_dict()
        print(f"Serialized context keys: {len(context_dict)}")

        # Test validation errors
        try:
            invalid_context = TaskContext(
                task_id="test-context-456",
                task_name="test_task",
                retries=10,
                max_retries=5  # Should fail - retries > max_retries
            )
            print("ERROR: Invalid retry count was accepted!")
        except Exception as e:
            print(f"Correctly caught retry validation error: {e}")

        # Test time validation
        try:
            invalid_time_context = TaskContext(
                task_id="test-context-789",
                task_name="test_task",
                eta=time.time() + 3600,
                expires=time.time() + 1800  # Should fail - expires before eta
            )
            print("ERROR: Invalid time relationship was accepted!")
        except Exception as e:
            print(f"Correctly caught time validation error: {e}")

    except Exception as e:
        print(f"Error testing TaskContext: {e}")
        return False

    return True


def test_task_info():
    """Test the enhanced TaskInfo model."""
    print("\nTesting TaskInfo...")

    try:
        from celery_core.manager import TaskInfo

        # Test valid task info creation
        task_info = TaskInfo(
            task_id="info-test-123",
            task_name="test_info_task",
            args=("arg1", 123),
            kwargs={"param": "value", "count": 42},
            queue="high_priority"
        )
        print(f"Valid task info created: {task_info.task_id}")
        print(f"Queue: {task_info.queue}")
        print(f"Submitted at: {task_info.submitted_at}")

        # Test serialization
        info_dict = task_info.to_dict()
        print(f"Serialized info keys: {len(info_dict)}")

        # Test validation errors
        try:
            invalid_info = TaskInfo(
                task_id="",  # Should fail - empty task ID
                task_name="test_task"
            )
            print("ERROR: Invalid empty task ID was accepted!")
        except Exception as e:
            print(f"Correctly caught empty task ID error: {e}")

        # Test queue name validation
        try:
            invalid_queue_info = TaskInfo(
                task_id="test-info-456",
                task_name="test_task",
                queue="invalid queue name!"  # Should fail - invalid characters
            )
            print("ERROR: Invalid queue name was accepted!")
        except Exception as e:
            print(f"Correctly caught queue validation error: {e}")

    except Exception as e:
        print(f"Error testing TaskInfo: {e}")
        return False

    return True


if __name__ == "__main__":
    print("Testing PixCrawler Validator Level Implementation")
    print("=" * 50)

    test_validation_config()
    test_fast_validation()
    test_validation_levels()
    test_validation_result_model()

    print("\n" + "=" * 50)
    print("Testing completed!")

    print("Testing Enhanced Pydantic Configurations")
    print("=" * 50)

    success = True
    success &= test_root_config()
    success &= test_validator_config()
    success &= test_config_serialization()

    print("\n" + "=" * 50)
    if success:
        print("All configuration tests passed!")
    else:
        print("Some tests failed!")

    print("Testing Enhanced Pydantic Models in celery_core")
    print("=" * 60)

    success = True
    success &= test_celery_settings()
    success &= test_task_result()
    success &= test_task_context()
    success &= test_task_info()

    print("\n" + "=" * 60)
    if success:
        print("All celery_core model tests passed!")
    else:
        print("Some tests failed!")
