#!/usr/bin/env python3
"""
Example demonstrating the new Pydantic V2 Settings configuration system.

This example shows how to:
1. Load project-level and package-specific settings
2. Override settings with environment variables
3. Handle configuration validation errors
4. Use settings in your application code
"""

import os
from pydantic import ValidationError

# Import configuration classes
from config import get_project_settings
from builder._config import DatasetGenerationConfig
from validator.config import ValidatorConfig


def demonstrate_basic_usage():
    """Demonstrate basic configuration loading."""
    print("=== Basic Configuration Usage ===")
    
    # Load project-level settings
    project_settings = get_project_settings()
    print(f"Project: {project_settings.project_name} v{project_settings.project_version}")
    print(f"Development mode: {project_settings.development_mode}")
    print(f"Workspace members: {project_settings.workspace_members}")
    
    # Load package-specific settings
    builder_config = DatasetGenerationConfig()
    print(f"Builder max images: {builder_config.max_images}")
    print(f"Builder AI model: {builder_config.ai_model}")
    print(f"Builder cache file: {builder_config.cache_file}")
    
    validator_config = ValidatorConfig()
    print(f"Validator mode: {validator_config.mode}")
    print(f"Validator batch size: {validator_config.batch_size}")
    print(f"Validator hash size: {validator_config.hash_size}")


def demonstrate_environment_override():
    """Demonstrate environment variable overrides."""
    print("\n=== Environment Variable Overrides ===")
    
    # Set some environment variables
    os.environ["PIXCRAWLER_PROJECT_NAME"] = "Custom PixCrawler"
    os.environ["PIXCRAWLER_BUILDER_MAX_IMAGES"] = "25"
    os.environ["PIXCRAWLER_BUILDER_AI_MODEL"] = "gpt4"
    os.environ["PIXCRAWLER_VALIDATOR_MODE"] = "STRICT"
    os.environ["PIXCRAWLER_VALIDATOR_BATCH_SIZE"] = "200"
    
    # Reload settings to pick up environment changes
    project_settings = get_project_settings()
    builder_config = DatasetGenerationConfig()
    validator_config = ValidatorConfig()
    
    print(f"Project name (overridden): {project_settings.project_name}")
    print(f"Builder max images (overridden): {builder_config.max_images}")
    print(f"Builder AI model (overridden): {builder_config.ai_model}")
    print(f"Validator mode (overridden): {validator_config.mode}")
    print(f"Validator batch size (overridden): {validator_config.batch_size}")


def demonstrate_validation_errors():
    """Demonstrate configuration validation."""
    print("\n=== Configuration Validation ===")
    
    # Test invalid values
    test_cases = [
        ("PIXCRAWLER_BUILDER_MAX_IMAGES", "0", "Invalid max images (must be >= 1)"),
        ("PIXCRAWLER_BUILDER_AI_MODEL", "invalid-model", "Invalid AI model"),
        ("PIXCRAWLER_VALIDATOR_HASH_SIZE", "2", "Invalid hash size (must be >= 4)"),
        ("PIXCRAWLER_VALIDATOR_BATCH_SIZE", "0", "Invalid batch size (must be >= 1)"),
    ]
    
    for env_var, invalid_value, description in test_cases:
        print(f"\nTesting {description}:")
        
        # Save original value
        original_value = os.environ.get(env_var)
        
        try:
            # Set invalid value
            os.environ[env_var] = invalid_value
            
            # Try to load settings
            if "BUILDER" in env_var:
                DatasetGenerationConfig()
            elif "VALIDATOR" in env_var:
                ValidatorConfig()
            
            print(f"  ❌ Expected validation error but none occurred")
            
        except ValidationError as e:
            print(f"  ✅ Validation error caught: {e.errors()[0]['msg']}")
        
        finally:
            # Restore original value
            if original_value is not None:
                os.environ[env_var] = original_value
            else:
                os.environ.pop(env_var, None)


def demonstrate_practical_usage():
    """Demonstrate practical usage in application code."""
    print("\n=== Practical Usage Examples ===")
    
    # Example: Configuring a dataset builder
    builder_config = DatasetGenerationConfig()
    
    print("Dataset Builder Configuration:")
    print(f"  Config path: {builder_config.config_path}")
    print(f"  Max images per keyword: {builder_config.max_images}")
    print(f"  Max retries: {builder_config.max_retries}")
    print(f"  Cache file: {builder_config.cache_file}")
    print(f"  Keyword generation: {builder_config.keyword_generation}")
    print(f"  AI model: {builder_config.ai_model}")
    print(f"  Generate labels: {builder_config.generate_labels}")
    
    # Example: Configuring a validator
    validator_config = ValidatorConfig()
    
    print("\nValidator Configuration:")
    print(f"  Validation mode: {validator_config.mode}")
    print(f"  Duplicate action: {validator_config.duplicate_action}")
    print(f"  Batch size: {validator_config.batch_size}")
    print(f"  Hash size: {validator_config.hash_size}")
    print(f"  Min image size: {validator_config.min_image_width}x{validator_config.min_image_height}")
    print(f"  Generate reports: {validator_config.generate_reports}")


def demonstrate_settings_export():
    """Demonstrate exporting settings to dictionary."""
    print("\n=== Settings Export ===")
    
    # Get settings
    project_settings = get_project_settings()
    builder_config = DatasetGenerationConfig()
    validator_config = ValidatorConfig()
    
    # Export to dictionary (useful for logging, debugging, or serialization)
    project_dict = project_settings.model_dump()
    builder_dict = builder_config.model_dump()
    validator_dict = validator_config.model_dump()
    
    print("Project settings keys:", list(project_dict.keys()))
    print("Builder settings keys:", list(builder_dict.keys()))
    print("Validator settings keys:", list(validator_dict.keys()))
    
    # Example: Log configuration at startup
    print("\nConfiguration summary:")
    print(f"  Project: {project_dict['project_name']} ({project_dict['project_version']})")
    print(f"  Build target: {project_dict['build_target']}")
    print(f"  Builder max images: {builder_dict['max_images']}")
    print(f"  Builder AI model: {builder_dict['ai_model']}")
    print(f"  Validator mode: {validator_dict['mode']}")


if __name__ == "__main__":
    print("PixCrawler Configuration System Example")
    print("=" * 50)
    
    try:
        demonstrate_basic_usage()
        demonstrate_environment_override()
        demonstrate_validation_errors()
        demonstrate_practical_usage()
        demonstrate_settings_export()
        
        print("\n✅ Configuration example completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error running example: {e}")
        raise
    
    finally:
        # Clean up environment variables
        env_vars_to_clean = [
            "PIXCRAWLER_PROJECT_NAME",
            "PIXCRAWLER_BUILDER_MAX_IMAGES",
            "PIXCRAWLER_BUILDER_AI_MODEL",
            "PIXCRAWLER_VALIDATOR_MODE",
            "PIXCRAWLER_VALIDATOR_BATCH_SIZE",
        ]
        
        for var in env_vars_to_clean:
            os.environ.pop(var, None)