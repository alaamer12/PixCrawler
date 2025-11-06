"""API endpoints for the metrics service."""

from fastapi import APIRouter

from .endpoints import metrics, system

api_router = APIRouter()
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
