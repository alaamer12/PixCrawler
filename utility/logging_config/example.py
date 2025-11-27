"""
Example usage of the logging system with Pydantic Settings.

This example demonstrates various logging configurations and features
using the LoggingSettings class and Loguru.
"""

from utility.logging_config import (
    Environment,
    LoggingSettings,
    get_logger,
    get_logging_settings,
    setup_logging,
)


def main() -> None:
    """Demonstrate the logging system with Pydantic Settings."""

    print("=== Development Environment (Default) ===")
    setup_logging(environment='development')
    logger = get_logger()

    logger.trace("This is a trace message")
    logger.debug("Debug information for development")
    logger.info("Application started successfully")
    logger.success("Operation completed successfully")
    logger.warning("This is a warning message")
    logger.error("An error occurred")

    print("\n=== Production Environment (JSON Logging) ===")
    prod_config = LoggingSettings(
        environment=Environment.PRODUCTION,
        use_json=True,
        use_colors=False
    )
    setup_logging(config=prod_config)
    logger = get_logger()

    logger.info("Production logging - structured JSON format_")
    logger.bind(user_id="user123", operation="test").info("Contextual logging")

    print("\n=== Custom Configuration ===")
    custom_config = LoggingSettings(
        environment=Environment.DEVELOPMENT,
        log_dir="./custom_logs",
        console_level="INFO",
        file_level="DEBUG"
    )
    setup_logging(config=custom_config)
    logger = get_logger()
    logger.info("Using custom configuration")

    print("\n=== Exception Handling ===")
    try:
        1 / 0
    except Exception:
        logger.exception("Caught an exception with automatic traceback")

    print("\n=== Package-specific Usage ===")
    # Simulate different packages
    builder_logger = logger.bind(package="builder")
    backend_logger = logger.bind(package="backend")

    builder_logger.info("Builder package: Starting image download")
    backend_logger.info("Backend package: API request received")

    print("\n=== Using Cached Settings ===")
    settings = get_logging_settings()
    print(f"Environment: {settings.environment.value}")
    print(f"Log directory: {settings.log_dir}")
    print(f"Console level: {settings.console_level.value}")

    print("\nCheck the 'logs' directory for output files!")


if __name__ == "__main__":
    main()
