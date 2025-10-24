"""
Pytest configuration and fixtures for backend tests.

This module provides shared fixtures and configuration for all backend tests,
including test client setup, database fixtures, and mock settings.
"""

import os
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

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

from backend.core.config import Settings, get_settings


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """
    Create test settings instance.
    
    Returns:
        Settings instance configured for testing
    """
    # Clear the cache to ensure test settings are used
    get_settings.cache_clear()
    settings = get_settings()
    return settings


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


@pytest.fixture(autouse=True)
def reset_settings_cache():
    """
    Reset settings cache before each test.
    
    This ensures each test gets fresh settings and prevents
    test pollution from cached values.
    """
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
