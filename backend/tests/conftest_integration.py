"""
Integration test fixtures for backend integration testing.

This module provides specialized fixtures for integration tests that require
mocked external services while using real database/service interactions.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from typing import AsyncGenerator, Generator
from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture
async def async_db_session():
    """
    Create an async database session for integration tests.
    
    Yields:
        AsyncSession instance for database operations
    """
    from backend.database.connection import AsyncSessionLocal
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ============================================================================
# Builder Mocks
# ============================================================================

@pytest.fixture
def mock_builder():
    """
    Create a pre-configured Builder mock with async generator support.
    
    The mock simulates the Builder's generate_async_batches method
    which yields batches of image results.
    
    Returns:
        MagicMock configured to simulate Builder behavior
    """
    mock = MagicMock()
    
    # Configure the mock instance
    mock_instance = MagicMock()
    mock.return_value = mock_instance
    
    # Create async generator for generate_async_batches
    async def mock_async_gen(batch_size: int = 50):
        """Yield mock image batches."""
        yield [
            {
                "original_url": "http://example.com/img1.jpg",
                "filename": "img1.jpg",
                "is_valid": True,
                "width": 800,
                "height": 600,
                "format": "jpeg"
            },
            {
                "original_url": "http://example.com/img2.jpg",
                "filename": "img2.jpg",
                "is_valid": True,
                "width": 1024,
                "height": 768,
                "format": "jpeg"
            }
        ]
        yield [
            {
                "original_url": "http://example.com/img3.jpg",
                "filename": "img3.jpg",
                "is_valid": True,
                "width": 640,
                "height": 480,
                "format": "png"
            }
        ]
    
    mock_instance.generate_async_batches = lambda batch_size=50: mock_async_gen(batch_size)
    mock_instance.cleanup = MagicMock()
    mock_instance.get_stats = MagicMock(return_value={
        "total_downloaded": 3,
        "total_valid": 3,
        "total_failed": 0
    })
    
    return mock


@pytest.fixture
def mock_builder_with_errors():
    """
    Create a Builder mock that simulates error scenarios.
    
    Returns:
        MagicMock configured to simulate Builder failures
    """
    mock = MagicMock()
    mock_instance = MagicMock()
    mock.return_value = mock_instance
    
    async def mock_async_gen_with_error(batch_size: int = 50):
        """Yield one batch then raise an error."""
        yield [
            {
                "original_url": "http://example.com/img1.jpg",
                "filename": "img1.jpg",
                "is_valid": True
            }
        ]
        raise Exception("Network error during crawl")
    
    mock_instance.generate_async_batches = lambda batch_size=50: mock_async_gen_with_error(batch_size)
    mock_instance.cleanup = MagicMock()
    
    return mock


# ============================================================================
# Validator Mocks
# ============================================================================

@pytest.fixture
def mock_validator():
    """
    Create a pre-configured CheckManager mock for validation tests.
    
    Returns:
        MagicMock configured to simulate CheckManager behavior
    """
    mock = MagicMock()
    
    # Mock validation results
    mock.validate_image.return_value = {
        "is_valid": True,
        "quality_score": 0.85,
        "checks": {
            "format": True,
            "dimensions": True,
            "corruption": False,
            "blur": False
        }
    }
    
    mock.validate_batch.return_value = [
        {"image_id": 1, "is_valid": True, "quality_score": 0.85},
        {"image_id": 2, "is_valid": True, "quality_score": 0.92},
        {"image_id": 3, "is_valid": False, "quality_score": 0.45, "reason": "blur_detected"}
    ]
    
    return mock


# ============================================================================
# Celery Mocks
# ============================================================================

@pytest.fixture
def mock_celery_app():
    """
    Create a Celery app mock configured for synchronous execution.
    
    This allows testing Celery task logic without a running broker.
    
    Returns:
        MagicMock configured to simulate Celery app
    """
    mock_app = MagicMock()
    
    # Mock the control.inspect for worker monitoring
    mock_inspect = MagicMock()
    mock_inspect.active.return_value = {}
    mock_inspect.reserved.return_value = {}
    mock_inspect.stats.return_value = {}
    mock_app.control.inspect.return_value = mock_inspect
    
    # Mock conf
    mock_app.conf = MagicMock()
    mock_app.conf.broker_url = "memory://"
    mock_app.conf.result_backend = "cache+memory://"
    mock_app.main = "pixcrawler"
    
    return mock_app


@pytest.fixture
def mock_celery_task_request():
    """
    Create a mock Celery task request object.
    
    Returns:
        MagicMock simulating task.request
    """
    mock_request = MagicMock()
    mock_request.id = str(uuid4())
    mock_request.hostname = "worker@test"
    mock_request.retries = 0
    
    return mock_request


# ============================================================================
# Authentication Fixtures
# ============================================================================

@pytest.fixture
def mock_auth_user():
    """
    Create a mock authenticated user.
    
    Returns:
        Dictionary representing authenticated user data
    """
    user_id = str(uuid4())
    return {
        "user_id": user_id,
        "email": "test@example.com",
        "tier": "free",
        "onboarding_completed": True
    }


@pytest.fixture
def authenticated_client(app: FastAPI, mock_auth_user: dict) -> Generator[TestClient, None, None]:
    """
    Create a TestClient with pre-configured authentication.
    
    Args:
        app: FastAPI application fixture
        mock_auth_user: Mock user data fixture
        
    Yields:
        TestClient with authentication headers set
    """
    from backend.api.dependencies import get_current_user
    
    async def override_get_current_user():
        return mock_auth_user
    
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    with TestClient(app) as client:
        # Set a mock authorization header
        client.headers["Authorization"] = "Bearer mock_token_for_testing"
        yield client
    
    # Clean up
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def secondary_auth_user():
    """
    Create a second mock user for isolation tests.
    
    Returns:
        Dictionary representing second user data
    """
    return {
        "user_id": str(uuid4()),
        "email": "other@example.com",
        "tier": "free",
        "onboarding_completed": True
    }


# ============================================================================
# Storage Fixtures
# ============================================================================

@pytest.fixture
def mock_storage_provider():
    """
    Create a mock storage provider for integration tests.
    
    Returns:
        MagicMock simulating StorageProvider
    """
    mock = MagicMock()
    
    # Track uploaded files
    _files = {}
    
    def mock_upload(source, dest):
        _files[dest] = source
        return dest
    
    def mock_download(source, dest):
        if source not in _files:
            raise FileNotFoundError(f"File not found: {source}")
        return dest
    
    def mock_list_files(prefix=None):
        if prefix:
            return [f for f in _files.keys() if f.startswith(prefix)]
        return list(_files.keys())
    
    def mock_delete(path):
        if path not in _files:
            raise FileNotFoundError(f"File not found: {path}")
        del _files[path]
    
    mock.upload = mock_upload
    mock.download = mock_download
    mock.list_files = mock_list_files
    mock.delete = mock_delete
    mock.generate_presigned_url = lambda path, expires_in=3600: f"file://{path}"
    mock._files = _files
    
    return mock


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_project_data(mock_auth_user: dict) -> dict:
    """
    Create sample project data for tests.
    
    Args:
        mock_auth_user: Mock user fixture
        
    Returns:
        Dictionary with project creation data
    """
    return {
        "name": "Integration Test Project",
        "description": "Project for integration testing",
        "user_id": mock_auth_user["user_id"]
    }


@pytest.fixture
def sample_job_data() -> dict:
    """
    Create sample crawl job data for tests.
    
    Returns:
        Dictionary with job creation data
    """
    return {
        "name": "Integration Test Job",
        "keywords": ["test", "integration", "images"],
        "max_images": 10,
        "engines": ["google", "bing"]
    }


@pytest.fixture
def sample_image_data() -> list:
    """
    Create sample image metadata for tests.
    
    Returns:
        List of image metadata dictionaries
    """
    return [
        {
            "original_url": "http://example.com/img1.jpg",
            "filename": "img1.jpg",
            "width": 800,
            "height": 600,
            "format_": "jpeg",
            "file_size": 102400,
            "is_valid": True
        },
        {
            "original_url": "http://example.com/img2.jpg",
            "filename": "img2.jpg",
            "width": 1024,
            "height": 768,
            "format_": "jpeg",
            "file_size": 153600,
            "is_valid": True
        },
        {
            "original_url": "http://example.com/img3.png",
            "filename": "img3.png",
            "width": 640,
            "height": 480,
            "format_": "png",
            "file_size": 81920,
            "is_valid": False
        }
    ]
