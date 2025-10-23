"""
Example usage of the unified Builder class for PixCrawler.

This example demonstrates how to use the Builder class across your monorepo
for generating image datasets with various configurations.
"""

import json
from pathlib import Path

from builder import Builder


def create_sample_config():
    """Create a sample configuration file for demonstration."""
    config = {
        "dataset_name": "animals_dataset",
        "categories": {
            "cats": ["cat", "kitten", "feline"],
            "dogs": ["dog", "puppy", "canine"],
            "birds": ["bird", "eagle", "sparrow"]
        },
        "options": {
            "max_images": 20,
            "generate_labels": True,
            "keyword_generation": "auto",
            "ai_model": "gpt4-mini"
        }
    }

    config_path = Path("sample_config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    return str(config_path)


def example_basic_usage():
    """Example 1: Basic usage with config file."""
    print("=== Example 1: Basic Usage ===")

    # Create sample config
    config_path = create_sample_config()

    try:
        # Simple initialization and generation
        builder = Builder(config_path)
        print(f"Initialized builder: {builder}")

        # Get dataset information
        info = builder.dataset_info()
        print(f"Dataset info: {info}")

        # Note: Uncomment the line below to actually generate the dataset
        builder.generate()

    finally:
        # Cleanup
        Path(config_path).unlink(missing_ok=True)


def example_advanced_usage():
    """Example 2: Advanced usage with custom configuration."""
    print("\n=== Example 2: Advanced Usage ===")

    config_path = create_sample_config()

    try:
        # Advanced initialization with custom parameters
        builder = Builder(
            config_path=config_path,
            max_images=50,
            output_dir="./custom_dataset",
            generate_labels=True,
            keyword_generation="enabled",
            ai_model="gpt4"
        )

        # Configure additional settings
        builder.set_maxi(30)
        builder.enable_kwgen("auto")

        print(f"Advanced builder: {builder}")
        print(f"Available engines: {builder.available_engines()}")
        print(f"Search variations count: {len(builder.search_variations())}")

        # Note: Uncomment to actually generate
        # builder.generate()

    finally:
        Path(config_path).unlink(missing_ok=True)


def example_individual_operations():
    """Example 3: Using individual operations."""
    print("\n=== Example 3: Individual Operations ===")

    config_path = create_sample_config()

    try:
        builder = Builder(config_path)

        # Download images for a specific keyword
        # Note: Uncomment to actually download
        # downloaded = builder.download_images(
        #     keyword="cat",
        #     output_dir="./test_downloads",
        #     max_count=5,
        #     engines=["duckduckgo"]
        # )
        # print(f"Downloaded {downloaded} images")

        # Validate images in a directory
        # validation_result = builder.validate_images("./test_downloads")
        # print(f"Validation result: {validation_result}")

        # Generate labels for existing dataset
        # builder.generate_labels("./test_downloads")

        # Generate report
        # report_path = builder.generate_report("./test_downloads")
        # print(f"Report generated: {report_path}")

        print("Individual operations configured successfully")

    finally:
        Path(config_path).unlink(missing_ok=True)


def example_monorepo_usage():
    """Example 4: Usage across monorepo packages."""
    print("\n=== Example 4: Monorepo Integration ===")

    # This is how other packages in your monorepo can use the Builder
    config_path = create_sample_config()

    try:
        # In backend package
        def backend_service_function():
            """Example function that might be in your backend package."""
            builder = Builder(config_path, max_images=10)
            info = builder.dataset_info()
            return {
                "status": "ready",
                "dataset_name": info["dataset_name"],
                "categories": info["categories"],
                "total_keywords": info["total_keywords"]
            }

        # In another service
        def ml_training_service():
            """Example ML training service using the builder."""
            builder = Builder(
                config_path=config_path,
                max_images=100,
                generate_labels=True,
            )

            # Generate dataset for training
            # builder.generate()

            return "Dataset ready for ML training"

        # Demonstrate usage
        backend_result = backend_service_function()
        print(f"Backend service result: {backend_result}")

        ml_result = ml_training_service()
        print(f"ML service result: {ml_result}")

    finally:
        Path(config_path).unlink(missing_ok=True)


if __name__ == "__main__":
    print("PixCrawler Builder Class Examples")
    print("=" * 40)

    example_basic_usage()
    # example_advanced_usage()
    # example_individual_operations()
    # example_monorepo_usage()

    print("\n" + "=" * 40)
    print("Examples completed successfully!")
    print("\nTo use the Builder class in your monorepo:")
    print("1. Import: from builder import Builder")
    print("2. Create config file with dataset specification")
    print("3. Initialize Builder with config and options")
    print("4. Call builder.generate() or use individual methods")
