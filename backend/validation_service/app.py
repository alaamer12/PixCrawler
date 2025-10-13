from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
from datetime import datetime
import uuid
import asyncio
import logging
from typing import Dict, List, Optional, Any
from enum import Enum
import os

# Configuration
class Config:
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "bmp", "webp"}
    MAX_BATCH_SIZE = 50

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Validation Service API", version="1.0.0")

class ValidationLevel(Enum):
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"

class ValidationStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ValidationResult(BaseModel):
    image_id: str
    is_valid: bool
    confidence: float
    issues: List[str]
    metadata: Dict[str, Any]
    
    @validator('confidence')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v

class ValidationJob(BaseModel):
    job_id: str
    status: ValidationStatus
    created_at: str
    completed_at: Optional[str]
    total_images: int
    processed_images: int
    results: List[ValidationResult]

class ValidationLevelRequest(BaseModel):
    dataset_id: str
    validation_level: ValidationLevel

# In-memory storage (in production, use a proper database)
validation_jobs: Dict[str, ValidationJob] = {}
dataset_stats: Dict[str, Dict[str, Any]] = {}
dataset_validation_levels: Dict[str, ValidationLevel] = {}

def validate_file(file: UploadFile) -> None:
    """Validate uploaded file"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")
    
    # Check file extension
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in Config.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: {', '.join(Config.ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size (this is approximate, actual size check happens during read)
    if hasattr(file, 'size') and file.size and file.size > Config.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, 
            detail=f"File too large. Maximum size: {Config.MAX_FILE_SIZE // (1024*1024)}MB"
        )

def validate_image(image_data: bytes, validation_level: ValidationLevel = ValidationLevel.STANDARD) -> ValidationResult:
    """Mock validation logic - replace with actual image validation"""
    image_id = str(uuid.uuid4())
    
    # Mock validation results based on level
    if validation_level == ValidationLevel.BASIC:
        is_valid = True
        confidence = 0.85
        issues = []
    elif validation_level == ValidationLevel.STANDARD:
        is_valid = len(image_data) > 1000  # Mock check
        confidence = 0.92
        issues = [] if is_valid else ["Image too small"]
    else:  # STRICT
        is_valid = len(image_data) > 5000  # Mock stricter check
        confidence = 0.95
        issues = [] if is_valid else ["Image does not meet strict quality standards"]
    
    return ValidationResult(
        image_id=image_id,
        is_valid=is_valid,
        confidence=confidence,
        issues=issues,
        metadata={"size": len(image_data), "validation_level": validation_level.value}
    )

@app.post("/api/v1/validation/analyze/")
async def analyze_single_image(
    image: UploadFile = File(...),
    validation_level: ValidationLevel = Form(ValidationLevel.STANDARD)
):
    """Analyze single image endpoint"""
    try:
        validate_file(image)
        
        image_data = await image.read()
        
        # Check actual file size after reading
        if len(image_data) > Config.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size: {Config.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        logger.info(f"Processing single image: {image.filename}, size: {len(image_data)} bytes")
        
        result = validate_image(image_data, validation_level)
        
        return {
            "result": result.dict(),
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing image {image.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during image processing")

async def process_single_image_async(image_file: UploadFile, validation_level: ValidationLevel) -> Optional[ValidationResult]:
    """Process a single image asynchronously"""
    try:
        if not image_file.filename:
            return None
            
        validate_file(image_file)
        image_data = await image_file.read()
        
        if len(image_data) > Config.MAX_FILE_SIZE:
            logger.warning(f"Skipping large file: {image_file.filename}")
            return None
            
        return validate_image(image_data, validation_level)
    except Exception as e:
        logger.error(f"Error processing image {image_file.filename}: {str(e)}")
        return None

@app.post("/api/v1/validation/batch/")
async def batch_validation(
    images: List[UploadFile] = File(...),
    validation_level: ValidationLevel = Form(ValidationLevel.STANDARD)
):
    """Batch validation endpoint"""
    try:
        if not images:
            raise HTTPException(status_code=400, detail="No image files provided")
        
        if len(images) > Config.MAX_BATCH_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"Too many files. Maximum batch size: {Config.MAX_BATCH_SIZE}"
            )
        
        job_id = str(uuid.uuid4())
        logger.info(f"Starting batch validation job {job_id} with {len(images)} images")
        
        # Create validation job
        job = ValidationJob(
            job_id=job_id,
            status=ValidationStatus.PROCESSING,
            created_at=datetime.now().isoformat(),
            completed_at=None,
            total_images=len(images),
            processed_images=0,
            results=[]
        )
        
        # Store job immediately
        validation_jobs[job_id] = job
        
        # Process images concurrently
        tasks = [process_single_image_async(image_file, validation_level) for image_file in images]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        for result in results:
            if isinstance(result, ValidationResult):
                job.results.append(result)
                job.processed_images += 1
        
        job.status = ValidationStatus.COMPLETED
        job.completed_at = datetime.now().isoformat()
        validation_jobs[job_id] = job
        
        logger.info(f"Completed batch validation job {job_id}: {job.processed_images}/{job.total_images} successful")
        
        return {
            "job_id": job_id,
            "status": job.status.value,
            "total_images": job.total_images,
            "processed_images": job.processed_images,
            "message": "Batch validation completed"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch validation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during batch processing")

@app.get("/api/v1/validation/results/{job_id}/")
async def get_validation_results(job_id: str):
    """Get validation results endpoint"""
    try:
        if job_id not in validation_jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = validation_jobs[job_id]
        logger.info(f"Retrieved results for job {job_id}")
        
        return {
            "job_id": job.job_id,
            "status": job.status.value,
            "created_at": job.created_at,
            "completed_at": job.completed_at,
            "total_images": job.total_images,
            "processed_images": job.processed_images,
            "results": [result.dict() for result in job.results]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving job results {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/validation/stats/{dataset_id}/")
async def get_dataset_stats(dataset_id: str):
    """Get dataset validation stats endpoint"""
    try:
        if dataset_id not in dataset_stats:
            # Generate mock stats if dataset doesn't exist
            dataset_stats[dataset_id] = {
                "dataset_id": dataset_id,
                "total_images": 0,
                "valid_images": 0,
                "invalid_images": 0,
                "validation_level": dataset_validation_levels.get(dataset_id, ValidationLevel.STANDARD).value,
                "last_updated": datetime.now().isoformat(),
                "average_confidence": 0.0,
                "common_issues": []
            }
        
        stats = dataset_stats[dataset_id]
        logger.info(f"Retrieved stats for dataset {dataset_id}")
        
        return stats
    
    except Exception as e:
        logger.error(f"Error retrieving dataset stats {dataset_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/api/v1/validation/level/")
async def change_validation_level(request: ValidationLevelRequest):
    """Change validation level for dataset endpoint"""
    try:
        dataset_validation_levels[request.dataset_id] = request.validation_level
        
        # Update dataset stats if exists
        if request.dataset_id in dataset_stats:
            dataset_stats[request.dataset_id]['validation_level'] = request.validation_level.value
            dataset_stats[request.dataset_id]['last_updated'] = datetime.now().isoformat()
        
        logger.info(f"Updated validation level for dataset {request.dataset_id} to {request.validation_level.value}")
        
        return {
            "dataset_id": request.dataset_id,
            "validation_level": request.validation_level.value,
            "updated_at": datetime.now().isoformat(),
            "message": "Validation level updated successfully"
        }
    
    except Exception as e:
        logger.error(f"Error updating validation level for dataset {request.dataset_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
