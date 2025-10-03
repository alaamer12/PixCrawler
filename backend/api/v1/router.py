"""
Main API router for v1 endpoints.
"""

from fastapi import APIRouter

from .endpoints import auth, datasets, health, users

api_router = APIRouter(prefix="/v1")

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
