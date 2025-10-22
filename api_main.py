"""
Minimal FastAPI application for testing Azure deployment of PixCrawler.

This API provides endpoints to:
1. Trigger dataset generation on the cloud
2. Retrieve URLs for generated images
3. Serve generated images via HTTP

Endpoints:
    POST /api/generate: Start dataset generation
    GET /api/status/{job_id}: Check generation status
    GET /api/images/{job_id}: List all generated image URLs
    GET /images/{job_id}/{filename}: Serve individual images
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from _exceptions import PixCrawlerError
from config import DatasetGenerationConfig
from generator import generate_dataset

__all__ = ["app", "GenerateRequest", "GenerateResponse", "StatusResponse", "ImageListResponse"]

# Initialize FastAPI app
app = FastAPI(
    title="PixCrawler API",
    description="Minimal API for testing Azure deployment",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job tracking (use Redis/DB in production)
jobs: Dict[str, Dict[str, Any]] = {}


class GenerateRequest(BaseModel):
    """Request model for dataset generation."""
    
    dataset_name: str = Field(..., description="Name of the dataset")
    categories: Dict[str, List[str]] = Field(..., description="Categories with keywords")
    max_images: int = Field(default=10, ge=1, le=100, description="Max images per keyword")
    keyword_generation: str = Field(default="auto", description="Keyword generation mode")
    ai_model: str = Field(default="gpt4-mini", description="AI model for keyword generation")
    generate_labels: bool = Field(default=False, description="Generate label files")
    
    class Config:
        json_schema_extra = {
            "example": {
                "dataset_name": "test_dataset",
                "categories": {
                    "animals": ["cat", "dog"],
                    "vehicles": ["car"]
                },
                "max_images": 10,
                "keyword_generation": "auto",
                "ai_model": "gpt4-mini",
                "generate_labels": False
            }
        }


class GenerateResponse(BaseModel):
    """Response model for generation request."""
    
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status")
    message: str = Field(..., description="Status message")
    created_at: str = Field(..., description="Job creation timestamp")


class StatusResponse(BaseModel):
    """Response model for job status."""
    
    job_id: str
    status: str
    dataset_name: Optional[str] = None
    output_dir: Optional[str] = None
    total_images: Optional[int] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


class ImageListResponse(BaseModel):
    """Response model for image list."""
    
    job_id: str
    dataset_name: str
    total_images: int
    images: List[Dict[str, str]]


def run_generation_task(job_id: str, request: GenerateRequest) -> None:
    """
    Background task to run dataset generation.
    
    Args:
        job_id: Unique job identifier
        request: Generation request parameters
    """
    try:
        # Update job status
        jobs[job_id]["status"] = "running"
        
        # Create temporary config file
        config_data = {
            "dataset_name": request.dataset_name,
            "categories": request.categories,
            "options": {
                "max_images": request.max_images,
                "generate_labels": request.generate_labels,
                "keyword_generation": request.keyword_generation,
                "ai_model": request.ai_model
            }
        }
        
        # Use job-specific config and output directory
        config_path = f"temp_config_{job_id}.json"
        output_dir = f"datasets/{job_id}_{request.dataset_name}"
        
        with open(config_path, "w") as f:
            json.dump(config_data, f, indent=2)
        
        # Create configuration
        config = DatasetGenerationConfig(
            config_path=config_path,
            max_images=request.max_images,
            output_dir=output_dir,
            integrity=True,
            max_retries=3,
            continue_from_last=False,
            cache_file=f"cache_{job_id}.json",
            keyword_generation=request.keyword_generation,
            ai_model=request.ai_model,
            generate_labels=request.generate_labels
        )
        
        # Generate dataset
        generate_dataset(config)
        
        # Count generated images
        output_path = Path(output_dir)
        image_count = 0
        if output_path.exists():
            image_count = sum(1 for f in output_path.rglob("*") 
                            if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif'])
        
        # Update job status
        jobs[job_id].update({
            "status": "completed",
            "output_dir": output_dir,
            "total_images": image_count,
            "completed_at": datetime.utcnow().isoformat()
        })
        
        # Cleanup temp config
        if os.path.exists(config_path):
            os.remove(config_path)
            
    except PixCrawlerError as e:
        jobs[job_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat()
        })
    except Exception as e:
        jobs[job_id].update({
            "status": "failed",
            "error": f"Unexpected error: {str(e)}",
            "completed_at": datetime.utcnow().isoformat()
        })


@app.get("/", tags=["Health"])
async def root() -> Dict[str, str]:
    """
    Root endpoint for health check.
    
    Returns:
        Dict with status and message
    """
    return {
        "status": "healthy",
        "message": "PixCrawler API is running",
        "version": "0.1.0"
    }


@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint for Azure monitoring.
    
    Returns:
        Dict with health status
    """
    return {"status": "healthy"}


