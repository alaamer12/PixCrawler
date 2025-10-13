"""
PixCrawler Backend API Server

Main application entry point for the PixCrawler backend service.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.v1.router import api_router
from backend.core.config import get_settings
from backend.core.exceptions import setup_exception_handlers
from backend.core.middleware import setup_middleware


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="PixCrawler API",
        description="Automated image dataset builder platform",
        version="1.0.0",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
    )

    # Setup CORS
    # noinspection PyTypeChecker
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Setup custom middleware
    setup_middleware(app)

    # Setup exception handlers
    setup_exception_handlers(app)

    # Include API routes
    app.include_router(api_router, prefix="/api")

    return app


app = create_app()


def main() -> None:
    """Run the application server."""
    settings = get_settings()
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
