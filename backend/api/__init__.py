"""FastAPI application initialization."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import auth, images, users

# Create FastAPI app instance
app = FastAPI(
    title="PixCrawler API",
    description="Backend API for PixCrawler - Image management system",
    version="0.0.1",
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(images.router)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to PixCrawler API",
        "version": "0.0.1",
        "docs": "/docs",
    }