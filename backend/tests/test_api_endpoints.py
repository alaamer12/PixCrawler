import pytest
from fastapi import FastAPI, HTTPException, status, Depends, Query, Request
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
# ==================== MODELS ====================
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class DatasetCreate(BaseModel):
    name: str
    description: Optional[str] = None

class DatasetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class JobCreate(BaseModel):
    dataset_id: int
    name: str

class ExportRequest(BaseModel):
    dataset_id: int
    format: str

class StorageUpload(BaseModel):
    filename: str
    content_type: str

# ==================== APP SETUP ====================
app = FastAPI(title="PixCrawler API")

# Global variables
auth_service = None
db = None

class AuthService:
    def __init__(self):
        self.users_db = {}
        self.next_id = 1
    
    def verify_password(self, plain_password: str, stored_password: str) -> bool:
        return plain_password == stored_password
    
    def create_access_token(self, data: dict):
        # Simple token generation for testing
        return f"test_token_{data.get('sub')}"
    
    def create_user(self, email: str, password: str):
        if email in self.users_db:
            raise HTTPException(409, "User exists")
        user_id = self.next_id
        self.users_db[email] = {
            "id": user_id,
            "email": email,
            "password": password,
            "disabled": False
        }
        self.next_id += 1
        return {"id": user_id, "email": email}
    
    def authenticate_user(self, email: str, password: str):
        user = self.users_db.get(email)
        if not user or user["password"] != password:
            raise HTTPException(401, "Incorrect email or password")
        return {"access_token": f"test_token_{email}", "token_type": "bearer"}
    
    async def get_current_user(self, token: str = None):
        if not token or not token.startswith("test_token_"):
            raise HTTPException(status_code=401, detail="Invalid token")
        email = token.replace("test_token_", "")
        return self.users_db.get(email)

class Database:
    def __init__(self):
        self.datasets = []
        self.jobs = []
        self.exports = []
        self.storage = []
        self.next_ids = {"datasets": 1, "jobs": 1, "exports": 1, "storage": 1}
    
    def add_dataset(self, data):
        dataset = {"id": self.next_ids["datasets"], **data, "created_at": datetime.now()}
        self.datasets.append(dataset)
        self.next_ids["datasets"] += 1
        return dataset
    
    def get_dataset(self, dataset_id):
        return next((d for d in self.datasets if d["id"] == dataset_id), None)
    
    def get_datasets(self, skip: int = 0, limit: int = 100):
        return self.datasets[skip:skip + limit]
    
    def update_dataset(self, dataset_id, data):
        dataset = self.get_dataset(dataset_id)
        if dataset:
            dataset.update({k: v for k, v in data.items() if v is not None})
        return dataset
    
    def delete_dataset(self, dataset_id):
        self.datasets = [d for d in self.datasets if d["id"] != dataset_id]
        return True
    
    def add_job(self, data):
        job = {"id": self.next_ids["jobs"], **data, "status": "pending", "created_at": datetime.now()}
        self.jobs.append(job)
        self.next_ids["jobs"] += 1
        return job
    
    def add_export(self, data):
        export = {"id": self.next_ids["exports"], **data, "status": "processing", "download_url": None}
        self.exports.append(export)
        self.next_ids["exports"] += 1
        return export
    
    def add_storage(self, data):
        item = {"id": self.next_ids["storage"], **data, "created_at": datetime.now()}
        self.storage.append(item)
        self.next_ids["storage"] += 1
        return item

async def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = auth_header.split(" ")[1]
    if not token.startswith("test_token_"):
        raise HTTPException(status_code=401, detail="Invalid token")
    email = token.replace("test_token_", "")
    user = auth_service.users_db.get(email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# ==================== AUTH ENDPOINTS ====================
@app.post("/api/v1/auth/register", status_code=201)
def register(user_data: UserCreate):
    return auth_service.create_user(user_data.email, user_data.password)

@app.post("/api/v1/auth/login")
def login(credentials: UserLogin):
    return auth_service.authenticate_user(credentials.email, credentials.password)

# ==================== USER ENDPOINTS ====================
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response

@app.get("/api/v1/users/me")
async def get_current_user_endpoint(request: Request, current_user: dict = Depends(get_current_user)):
    return current_user

@app.get("/api/v1/users/{user_id}")
def get_user(user_id: int):
    return {"id": user_id, "email": f"user{user_id}@example.com"}

# ==================== DATASET ENDPOINTS ====================
@app.post("/api/v1/datasets", status_code=201)
def create_dataset(dataset: DatasetCreate, request: Request, current_user: dict = Depends(get_current_user)):
    if not dataset.name.strip():
        raise HTTPException(422, "Name cannot be empty")
    return db.add_dataset(dataset.dict())

@app.get("/api/v1/datasets")
def get_datasets(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100)):
    return db.get_datasets(skip=skip, limit=limit)

