"""
Example usage of the simplified logging system.
"""

from logging_config import setup_logging, get_logger


def main():
    """Demonstrate the simplified logging system."""

    print("=== Development Environment ===")
    setup_logging(environment='development')
    logger = get_logger()

    logger.trace("This is a trace message")
    logger.debug("Debug information for development")
    logger.info("Application started successfully")
    logger.success("Operation completed successfully")
    logger.warning("This is a warning message")
    logger.error("An error occurred")

    print("\n=== Production Environment ===")
    setup_logging(environment='production')
    logger = get_logger()

    logger.info("Production logging - structured format")
    logger.bind(user_id="user123", operation="test").info("Contextual logging")

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

    print("\nCheck the 'logs' directory for output files!")


if __name__ == "__main__":
    main()
