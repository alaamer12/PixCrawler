"""
Pytest configuration and fixtures for backend tests.

This module provides shared fixtures and configuration for all backend tests,
including test client setup, database fixtures, and mock settings.
"""

import os
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Set test environment variables before importing Settings
os.environ["ENVIRONMENT"] = "test"
os.environ["SUPABASE_URL"] = "https://test-project.supabase.co"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test_service_role_key_" + "x" * 50
os.environ["SUPABASE_ANON_KEY"] = "test_anon_key_" + "x" * 50
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/pixcrawler_test"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["CELERY_BROKER_URL"] = "redis://localhost:6379/1"
os.environ["CELERY_RESULT_BACKEND"] = "redis://localhost:6379/1"

from backend.core.config import Settings


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """
    Create test settings instance.

    Returns:
        Settings instance configured for testing
    """
    # Clear the cache to ensure test settings are used
    # Fresh Instance
    settings = Settings()
    return settings


# noinspection PyTypeChecker
@pytest.fixture(scope="function")
def app(test_settings: Settings) -> FastAPI:
    """
    Create FastAPI application without lifespan for testing.

    Args:
        test_settings: Test settings fixture

    Returns:
        FastAPI application instance
    """
    from backend.api.v1.router import api_router
    from starlette.middleware.cors import CORSMiddleware
    from starlette.middleware.gzip import GZipMiddleware

    # Create app without lifespan to avoid Redis/DB connections
    app = FastAPI(
        title="PixCrawler API",
        description="Automated image dataset builder platform",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Add middleware (same as main.py but without rate limiting)
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=test_settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API router (api_router already has /v1 prefix)
    app.include_router(api_router, prefix="/api")

    return app


@pytest.fixture(scope="function")
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    """
    Create test client for FastAPI application.

    Args:
        app: FastAPI application fixture

    Yields:
        TestClient instance for making requests
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def mock_supabase_client() -> MagicMock:
    """
    Create mock Supabase client for testing.

    Returns:
        MagicMock instance configured as Supabase client
    """
    mock_client = MagicMock()
    mock_client.auth = MagicMock()
    mock_client.table = MagicMock()
    mock_client.storage = MagicMock()
    return mock_client


# ============================================================================
# Storage-specific fixtures
# ============================================================================

@pytest.fixture(scope="function")
def temp_storage_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for storage tests.

    Yields:
        Path to temporary directory that is automatically cleaned up
    """
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="function")
def storage_settings(temp_storage_dir: Path):
    """
    Create storage settings for testing.

    Args:
        temp_storage_dir: Temporary directory fixture

    Returns:
        StorageSettings instance configured for testing
    """
    from backend.storage.config import StorageSettings

    return StorageSettings(
        storage_provider="local",
        local_storage_path=str(temp_storage_dir)
    )


@pytest.fixture(scope="function")
def local_storage_provider(temp_storage_dir: Path):
    """
    Create LocalStorageProvider instance for testing.

    Args:
        temp_storage_dir: Temporary directory fixture

    Returns:
        LocalStorageProvider instance
    """
    from backend.storage.local import LocalStorageProvider

    return LocalStorageProvider(base_directory=temp_storage_dir)


@pytest.fixture(scope="function")
def sample_files_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for sample files.

    Yields:
        Path to temporary directory
    """
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="function")
def sample_text_file(sample_files_dir: Path) -> Path:
    """
    Create a sample text file for testing.

    Args:
        sample_files_dir: Temporary directory fixture

    Returns:
        Path to sample text file
    """

    file_path = sample_files_dir / "sample_text.txt"
    file_path.write_text("Sample content for testing")
    return file_path


@pytest.fixture(scope="function")
def sample_json_file(sample_files_dir: Path) -> Path:
    """
    Create a sample JSON file for testing.

    Args:
        sample_files_dir: Temporary directory fixture

    Returns:
        Path to sample JSON file
    """
    import json

    file_path = sample_files_dir / "sample_data.json"
    data = {
        "name": "test_dataset",
        "version": "1.0",
        "images": ["img1.jpg", "img2.jpg"],
        "metadata": {"created": "2024-01-01", "author": "test"}
    }
    file_path.write_text(json.dumps(data, indent=2))
    return file_path


@pytest.fixture(scope="function")
def sample_image_file(sample_files_dir: Path) -> Path:
    """
    Create a sample PNG image file for testing.

    Args:
        sample_files_dir: Temporary directory fixture

    Returns:
        Path to sample PNG image file
    """

    # Minimal valid PNG file (1x1 transparent pixel)
    png_data = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
        b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    file_path = sample_files_dir / "sample_image.png"
    file_path.write_bytes(png_data)
    return file_path
