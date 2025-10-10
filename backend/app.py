import os
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from storage.factory import get_storage_provider
from storage.management import router as storage_router

# Create FastAPI app
app = FastAPI(
    title="PixCrawler API",
    description="API for PixCrawler - Image Crawling and Management System",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize storage
storage = get_storage_provider()

# Include routers
app.include_router(storage_router)

# Legacy endpoints (kept for backward compatibility)
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Legacy upload endpoint"""
    destination = f"uploads/{file.filename}"
    with open(file.filename, "wb") as buffer:
        buffer.write(await file.read())
    storage.upload(file.filename, destination)
    os.remove(file.filename)
    return {"message": "Uploaded successfully", "path": destination}

@app.get("/download")
def download_file(path: str):
    """Legacy download endpoint"""
    destination = f"downloaded_{os.path.basename(path)}"
    storage.download(path, destination)
    return {"message": "Downloaded", "saved_as": destination}

@app.delete("/delete")
def delete_file(path: str):
    """Legacy delete endpoint"""
    storage.delete(path)
    return {"message": "Deleted"}

@app.get("/list")
def list_files():
    """Legacy list files endpoint"""
    return storage.list_files()

@app.get("/url")
def presigned_url(path: str):
    """Legacy presigned URL endpoint"""
    return {"url": storage.generate_presigned_url(path)}