@app.get("/api/v1/datasets/{dataset_id}")
def get_dataset(dataset_id: int):
    dataset = db.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(404, "Dataset not found")
    return dataset

@app.put("/api/v1/datasets/{dataset_id}")
def update_dataset(dataset_id: int, dataset: DatasetUpdate, request: Request, current_user: dict = Depends(get_current_user)):
    updated = db.update_dataset(dataset_id, dataset.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(404, "Dataset not found")
    return updated

@app.delete("/api/v1/datasets/{dataset_id}")
def delete_dataset(dataset_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    if not db.delete_dataset(dataset_id):
        raise HTTPException(404, "Dataset not found")
    return {"message": "Dataset deleted"}

# ==================== JOB ENDPOINTS ====================
@app.post("/api/v1/jobs", status_code=201)
def create_job(job: JobCreate, request: Request, current_user: dict = Depends(get_current_user)):
    return db.add_job(job.dict())

@app.get("/api/v1/jobs")
def get_jobs(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100)):
    return db.jobs[skip:skip + limit]

@app.get("/api/v1/jobs/{job_id}")
def get_job(job_id: int):
    job = next((j for j in db.jobs if j["id"] == job_id), None)
    if not job:
        raise HTTPException(404, "Job not found")
    return job

# ==================== EXPORT ENDPOINTS ====================
@app.post("/api/v1/exports", status_code=201)
def create_export(export: ExportRequest, request: Request, current_user: dict = Depends(get_current_user)):
    return db.add_export(export.dict())

@app.get("/api/v1/exports")
def get_exports(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100)):
    return db.exports[skip:skip + limit]

# ==================== STORAGE ENDPOINTS ====================
@app.post("/api/v1/storage/upload", status_code=201)
def upload_file(upload: StorageUpload, request: Request, current_user: dict = Depends(get_current_user)):
    return db.add_storage(upload.dict())

@app.get("/api/v1/storage")
def get_storage_items(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100)):
    return db.storage[skip:skip + limit]

