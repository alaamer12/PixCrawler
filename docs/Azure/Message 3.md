# Message 3

# Azure Deployment Configuration Guide

A comprehensive conversation about deploying a Python FastAPI backend to Azure App Service.

---

## Project Overview

**Production Backend Stack:**

- **Framework:** FastAPI with async support
- **Package Manager:** UV (workspace/monorepo)
- **Database:** PostgreSQL (Supabase)
- **Caching:** Redis (rate limiting + Celery broker)
- **Task Queue:** Celery
- **Architecture:** Clean architecture with routers, services, repositories

**Entry Point:** `backend/main.py` → `backend.main:app`

---

## Azure Deployment Files Created

### 1. **startup-azure.sh** (Bash Startup Script)

Main startup script that:

- Installs UV package manager
- Syncs UV workspace dependencies
- Installs and starts Redis (localhost)
- Starts Celery worker (background)
- Starts Gunicorn with FastAPI (foreground)
- Includes comprehensive diagnostic output

**Startup command:**

```bash
uv run gunicorn backend.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000

```

### 2. **startup-azure.py** (Python Alternative)

Python version of the startup script with:

- Type hints throughout
- Proper error handling (try/except)
- Modular functions
- Better logging and diagnostics
- **Zero external dependencies** (uses only Python standard library)

**Key advantage:** More maintainable and easier to debug than bash

### 3. **.deployignore**

Excludes unnecessary files from Azure deployment:

- `frontend/` directory (deployed separately to Vercel/Netlify)
- Development files (tests, docs, cache)
- Build artifacts
- Local config files

**Benefit:** Faster deployments, smaller size, no unnecessary rebuilds

### 4. **.deployment**

Tells Azure:

- Deploy from root directory
- Exclude frontend automatically
- Use Python startup script by default

### 5. **.env.example.azure**

Template for required environment variables (must be set manually in Azure Portal)

---

## Key Decisions & Solutions

### UV Workspace vs requirements.txt

**Question:** Do we need `requirements-azure.txt`?

**Answer:** ❌ No! The project uses UV workspace with `pyproject.toml` files.

```bash
uv sync --no-dev

```

This single command installs all workspace packages and dependencies:

- `backend/` → FastAPI, SQLAlchemy, Supabase
- `builder/` → icrawler, Pillow
- `logging_config/` → Loguru
- `celery_core/` → Celery, Redis
- `validator/` → Image validation deps

### Startup Script: Bash vs Python

**Both options available:**

| Feature | Bash Script | Python Script |
| --- | --- | --- |
| Language | Shell | Python |
| Type Safety | ❌ No | ✅ Yes |
| Error Handling | Basic | Robust (try/except) |
| Readability | Good | Excellent |
| Maintainability | Medium | High |
| Debugging | Harder | Easier |
| Azure Support | ✅ Yes | ✅ Yes |

**Python script dependencies:** None! Uses only standard library modules (os, subprocess, sys, time, pathlib, typing)

**If external dependencies were needed:**

- **Option 1:** Install in script itself using pip
- **Option 2:** Add to main dependency file (installed before startup)
- **Option 3:** Use UV to install
- **Recommended:** Add to main dependencies (simplest approach)

### Frontend Exclusion from Backend Deployment

**Problem:** Frontend changes trigger unnecessary backend deployments

**Solution:** Use `.deployignore` file

**Before:**

```
Git push → Deploy EVERYTHING
├── backend/ ✅
├── frontend/ ❌ (unnecessary)
├── tests/ ❌

```

**After:**

```
Git push → Deploy ONLY backend
├── backend/ ✅
├── builder/ ✅
└── Frontend changes ignored ✅

```

### Environment Variables Configuration

**Important:** Azure does NOT automatically load `.env.azure` file

**The `.env.azure` file is just a reference template**

**How to set variables in Azure:**

**Option 1: Azure Portal (Manual)**

- App Service → Configuration → Application settings
- Add each variable manually
- Click Save

**Option 2: Azure CLI (Bulk)**

```bash
az webapp config appsettings set \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg \
  --settings \
    ENVIRONMENT=production \
    DEBUG=false \
    SUPABASE_URL=https://your-project.supabase.co \
    DATABASE_URL=postgresql+asyncpg://... \
    REDIS_URL=redis://localhost:6379/0

```

**Why not load .env.azure in startup script?**

- ❌ Secrets in Git (security risk)
- ❌ Not the Azure way
- ❌ Harder to manage per environment
- ✅ Use Azure Portal Application Settings instead

---

## Azure Lifecycle Hooks

### What Azure App Service Supports

