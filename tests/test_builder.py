"""
Test script for the unified Builder class.

This script demonstrates the usage of the new Builder class and validates
that it can be imported and instantiated correctly.
"""

import json
import tempfile
from pathlib import Path

# Test the Builder import
try:
    from builder import Builder
    print("Success: Successfully imported Builder class")
except ImportError as e:
    print(f"Error: Failed to import Builder class: {e}")
    exit(1)

# Create a test configuration file
test_config = {
    "dataset_name": "test_dataset",
    "categories": {
        "cats": ["cat", "kitten"],
        "dogs": ["dog", "puppy"]
    },
    "options": {
        "max_images": 5,
        "integrity": True,
        "generate_labels": True
    }
}

# Create temporary config file
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    json.dump(test_config, f, indent=2)
    config_path = f.name

try:
    # Test Builder instantiation
    print("Testing Builder instantiation...")
    builder = Builder(
        config_path=config_path,
        max_images=10,
        output_dir="./test_output",
        integrity=True,
        generate_labels=True
    )
    print("Success: Builder instantiated successfully")

    # Test configuration methods
    print("\nTesting configuration methods...")
    builder.set_maxi(20)
    builder.set_ai_model("gpt4-mini")
    builder.enable_kwgen("auto")
    builder.enable_integrity(True)
    builder.enable_label_generation(True)
    print("Success: Configuration methods work correctly")

    # Test getter methods
    print("\nTesting getter methods...")
    config = builder.config
    dataset_info = builder.dataset_info()
    engines = builder.available_engines()
    variations = builder.search_variations()

    print(f"Success: Dataset info: {dataset_info}")
    print(f"Success: Available engines: {engines}")
    print(f"Success: Search variations count: {len(variations)}")

    # Test string representations
    print(f"\nBuilder string representation: {str(builder)}")
    print(f"Builder repr: {repr(builder)}")

    print("\nSuccess: All tests passed! Builder class is working correctly.")

except Exception as e:
    print(f"Error: Test failed: {e}")
    import traceback
    traceback.print_exc()

finally:
    # Cleanup
    Path(config_path).unlink(missing_ok=True)
