"""
Main API router for v1 endpoints.
"""

from fastapi import APIRouter

from .endpoints import auth, crawl_jobs, datasets, health, storage, users, validation

api_router = APIRouter(prefix="/v1")

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(crawl_jobs.router, prefix="/jobs", tags=["crawl-jobs"])
api_router.include_router(storage.router, prefix="/storage", tags=["storage"])
api_router.include_router(validation.router, prefix="/validation", tags=["validation"])