| Hook Type | Supported? | How to Implement |
| --- | --- | --- |
| Startup | ✅ Yes | `startup-azure.py` |
| Health Check | ✅ Yes | Portal configuration |
| Shutdown | ❌ No | Use FastAPI lifespan |
| Restart | ❌ No | N/A |
| Error | ❌ No | Application-level handling |
| Pre-deploy | ❌ No | GitHub Actions workflow |
| Post-deploy | ❌ No | GitHub Actions workflow |

### Graceful Shutdown (Already Implemented)

Your `backend/main.py` already handles shutdown:

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup
    redis_connection = await redis.from_url(...)
    await FastAPILimiter.init(redis_connection)

    yield  # App runs here

    # Shutdown - runs when app stops
    await FastAPILimiter.close()
    await redis_connection.close()
    logger.info("Cleanup completed")

```

### Pre/Post Deployment Hooks

Use GitHub Actions workflow for:

- **Pre-deployment:** Run tests, validate configuration, send notifications
- **Post-deployment:** Health checks, readiness validation, success notifications

---

## Storage: Azure Blob Storage vs Data Lake Gen2

### Your Use Case

- ✅ Store images (objects/blobs)
- ✅ Retrieve images via URLs
- ✅ Tier storage by subscription (hot/cool/archive)
- ✅ Serve images to users
- ❌ NOT doing big data analytics
- ❌ NOT doing complex hierarchical queries

### Comparison

| Feature | Blob Storage | Data Lake Gen2 | Your Need |
| --- | --- | --- | --- |
| Store images | ✅ Perfect | ✅ Works | ✅ Need |
| Retrieve via URL | ✅ Simple | ✅ Complex | ✅ Need |
| Hot/Cool/Archive | ✅ Yes | ✅ Yes | ✅ Need |
| Flat structure | ✅ Yes | ❌ No | ✅ Need |
| Big data analytics | ❌ No | ✅ Yes | ❌ Don't need |
| Cost | 💰 Lower | 💰💰 Higher | 💰 Prefer |
| Complexity | 🟢 Simple | 🔴 Complex | 🟢 Prefer |

**Verdict:** ✅ **Azure Blob Storage is perfect** for your use case. Data Lake Gen2 is unnecessary complexity.

### Storage Tiers

Your code already supports tiered storage:

| Tier | Cost/GB/Month | Use Case | Your Implementation |
| --- | --- | --- | --- |
| Hot | $0.018 | Frequent access | Enterprise users |
| Cool | $0.010 | Infrequent access | Pro users |
| Archive | $0.001 | Rare access | Free users |

### Rehydration Explained

**Rehydration = Unarchiving**

Archive tier blobs are **offline:**

- ❌ Cannot be downloaded directly
- ❌ Cannot be accessed via URL
- ✅ Super cheap storage

**To access archived blob:**

1. Rehydrate it (move to Hot/Cool tier)
2. Wait for rehydration to complete
3. Then download/access

**Rehydration Time:**

- **Standard Priority:** Up to 15 hours (lower cost)
- **High Priority:** < 1 hour (higher cost)

**Example Flow:**

```python
blob_status = storage.get_blob_properties("dataset.zip")

if blob_status.tier == "Archive":
    # Rehydrate required - user must wait
    storage.rehydrate_blob(
        "dataset.zip",
        target_tier=AccessTier.HOT,
        priority=RehydratePriority.STANDARD  # 15 hours
    )
    return {"status": "rehydrating", "eta": "15 hours"}
else:
    # Ready immediately
    return storage.get_blob_url("dataset.zip")

```

**Monetization Strategy:**

- Free users → Archive tier (cheap, 15-hour wait)
- Pro/Enterprise users → Hot/Cool tier (instant access, higher cost)

### Azure Resources Needed

```bash
# 1. Create Storage Account
az storage account create \
  --name pixcrawlerstorage \
  --resource-group pixcrawler-rg \
  --location francecentral \
  --sku Standard_LRS \
  --kind StorageV2

# 2. Create Blob Container
az storage container create \
  --name pixcrawler-datasets \
  --account-name pixcrawlerstorage

```

**Required Environment Variables:**

```bash
STORAGE_PROVIDER=azure
STORAGE_AZURE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...
STORAGE_AZURE_CONTAINER_NAME=pixcrawler-datasets
STORAGE_AZURE_ENABLE_ARCHIVE_TIER=true
STORAGE_AZURE_DEFAULT_TIER=hot

```

---

## Celery Tasks for Storage

**Question:** Do I need Celery tasks like `task_transfer_archived_dataset_into_blobs`?

**Answer:** ❌ No, not for tier changes. Tier changes are instant via Azure SDK (milliseconds).

### When to Use Celery Tasks

✅ **Use Celery for:**

- **Bulk operations** - Moving 1000s of blobs at once
- **Scheduled jobs** - Auto-archive old datasets nightly
- **Long-running operations** - Rehydrating archived blobs (15 hours)
- **Retry logic** - Retry failed operations

**Examples:**

```python
@celery_app.task
def auto_archive_old_datasets():
    """Run nightly: Archive datasets older than 90 days."""
    old_blobs = storage.list_blobs(older_than_days=90)
    for blob in old_blobs:
        storage.set_blob_tier(blob, AccessTier.ARCHIVE)