@app.post("/api/generate", response_model=GenerateResponse, tags=["Generation"])
async def generate(
    request: GenerateRequest,
    background_tasks: BackgroundTasks
) -> GenerateResponse:
    """
    Trigger dataset generation in the background.
    
    Args:
        request: Generation request parameters
        background_tasks: FastAPI background tasks
        
    Returns:
        GenerateResponse with job details
    """
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Initialize job tracking
    jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "dataset_name": request.dataset_name,
        "created_at": datetime.utcnow().isoformat(),
        "output_dir": None,
        "total_images": None,
        "error": None,
        "completed_at": None
    }
    
    # Add background task
    background_tasks.add_task(run_generation_task, job_id, request)
    
    return GenerateResponse(
        job_id=job_id,
        status="pending",
        message="Dataset generation started",
        created_at=jobs[job_id]["created_at"]
    )


@app.get("/api/status/{job_id}", response_model=StatusResponse, tags=["Status"])
async def get_status(job_id: str) -> StatusResponse:
    """
    Get the status of a generation job.
    
    Args:
        job_id: Unique job identifier
        
    Returns:
        StatusResponse with job status
        
    Raises:
        HTTPException: If job not found
    """
    if job_id not in jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    job = jobs[job_id]
    return StatusResponse(**job)


@app.get("/api/images/{job_id}", response_model=ImageListResponse, tags=["Images"])
async def list_images(job_id: str) -> ImageListResponse:
    """
    List all generated images for a job with their URLs.
    
    Args:
        job_id: Unique job identifier
        
    Returns:
        ImageListResponse with image URLs
        
    Raises:
        HTTPException: If job not found or not completed
    """
    if job_id not in jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    job = jobs[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not completed. Current status: {job['status']}"
        )
    
    output_dir = job["output_dir"]
    if not output_dir or not os.path.exists(output_dir):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output directory not found"
        )
    
    # Collect all images
    images = []
    output_path = Path(output_dir)
    
    for image_file in output_path.rglob("*"):
        if image_file.is_file() and image_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
            # Get relative path from output directory
            rel_path = image_file.relative_to(output_path)
            category = rel_path.parts[0] if len(rel_path.parts) > 1 else "uncategorized"
            
            images.append({
                "filename": image_file.name,
                "category": category,
                "url": f"/images/{job_id}/{rel_path.as_posix()}",
                "size_bytes": image_file.stat().st_size
            })
    
    return ImageListResponse(
        job_id=job_id,
        dataset_name=job["dataset_name"],
        total_images=len(images),
        images=images
    )


@app.get("/images/{job_id}/{path:path}", tags=["Images"])
async def serve_image(job_id: str, path: str) -> FileResponse:
    """
    Serve a generated image file.
    
    Args:
        job_id: Unique job identifier
        path: Relative path to the image
        
    Returns:
        FileResponse with the image
        
    Raises:
        HTTPException: If job or image not found
    """
    if job_id not in jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    job = jobs[job_id]
    output_dir = job["output_dir"]
    
    if not output_dir:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output directory not found"
        )
    
    # Construct full path
    image_path = Path(output_dir) / path
    
    # Security check: ensure path is within output directory
    try:
        image_path = image_path.resolve()
        output_path = Path(output_dir).resolve()
        if not str(image_path).startswith(str(output_path)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid path"
        )
    
    if not image_path.exists() or not image_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    return FileResponse(
        path=str(image_path),
        media_type="image/jpeg",
        filename=image_path.name
    )


@app.get("/api/jobs", tags=["Status"])
async def list_jobs() -> Dict[str, Any]:
    """
    List all jobs and their statuses.
    
    Returns:
        Dict with all jobs
    """
    return {
        "total_jobs": len(jobs),
        "jobs": list(jobs.values())
    }


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "api_main:app",
        # host="0.0.0.0",
        # port=8000,
        reload=False
    )
