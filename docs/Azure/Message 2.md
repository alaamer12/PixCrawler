# Message 2

# Azure App Service Deployment Guide: Storage, Celery, and Docker

A comprehensive guide covering persistent storage, background task processing, and containerization on Azure App Service.

---

## Table of Contents

1. [Adding ZIP Download Functionality](https://claude.ai/chat/1a03e62b-f497-458e-955a-ff45653452f7#zip-download)
2. [Understanding Ephemeral Storage](https://claude.ai/chat/1a03e62b-f497-458e-955a-ff45653452f7#ephemeral-storage)
3. [Celery Integration Options](https://claude.ai/chat/1a03e62b-f497-458e-955a-ff45653452f7#celery-integration)
4. [Redis Deployment Strategies](https://claude.ai/chat/1a03e62b-f497-458e-955a-ff45653452f7#redis-strategies)
5. [Docker on App Service](https://claude.ai/chat/1a03e62b-f497-458e-955a-ff45653452f7#docker-deployment)

---

## 1. Adding ZIP Download Functionality {#zip-download}

### Creating a ZIP Download Endpoint

Add this endpoint to your `api_main.py`:

```python
import zipfile
import io
from fastapi.responses import StreamingResponse

@app.get("/api/download/{job_id}")
async def download_dataset_zip(job_id: str):
    """
    Download entire dataset as a ZIP file.

    Args:
        job_id: Job ID to download

    Returns:
        ZIP file containing all images
    """
    job_dir = DOWNLOADS_DIR / job_id

    if not job_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    # Create ZIP in memory
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Walk through all files in job directory
        for file_path in job_dir.rglob('*'):
            if file_path.is_file():
                # Add file to ZIP with relative path
                arcname = file_path.relative_to(job_dir)
                zip_file.write(file_path, arcname=arcname)

    # Reset buffer position
    zip_buffer.seek(0)

    # Return as streaming response
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={job_id}.zip"
        }
    )

```

### Using the ZIP Download

**Via Python:**

```python
import requests

job_id = "28ade4cd-7f12-4f0a-b4a5-c649867d0e82"
base_url = "https://your-app.azurewebsites.net"

response = requests.get(f"{base_url}/api/download/{job_id}", stream=True)
response.raise_for_status()

with open(f"{job_id}.zip", "wb") as f:
    for chunk in response.iter_content(chunk_size=8192):
        f.write(chunk)

print(f"✅ Downloaded {job_id}.zip")

```

**Via Browser:**
Simply visit: `https://your-app.azurewebsites.net/api/download/{job_id}`

### ZIP vs File-by-File Download

| Approach | Pros | Cons |
| --- | --- | --- |
| **ZIP Download** | ✅ One click/request<br>✅ Preserves folder structure<br>✅ Easy for users | ❌ Uses more server memory<br>❌ Slower for large datasets<br>❌ All-or-nothing |
| **File-by-File** | ✅ Lower memory usage<br>✅ Can resume individual files<br>✅ Progress tracking | ❌ Multiple requests<br>❌ Requires script/tool |

**Recommendation:** For small datasets (5-50 images), ZIP download is simpler for users.

---

## 2. Understanding Ephemeral Storage {#ephemeral-storage}

### The Reality of Azure App Service Storage

**Critical Insight:** All job data will be lost on restart. ⚠️

### Why Data is Lost

Azure App Service uses **ephemeral storage** across all tiers:

- **App Restart:** All files in `/tmp/` or `/home/site/wwwroot/downloads/` are deleted
- **App Stop/Start:** Container is destroyed → all data gone
- **Deployment:** New container created → old data lost
- **Scale/Move:** Container recreated → data lost

### Storage Capacity by Tier

| Tier | Local Disk | RAM | Notes |
| --- | --- | --- | --- |
| Free F1 | 1 GB | 1 GB | Shared CPU |
| Basic B1 | **10 GB** | 1.75 GB | Your current tier |
| Basic B2/B3 | 10 GB | 3.5-7 GB |  |
| Standard S1-S3 | 50 GB | 1.75-7 GB |  |
| Premium P1V2-P3V2 | 250 GB | 3.5-14 GB |  |
| Premium P1V3-P3V3 | 250 GB | 8-32 GB | Faster CPU |
| Isolated I1 | 1 TB | 3.5 GB | Dedicated |

### Checking Your Storage Usage

Via SSH console in Azure Portal:

```bash
df -h

```

### Understanding Your Available Space

For **Basic B1 (10 GB total)**:

- OS and runtime: ~2-3 GB
- App code and dependencies: ~1-2 GB
- **Usable space: ~6-7 GB** for images

**Example calculation for your use case:**

- Average image size: 300 KB
- 50 images: ~25 MB (only 0.4% of available space)
- Maximum capacity: ~20,000 images

### What Happens When Storage is Full?

```python
OSError: [Errno 28] No space left on device

```

**Consequences:**

1. New file writes fail
2. Existing files remain
3. App may become unstable
4. Logs may stop writing
5. Deployment may fail

**Recovery:** Restart app (clears ephemeral storage) or SSH in and delete files

### Solutions for Persistent Storage

### Option 1: Azure Blob Storage (Recommended for Production)

```python
from azure.storage.blob import BlobServiceClient

# After generating images
blob_service = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service.get_container_client("datasets")

for image_path in job_dir.rglob("*.jpg"):
    blob_name = f"{job_id}/{image_path.relative_to(job_dir)}"
    with open(image_path, "rb") as data:
        container_client.upload_blob(blob_name, data)

# Return permanent URLs
image_url = f"https://{account_name}.blob.core.windows.net/datasets/{blob_name}"

```

**Benefits:**

- ✅ Permanent storage
- ✅ Cheap (~$0.02/GB/month)
- ✅ Fast CDN delivery
- ✅ Survives restarts

### Option 2: Azure Files (Mounted Volume)

1. Create Azure Storage Account
2. Create File Share
3. Mount to `/home/data` in App Service
4. Save images there instead of `/tmp/`

**Trade-offs:**

- ✅ Persistent across restarts
- ✅ File system interface (no code changes)
- ❌ More expensive than Blob
- ❌ Slower than ephemeral storage

### Option 3: Immediate Download (Current Approach)

Generate → User downloads immediately → Delete

**Best for:**

- ✅ Test/demo environments
- ✅ No storage costs
- ✅ Simple implementation

**Limitations:**

- ❌ User must download before restart
- ❌ Can't retrieve old jobs

### Protection Strategies

### 1. Add Disk Space Check

```python
import shutil

def check_disk_space(min_free_gb: float = 1.0) -> bool:
    """Check if enough disk space is available."""
    stat = shutil.disk_usage("/")
    free_gb = stat.free / (1024**3)
    return free_gb >= min_free_gb

@app.post("/api/generate")
async def generate(request: Request, background_tasks: BackgroundTasks):
    if not check_disk_space(min_free_gb=1.0):
        raise HTTPException(
            status_code=507,  # Insufficient Storage
            detail="Not enough disk space available"
        )
    # ... proceed with generation

```

### 2. Auto-Cleanup Old Jobs

```python
def cleanup_old_jobs(max_age_hours: int = 24):
    """Delete jobs older than max_age_hours."""
    now = datetime.now()
    for job_dir in DOWNLOADS_DIR.iterdir():
        if job_dir.is_dir():
            age = now - datetime.fromtimestamp(job_dir.stat().st_mtime)
            if age.total_seconds() > max_age_hours * 3600:
                shutil.rmtree(job_dir)

```

### 3. Set Maximum Images Per Job

```python
class GenerateRequest(BaseModel):
    max_images: int = Field(default=10, le=100)  # Max 100 images

```

### Key Takeaway

**Even on the highest Azure App Service tier (Premium V3, Isolated), local disk is ALWAYS ephemeral.**

For production where data must persist, you **must use** Azure Blob Storage or similar external storage.

---

## 3. Celery Integration Options {#celery-integration}

### Understanding the Challenge

Celery on Azure App Service requires significant configuration because you need:

1. **Redis/RabbitMQ** (message broker)
2. **Celery worker processes** (separate from web app)
3. **Persistent broker connection**
4. **Background task execution**

### The Problem with App Service

Your current startup command:

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api_main:app

```

With Celery, you need:

```bash
# Terminal 1: Web server
gunicorn api_main:app

# Terminal 2: Celery worker
celery -A celery_core worker --loglevel=info

```

**But App Service only runs ONE startup command!**

### Solution: Run Both Processes

```bash
#!/bin/bash
# Start Celery worker in background
celery -A celery_core worker --loglevel=info &

# Start Gunicorn in foreground
gunicorn api_main:app

```

⚠️ This is fragile and not recommended for production.

### Better Solutions

### Option 1: Azure Container Apps (Recommended)

- Run web app and Celery workers as separate containers
- Built-in scaling
- Better for microservices

### Option 2: Azure Functions

- Use Azure Functions instead of Celery
- Serverless background tasks
- No worker management needed

### Option 3: WebJobs (App Service Feature)

- Run Celery worker as a WebJob
- Separate process from web app
- Still need Azure Redis

### Option 4: FastAPI BackgroundTasks (Current)

```python
@app.post("/api/generate")
async def generate(request: Request, background_tasks: BackgroundTasks):
    background_tasks.add_task(generate_dataset, config)
    return {"job_id": job_id}

```

**Pros:**

- ✅ No extra infrastructure
- ✅ No Redis needed
- ✅ Works on Basic tier
- ✅ Simple deployment

**Cons:**

- ❌ Tasks die if app restarts
- ❌ No task queue/retry logic
- ❌ Limited to app's resources

### Recommendation by Use Case

| Scenario | Solution | Why |
| --- | --- | --- |
| **Test/MVP** | BackgroundTasks | Simpler, lower costs |
| **Production (heavy)** | Container Apps + Celery | Proper scaling, separation |
| **Serverless** | Azure Functions | Fully managed |

---

## 4. Redis Deployment Strategies {#redis-strategies}

### The Philosophy Question: Why Celery + Redis?

You might wonder: *"Why use Celery and Redis if Azure has equivalent services (Functions + Azure Cache)?"*

### Why Use Celery + Redis Locally?

### 1. Vendor Independence

- Your code works on any platform (AWS, GCP, DigitalOcean, on-premise)
- Not locked into Azure ecosystem
- Easy to migrate providers

### 2. Local Development

- Run Redis locally (free, instant)
- Test full workflow on your laptop
- No cloud costs during development

### 3. Flexibility

- Use RabbitMQ instead of Redis if needed
- Deploy to Kubernetes
- Self-host everything

### 4. Cost Control

- Self-managed Redis on VM: ~$5/month
- Azure Cache for Redis: ~$15-50/month
- You choose based on budget

### Why Use Azure Functions + Azure Redis?

### 1. Managed Services

- No server management
- Auto-scaling
- Built-in monitoring
- High availability

### 2. Azure Integration

- Works seamlessly with other Azure services
- Single billing
- Unified monitoring (Application Insights)
- Better security (VNet integration)

### 3. Serverless Benefits (Functions)

- Pay per execution
- Auto-scale to zero
- No idle costs

### The Trade-off Matrix

| Approach | Pros | Cons |
| --- | --- | --- |
| **Celery + Self-hosted Redis** | Portable, cheap, flexible | You manage infrastructure |
| **Azure Functions + Azure Redis** | Fully managed, scalable | Vendor lock-in, more expensive |
| **Celery + Azure Redis** | Best of both worlds | Still need to manage Celery workers |

### Real-World Strategy

Most companies follow this pattern:

1. **Development:** Celery + local Redis (free, fast)
2. **Production:** Celery + Azure Redis (managed broker, self-managed workers)
3. **Or:** Migrate to Azure Functions only if Celery becomes a pain

### Redis Deployment Options

### Option 1: Azure Cache for Redis

**Pricing:**

| Tier | RAM | Price/Month | Use Case |
| --- | --- | --- | --- |
| Basic C0 | 250 MB | ~$16 | Dev/test (no SLA) |
| Basic C1 | 1 GB | ~$46 | Small workloads |
| Standard C0 | 250 MB | ~$31 | Production (has SLA) |
| Standard C1 | 1 GB | ~$93 | Recommended for production |
| Premium P1 | 6 GB | ~$300 | High performance |

**Setup via Azure CLI:**

```bash
az redis create \
  --resource-group TEST-Pixcrawler \
  --name pixcrawler-redis \
  --location francecentral \
  --sku Basic \
  --vm-size c1 \
  --enable-non-ssl-port

```

**Get connection string:**
Format: `pixcrawler-redis.redis.cache.windows.net:6379,password=YOUR_KEY,ssl=True`

### Option 2: Azure VM with Redis

**Cost:** ~$10-30/month (B1s or B2s VM)

**Setup:**

```bash
# Create VM
az vm create \
  --resource-group TEST-Pixcrawler \
  --name redis-vm \
  --image Ubuntu2204 \
  --size Standard_B1s \
  --admin-username azureuser

# SSH into VM and install Redis
sudo apt update
sudo apt install redis-server -y
sudo systemctl enable redis-server

```

**Trade-offs:**

- ✅ Cheap (~$10/month)
- ✅ Full control
- ❌ You manage updates, backups, security
- ❌ No high availability

### Option 3: Third-Party Managed Redis

**Redis Cloud:**

- Cost: Free tier (30MB) or $5-10/month
- Sign up at: https://redis.com/try-free/
- Get connection string and use in your app

**DigitalOcean/Linode:**

- Cost: ~$5-12/month
- Create droplet and install Redis
- Configure firewall (allow only your Azure App IP)

### Option 4: Redis on Same App Service Instance ⭐

**The simplest solution for your use case!**

Update your `startup.sh`:

```bash
#!/bin/bash

# Install Redis
apt-get update
apt-get install -y redis-server

# Start Redis as daemon
redis-server --daemonize yes

# Verify Redis is running
redis-cli ping

# Start Celery worker (if celery_core exists)
if [ -d "celery_core" ]; then
    celery -A celery_core worker --loglevel=info --concurrency=2 &
fi

# Start Gunicorn
gunicorn -w 2 -k uvicorn.workers.UvicornWorker api_main:app \
  --bind 0.0.0.0:8000 --timeout 300

```

**Process Architecture:**

```
Azure App Service Container
├── Redis (localhost:6379)
├── Celery Worker (background)
└── Gunicorn + FastAPI (foreground)

```

**Configure Celery:**

```python
import os
from celery import Celery

# Use local Redis
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

app = Celery('pixcrawler')
app.conf.broker_url = redis_url
app.conf.result_backend = redis_url

```

**Advantages:**

- ✅ $0 extra cost (uses existing B1 plan)
- ✅ Zero latency (localhost communication)
- ✅ Simple setup (one container)
- ✅ Works offline (for local dev)

**Limitations:**

- ❌ Data lost on restart (ephemeral)
- ❌ No high availability (single instance)
- ❌ Limited RAM (shares 1.75 GB)
- ❌ Can't scale horizontally

**Perfect for:**

- Testing/MVP
- Low traffic (<100 requests/min)
- Short-lived tasks
- Development

### Cost Comparison

| Option | Cost/Month | Reliability | Management |
| --- | --- | --- | --- |
| Azure Redis Basic C1 | $46 | ⭐⭐⭐⭐⭐ | Zero |
| Azure VM (B1s) | $10 | ⭐⭐⭐ | High |
| DigitalOcean Droplet | $6 | ⭐⭐⭐ | High |
| Redis Cloud Free | $0 | ⭐⭐⭐⭐ | Zero |
| Redis Cloud Paid | $5-10 | ⭐⭐⭐⭐ | Zero |
| **Same App Service** | **$0** | ⭐⭐ | Zero |

### Using Celery with Azure Redis

**Step 1:** Add Redis URL to App Settings

```
REDIS_URL=redis://:YOUR_PASSWORD@pixcrawler-redis.redis.cache.windows.net:6380?ssl_cert_reqs=required

```

**Step 2:** Update requirements

```
celery[redis]
redis

```

**Step 3:** Configure startup to run both processes

```bash
#!/bin/bash
# Start Celery worker in background
celery -A celery_core worker --loglevel=info --concurrency=2 &

# Start web server in foreground
gunicorn -w 2 -k uvicorn.workers.UvicornWorker api_main:app \
  --bind 0.0.0.0:8000 --timeout 300

```

**Step 4:** Use Celery in your API

```python
from celery_core.tasks import generate_dataset_task

@app.post("/api/generate")
async def generate(request: GenerateRequest):
    job_id = str(uuid.uuid4())

    # Queue task with Celery
    task = generate_dataset_task.delay(job_id, request.dict())

    return {
        "job_id": job_id,
        "task_id": task.id,
        "status": "queued"
    }

```

**Total Cost:**

- App Service B1: ~$13/month
- Azure Redis Basic C1: ~$46/month
- **Total: ~$59/month**

---

## 5. Docker on App Service {#docker-deployment}

### Understanding Docker Support

**Docker absolutely works on App Service!** In fact, it's one of the main deployment methods.

### Two Deployment Modes

### 1. Built-in Runtimes (Current Approach)

- App Service detects: Python 3.10
- Azure builds container automatically using Oryx
- Runs your `startup.sh`

### 2. Custom Docker Container (Recommended for Production)

- You build: Dockerfile → Docker image
- Push to: Azure Container Registry (ACR) or Docker Hub
- App Service pulls and runs your image

### Creating a Dockerfile

```docker
FROM python:3.10-slim

# Install system dependencies (including Redis)
RUN apt-get update && \
    apt-get install -y redis-server && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements-azure.txt .
RUN pip install --no-cache-dir -r requirements-azure.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run startup script
CMD ["bash", "startup.sh"]

```

### Building and Deploying

```bash
# Build image
docker build -t pixcrawler:latest .

# Tag for Azure Container Registry
docker tag pixcrawler:latest yourregistry.azurecr.io/pixcrawler:latest

# Push to ACR
docker push yourregistry.azurecr.io/pixcrawler:latest

```

### Configure App Service

In Azure Portal:

1. **Configuration** → **General settings**
2. **Stack:** Docker Container
3. **Image Source:** Azure Container Registry
4. **Registry:** yourregistry.azurecr.io
5. **Image:** pixcrawler:latest

### Benefits of Using Docker

| Aspect | Built-in Runtime | Docker Container |
| --- | --- | --- |
| **Setup** | Easier (just push code) | Requires Dockerfile |
| **Build time** | Slower (builds on Azure) | Faster (pre-built) |
| **Control** | Less | More |
| **Portability** | Azure-specific | Works anywhere |
| **Recommended for** | Quick tests, MVPs | Production |

**With Docker:**

- ✅ Consistent environment (dev = production)
- ✅ Faster deployments (pre-built image)
- ✅ Version control (tag images)
- ✅ Local testing (exact same container)
- ✅ Portable (works anywhere Docker runs)

**Without Docker:**

- ❌ Azure builds on every deploy (slower)
- ❌ Potential environment differences
- ❌ Less control over build process

### Important Limitation

**App Service still only runs ONE container**, whether you use:

- Built-in runtime (Azure builds container for you)
- Custom Docker image (you build container)

To run **multiple containers** (separate Redis, Celery, FastAPI), you need:

- **Azure Container Apps**
- **Azure Kubernetes Service (AKS)**
- **VM with Docker Compose**

### Multi-Container Architecture

### Azure Container Apps (Recommended)

```
Container App Environment
├── Container 1: FastAPI (your web app)
├── Container 2: Redis
└── Container 3: Celery Worker

```

**Setup:**

```bash
# Create Container App Environment
az containerapp env create \
  --name pixcrawler-env \
  --resource-group TEST-Pixcrawler \
  --location francecentral

# Deploy Redis container
az containerapp create \
  --name redis \
  --resource-group TEST-Pixcrawler \
  --environment pixcrawler-env \
  --image redis:alpine \
  --target-port 6379 \
  --ingress internal

# Deploy FastAPI container
az containerapp create \
  --name api \
  --resource-group TEST-Pixcrawler \
  --environment pixcrawler-env \
  --image your-registry/pixcrawler:latest \
  --target-port 8000 \
  --ingress external \
  --env-vars REDIS_URL=redis://redis:6379

# Deploy Celery worker container
az containerapp create \
  --name worker \
  --resource-group TEST-Pixcrawler \
  --environment pixcrawler-env \
  --image your-registry/pixcrawler:latest \
  --command celery -A celery_core worker \
  --env-vars REDIS_URL=redis://redis:6379

```

**Cost:** ~$30-50/month

### Docker Compose on Azure VM

`docker-compose.yml`:

```yaml
version: '3.8'
services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

  worker:
    build: .
    command: celery -A celery_core worker
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

```

**Cost:** ~$10-30/month (VM cost)

### Service Comparison

| Service | What It Is | Containers | Control | Cost |
| --- | --- | --- | --- | --- |
| **App Service** | Managed web hosting | 1 | Low | $13+ |
| **Container Apps** | Managed containers | Multiple | Medium | $30+ |
| **AKS** | Kubernetes cluster | Many | High | $70+ |
| **VM** | Virtual machine | Any | Full | $10+ |

### Simple Analogy

- **App Service** = Apartment (managed, simple, one unit)
- **Container Apps** = Condo complex (multiple units, some management)
- **AKS** = Building you own (full control, complex)
- **VM** = Empty lot (build everything yourself)

---

## Summary and Recommendations

### For Testing/MVP (Current Stage)

- ✅ Use **App Service B1** with Redis in same container ($13/month)
- ✅ Use **FastAPI BackgroundTasks** (no Celery needed)
- ✅ **Ephemeral storage** is fine (users download immediately)
- ✅ **Built-in runtime** deployment (simple git push)

### For Production

- ✅ Use **Azure Container Apps** with separate containers ($30-50/month)
- ✅ Use **Celery + Azure Redis** for task queue ($46/month for Redis)
- ✅ Use **Azure Blob Storage** for persistent file storage ($0.02/GB/month)
- ✅ Use **Docker** for consistent deployments

### Key Learnings

1. **All App Service tiers use ephemeral storage** - even Enterprise plans lose data on restart
2. **Redis can run on the same container** - cheapest and simplest for small apps
3. **Celery + Redis is portable** - not locked into Azure, works anywhere
4. **Docker works great on App Service** - but you're still limited to one container
5. **Multiple containers require Container Apps or AKS** - not possible with App Service alone

### Decision Framework

**Choose Based on:**

- **Budget:** App Service + same-container Redis ($13/month) vs. separate services ($60+/month)
- **Scale:** BackgroundTasks for MVP vs. Celery for production
- **Persistence:** Ephemeral for testing vs. Blob Storage for production
- **Portability:** Keep vendor-agnostic (Celery) vs. go full Azure (Functions)

---

*This guide represents a comprehensive learning journey through Azure deployment options, trade-offs, and best practices for FastAPI applications with background task processing.*