@app.delete("/api/v1/storage/{item_id}")
def delete_storage_item(item_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    db.storage = [item for item in db.storage if item["id"] != item_id]
    return {"message": "Storage item deleted"}

# ==================== HEALTH ENDPOINT ====================
@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

# ==================== TEST FIXTURES ====================
@pytest.fixture(autouse=True)
def reset_db():
    global auth_service, db, test_email, test_password, test_token
    
    # Initialize services
    auth_service = AuthService()
    db = Database()
    
    # Test user data
    test_email = "test@example.com"
    test_password = "password123"
    test_token = f"test_token_{test_email}"
    
    # Create test user
    auth_service.users_db[test_email] = {
        "id": 1,
        "email": test_email,
        "password": test_password,
        "disabled": False
    }
    
    # Create test dataset
    db.datasets = [{
        "id": 1,
        "name": "Test Dataset",
        "description": "Test description",
        "created_at": datetime.now()
    }]
    
    yield

# ==================== TESTS ====================
client = TestClient(app)

# Auth tests
def test_register_user():
    # Use a unique email for this test
    response = client.post(
        "/api/v1/auth/register", 
        json={"email": "newuser@example.com", "password": "password123"}
    )
    assert response.status_code == 201
    assert "id" in response.json()
    assert response.json()["email"] == "newuser@example.com"

def test_register_duplicate_user():
    client.post("/api/v1/auth/register", json={"email": "duplicate@example.com", "password": "password123"})
    response = client.post("/api/v1/auth/register", json={"email": "duplicate@example.com", "password": "password123"})
    assert response.status_code == 409

def test_login_success():
    client.post("/api/v1/auth/register", json={"email": "login@example.com", "password": "password123"})
    response = client.post("/api/v1/auth/login", json={"email": "login@example.com", "password": "password123"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_login_invalid_credentials():
    response = client.post("/api/v1/auth/login", json={"email": "nonexistent@example.com", "password": "wrong"})
    assert response.status_code == 401

# User tests
def test_get_current_user():
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == test_email

def test_get_user_by_id():
    response = client.get("/api/v1/users/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1

# Dataset CRUD tests
def test_create_dataset():
    response = client.post(
        "/api/v1/datasets",
        json={"name": "New Dataset", "description": "New Description"},
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "New Dataset"

def test_get_datasets():
    response = client.get("/api/v1/datasets/")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Test Dataset"

def test_get_dataset_by_id():
    response = client.get("/api/v1/datasets/1")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Dataset"

def test_get_nonexistent_dataset():
    response = client.get("/api/v1/datasets/999")
    assert response.status_code == 404

def test_update_dataset():
    # Add test dataset directly
    test_ds = {"id": 100, "name": "To Update", "description": "Old"}
    db.datasets.append(test_ds)
    
    response = client.put(
        "/api/v1/datasets/100",
        json={"name": "Updated"},
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated"

def test_delete_dataset():
    # Add test dataset directly
    test_ds = {"id": 101, "name": "To Delete", "description": "Delete me"}
    db.datasets.append(test_ds)
    
    response = client.delete(
        "/api/v1/datasets/101",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200

# Job tests
def test_create_job():
    response = client.post(
        "/api/v1/jobs/",
        json={"dataset_id": 1, "name": "Test Job"},
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Job"
    
    # Clean up
    db.jobs = []

def test_get_jobs():
    response = client.get("/api/v1/jobs?skip=0&limit=10")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_job_by_id():
    # Add test job directly
    test_job = {"id": 100, "dataset_id": 1, "name": "Test Job"}
    db.jobs.append(test_job)
    
    response = client.get(
        "/api/v1/jobs/100",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Test Job"

# Export tests
def test_create_export():
    response = client.post(
        "/api/v1/exports/",
        json={"dataset_id": 1, "format": "csv"},
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 201
    assert response.json()["format"] == "csv"
    
    # Clean up
    db.exports = []

def test_get_exports():
    response = client.get("/api/v1/exports?skip=0&limit=10")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# Storage tests
def test_upload_file():
    response = client.post(
        "/api/v1/storage/upload",
        json={"filename": "test.txt", "content_type": "text/plain"},
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 201
    assert response.json()["filename"] == "test.txt"
    
    # Clean up
    db.storage = []

def test_get_storage_items():
    response = client.get("/api/v1/storage?skip=0&limit=10")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_delete_storage_item():
    # Add test storage item directly
    test_item = {"id": 100, "filename": "delete.txt", "content_type": "text/plain"}
    db.storage.append(test_item)
    
    response = client.delete(
        "/api/v1/storage/100",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200

# Health test
def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

# Validation tests
def test_register_invalid_email():
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "invalid-email", "password": "password123"}
    )
    assert response.status_code == 422
    
def test_auth_service_verify_password():
    auth = AuthService()
    assert auth.verify_password("test", "test") == True
    assert auth.verify_password("test", "wrong") == False

def test_auth_service_create_access_token():
    auth = AuthService()
    token = auth.create_access_token({"sub": "test@example.com"})
    assert token == "test_token_test@example.com"

def test_get_current_user_invalid_token():
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401

def test_get_current_user_missing_token():
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401

def test_login_invalid_credentials():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "wrong"}
    )
    assert response.status_code == 401

def test_create_dataset_invalid_data():
    response = client.post(
        "/api/v1/datasets",
        json={"name": ""},
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 422

# Pagination tests
def test_datasets_pagination():
    # Add test datasets directly
    db.datasets = [
        {"id": i, "name": f"Dataset {i}", "created_at": datetime.now()}
        for i in range(1, 6)  # 5 test datasets
    ]
    
    # Test basic pagination
    response = client.get(
        "/api/v1/datasets?skip=2&limit=2",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    assert len(response.json()) == 2
    
    # Test skip beyond dataset count
    response = client.get(
        "/api/v1/datasets?skip=10&limit=2",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    assert len(response.json()) == 0
    
    # Test invalid limit (should be between 1-100)
    response = client.get(
        "/api/v1/datasets?skip=0&limit=0",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 422
    
    # Test invalid skip (should be >= 0)
    response = client.get(
        "/api/v1/datasets?skip=-1&limit=10",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 422

if __name__ == "__main__":
    pytest.main([__file__, "-v"])