@celery_app.task
def rehydrate_archived_blob(blob_name: str):
    """Rehydrate archived blob (takes 15 hours)."""
    storage.rehydrate_blob(blob_name, priority="standard")

@celery_app.task
def bulk_tier_change(blob_names: List[str], tier: str):
    """Change tier for multiple blobs."""
    for blob_name in blob_names:
        storage.set_blob_tier(blob_name, tier)

```

### For Your MVP

✅ **Don't add Celery tasks yet.** Your current setup handles:

- User requests dataset → Tier set immediately
- User changes subscription → Tier updated immediately
- Lifecycle policies → Azure handles automatically

Add Celery tasks later when you need scheduled archiving or bulk operations.

---

## Docker Files Usage

### Your Existing Files

✅ **`backend/Dockerfile`** - Multi-stage build, UV workspace support, health checks
✅ **`backend/docker-compose.yml`** - API + DB + Redis + Celery setup

### What Gets Used Where

**Local Development:**

```bash
docker-compose up

```

Uses:

- ✅ `backend/Dockerfile`
- ✅ `backend/docker-compose.yml`

**Azure App Service:**

```
Azure runs startup-azure.sh

```

Uses:

- ✅ `startup-azure.sh`
- ❌ `backend/Dockerfile` (not used)
- ❌ `backend/docker-compose.yml` (not used)

**Why?** Azure App Service doesn't support docker-compose. It runs your code directly with the startup script.

### Do You Need Traefik?

**Traefik = Reverse proxy/load balancer**

❌ **Not needed for:**

- Azure App Service (Azure handles routing)
- Local development (docker-compose handles it)
- Single backend deployment

✅ **Needed for:**

- Multiple services with custom routing
- Advanced load balancing
- Microservices architecture

**Verdict:** ❌ No Traefik needed for your setup

---

## Deployment Architecture

### Single Container Setup (Azure App Service B1)

```
Azure App Service B1 (~$13/month)
└── Linux Container
    ├── Python 3.11
    ├── UV (workspace manager)
    ├── Redis (localhost:6379)
    ├── Celery Worker (background)
    └── Gunicorn + FastAPI
        └── backend/main.py
            ├── API routes (/api/v1/*)
            ├── Services layer
            ├── Repositories
            └── Supabase integration

```

### Deployment Flow

```
1. Git push to GitHub
2. Azure detects changes (excludes frontend via .deployignore)
3. Runs startup-azure.sh:
   ├── Install UV
   ├── uv sync --no-dev (install all workspace dependencies)
   ├── Start Redis
   ├── Start Celery worker
   └── Start Gunicorn + FastAPI
4. Application ready

```

---

## Summary & Best Practices

### ✅ What You Have (Production Ready)

1. **Startup Script:** Both bash and Python versions available
2. **Dependency Management:** UV workspace (no requirements.txt needed)
3. **Frontend Exclusion:** `.deployignore` prevents unnecessary deployments
4. **Storage System:** Complete Azure Blob Storage with tiering
5. **Graceful Shutdown:** FastAPI lifespan context manager
6. **Local Development:** Docker Compose setup

### ⚙️ Configuration Checklist

- [ ]  Create Azure App Service (B1 tier)
- [ ]  Create Azure Storage Account (Blob, not Data Lake)
- [ ]  Set environment variables in Azure Portal (from `.env.example.azure`)
- [ ]  Set startup command: `python startup-azure.py` or `bash startup-azure.sh`
- [ ]  Connect GitHub for continuous deployment
- [ ]  Deploy frontend separately to Vercel/Netlify

### 📋 Key Takeaways

1. **UV Workspace:** No requirements.txt needed - `uv sync` handles everything
2. **Environment Variables:** Must be set manually in Azure Portal (not from .env files)
3. **Storage:** Azure Blob Storage (not Data Lake Gen2) is perfect for your use case
4. **Rehydration:** Archive tier requires 15-hour rehydration before access
5. **Celery:** Not needed for instant tier changes; add later for bulk/scheduled operations
6. **Docker Files:** Used for local dev only; Azure uses startup script
7. **Lifecycle Hooks:** Limited in Azure App Service; handle in application code

### 🚀 Deployment Workflow

```bash
# Local development
docker-compose up

# Production deployment
git push origin main
# Azure automatically runs startup-azure.sh

```

**Everything is configured and ready for deployment!** 🎉