# Message 1

# Azure Container Apps Migration Guide

A comprehensive conversation about migrating from Azure App Service (single container) to Azure Container Apps (microservices architecture) with separate containers for FastAPI, Redis, and Celery.

---

## Architecture Transition

### From: App Service (Single Container)

```
Azure App Service B1 (~$13/month)
└── Single Linux Container
    ├── Python 3.11
    ├── UV workspace manager
    ├── Redis (localhost process)
    ├── Celery worker (background process)
    └── Gunicorn + FastAPI (foreground)

```

### To: Container Apps (Microservices)

```
Azure Container Apps Environment
├── Container 1: FastAPI (pixcrawler-api)
│   ├── External HTTPS ingress
│   ├── Auto-scales: 1-10 instances
│   └── CPU: 0.5, Memory: 1Gi
│
├── Container 2: Redis (pixcrawler-redis)
│   ├── Internal-only access
│   ├── Fixed: 1 instance (stateful)
│   ├── DNS: pixcrawler-redis:6379
│   └── CPU: 0.25, Memory: 0.5Gi
│
└── Container 3: Celery Worker (pixcrawler-celery)
    ├── Internal-only access
    ├── Auto-scales: 1-5 instances (queue-based)
    ├── Connects to Redis via internal DNS
    └── CPU: 0.5, Memory: 1Gi

```

**Key Improvement:** All containers communicate via internal networking (no public IPs for Redis/Celery)

---

## Files Created for Container Apps

### 1. **azure-container-setup.sh** - Automated Deployment Script

**Purpose:** One-command deployment that handles everything

**What it does:**

- Creates Azure Container Registry (ACR)
- Builds and pushes your Docker image
- Creates Container Apps environment
- Deploys 3 containers (FastAPI, Redis, Celery)
- Configures networking between containers
- Sets up auto-scaling rules

**Key Features:**

- ✅ **Idempotent:** Safe to run multiple times
- ✅ **Handles existing resources:** Skips creation if already exists
- ✅ **Updates containers:** Deploys new images if containers exist
- ✅ **Validates prerequisites:** Checks Azure CLI and Docker

**Usage:**

```bash
# From project root: f:\Projects\Languages\Python\WorkingOnIt\PixCrawler\

# 1. Login to Azure
az login

# 2. Run deployment
bash azure-container-setup.sh

# Total time: ~10-15 minutes

```

### 2. **azure-container-apps.yaml** - Reference Documentation

**Important:** This file is **NOT auto-loaded** by Azure. It's documentation only.

**Purpose:** Shows you what containers need what configuration

**Contains:**

- Container specifications (CPU, memory, scaling)
- Environment variables for each container
- Health check configurations
- Auto-scaling rules
- Resource limits

**Azure Deployment Methods:**

| Method | Uses YAML? | What We Use |
| --- | --- | --- |
| Azure CLI | ❌ No | ✅ `azure-container-setup.sh` |
| Azure Portal | ❌ No | Manual clicks |
| ARM Templates | ❌ No (uses JSON) | Not used |
| Bicep | ❌ No (uses .bicep) | Not used |

**The YAML file is just for your reference** - think of it as documentation in an easy-to-read format.

### 3. **AZURE_CONTAINER_APPS_GUIDE.md** - Complete Deployment Guide

**Comprehensive documentation covering:**

- Step-by-step deployment instructions
- CI/CD setup (GitHub Actions + Azure DevOps)
- Monitoring and logging setup
- Troubleshooting common issues
- Cost estimation and optimization
- Migration checklist

### 4. **.github/workflows/deploy-container-apps.yml** - CI/CD Pipeline

**Automated deployment triggered by Git push**

**Workflow:**

```
Push to main branch
    ↓
Checkout code
    ↓
Login to Azure
    ↓
Build Docker image (tagged with commit SHA)
    ↓
Push to Azure Container Registry
    ↓
Set secrets (from GitHub Secrets)
    ↓
Deploy Backend API container
    ↓
Deploy Celery Worker container
    ↓
Run health check
    ↓
Show deployment summary
    ↓
✅ Done!

```

**Security Features:**

- ✅ Secrets stored in GitHub Secrets (encrypted)
- ✅ Never visible in logs (masked)
- ✅ Not in Git history
- ✅ Only accessible during workflow execution

### 5. **.github/SECRETS_SETUP.md** - Secrets Configuration Guide

**Step-by-step instructions for:**

- Adding secrets to GitHub repository
- Getting Azure credentials (service principal)
- Obtaining Supabase credentials
- Security best practices
- Troubleshooting common issues

**Required GitHub Secrets:**

1. `AZURE_CREDENTIALS` - Service principal for deployment
2. `SUPABASE_URL` - Supabase project URL
3. `SUPABASE_SERVICE_ROLE_KEY` - Supabase admin key
4. `SUPABASE_ANON_KEY` - Supabase public key
5. `DATABASE_URL` - PostgreSQL connection string
6. `AZURE_STORAGE_CONNECTION_STRING` - Blob storage access
7. `ALLOWED_ORIGINS` - CORS configuration

---

## Key Questions & Answers

### Q: Do I need to create a new `redis-core` package?

**A:** ❌ No! Redis runs as a separate container using the official `redis:7-alpine` image.

**Why not:**

- Redis is deployed as a standalone container (no custom code needed)
- Your backend already has the Redis client: `redis>=5.0.0` (in `backend/pyproject.toml`)
- Celery already uses Redis as broker: `celery>=5.3.0`
- Rate limiting already configured: `fastapi-limiter`

**How containers communicate:**

```
┌─────────────────────┐
│ Redis Container     │  ← Official redis:7-alpine image
│ (No custom code)    │     DNS: pixcrawler-redis:6379
└─────────────────────┘
         ↑
         │ Connects via redis:// URL
         │
┌─────────────────────┐
│ FastAPI Container   │  ← Uses redis>=5.0.0 client
│ backend.main:app    │
└─────────────────────┘
         ↑
┌─────────────────────┐
│ Celery Container    │  ← Uses celery>=5.3.0
│ celery worker       │
└─────────────────────┘

```

**Connection code (already in your project):**

```python
# backend/main.py
import redis.asyncio as redis

redis_connection = await redis.from_url(
    "redis://pixcrawler-redis:6379/0",  # Internal DNS name
    encoding="utf-8",
    decode_responses=True
)

```

### Q: Is `azure-container-apps.yaml` automatically loaded by Azure?

**A:** ❌ No. Azure does NOT use YAML files for Container Apps deployment.

**What the YAML file is:**

- 📄 Reference documentation showing container configuration
- 📄 Human-readable format for understanding architecture
- 📄 Can be version-controlled for documentation
- ❌ NOT used by Azure deployment

**What actually deploys:**

```bash
# The azure-container-setup.sh script runs Azure CLI commands like:
az containerapp create \
  --name pixcrawler-api \
  --resource-group pixcrawler-rg \
  --image myregistry.azurecr.io/app:latest \
  --env-vars KEY=value

```

**If you wanted Infrastructure as Code:**

- **Bicep** (Azure's IaC language):
    
    ```
    resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {  name: 'pixcrawler-api'  properties: { ... }}
    
    ```
    
- **ARM Templates** (JSON format):
    
    ```json
    {  "type": "Microsoft.App/containerApps",  "name": "pixcrawler-api",  "properties": { ... }}
    
    ```
    

### Q: Running the script from current location creates all 3 containers?

**A:** ✅ Yes, but prerequisites are required.

**Prerequisites:**

```bash
# 1. Azure CLI installed and authenticated
az --version
az login
az account set --subscription "Your-Subscription-Name"

# 2. Docker installed and running
docker --version
docker ps

# 3. Must run from project root
# Current location: f:\Projects\Languages\Python\WorkingOnIt\PixCrawler\
bash azure-container-setup.sh

```

**What if resources already exist?**

Original concern: Script would fail if resources existed

**Solution:** Script updated with idempotency checks

```bash
# Updated script behavior:

If resource group exists:
  ⚠️  Skip creation, show warning
  ✅ Continue with deployment

If Container Registry exists:
  ⚠️  Skip creation
  ✅ Use existing registry

If containers exist:
  ⚠️  Skip creation
  ✅ Update with new images
  ✅ Continue deployment

```

**If ACR name is globally taken:**

```bash
# Container Registry names must be globally unique
# If "pixcrawleracr" is taken, edit the script:

ACR_NAME="pixcrawleracr"  # Change this
# To:
ACR_NAME="yourname-pixcrawler"  # Must be unique across all Azure

```

### Q: Don't I need extra code or configuration?

**A:** ✅ Just run the script! But you must set secrets afterward.

**What the script automates:**

- ✅ Creates all Azure resources
- ✅ Builds Docker image from `backend/Dockerfile`
- ✅ Pushes to Azure Container Registry
- ✅ Deploys 3 containers
- ✅ Configures internal networking
- ✅ Sets up auto-scaling rules

**What you must do manually (one-time):**

**After deployment, set secrets:**

```bash
# 1. Set secrets for Backend API
az containerapp secret set \
  --name pixcrawler-api \
  --resource-group pixcrawler-rg \
  --secrets \
    supabase-url="https://your-project.supabase.co" \
    supabase-service-key="eyJhbGc..." \
    database-url="postgresql+asyncpg://..." \
    azure-storage-connection="DefaultEndpointsProtocol=https;..."

# 2. Update environment variables to use secrets
az containerapp update \
  --name pixcrawler-api \
  --resource-group pixcrawler-rg \
  --set-env-vars \
    SUPABASE_URL=secretref:supabase-url \
    SUPABASE_SERVICE_ROLE_KEY=secretref:supabase-service-key \
    DATABASE_URL=secretref:database-url \
    STORAGE_AZURE_CONNECTION_STRING=secretref:azure-storage-connection \
    ALLOWED_ORIGINS="https://your-frontend.vercel.app"

# 3. Same for Celery Worker
az containerapp secret set \
  --name pixcrawler-celery \
  --resource-group pixcrawler-rg \
  --secrets \
    database-url="postgresql+asyncpg://..." \
    azure-storage-connection="DefaultEndpointsProtocol=..."

```

**Complete workflow:**

```bash
# 1. Run deployment script
bash azure-container-setup.sh
# Wait 10-15 minutes

# 2. Set secrets (commands above)

# 3. Test your app
curl https://your-app-url.azurecontainerapps.io/api/v1/health/

# ✅ Done!

```

### Q: Why not add secrets to the setup script?

**Security reasons why secrets are separate:**

### 1. Security Best Practice

```bash
# ❌ BAD: Secrets in script (committed to Git)
SUPABASE_KEY="eyJhbGc..."  # Exposed in version control forever!

# ✅ GOOD: Secrets set separately
az containerapp secret set --secrets key="$SUPABASE_KEY"

```

**Problems with secrets in script:**

- ❌ Committed to Git (visible in history forever)
- ❌ Anyone with repo access sees them
- ❌ Hard to rotate/change
- ❌ Can't be different per environment

### 2. Different Environments Need Different Secrets

```bash
# Development
SUPABASE_URL=https://dev-project.supabase.co

# Production
SUPABASE_URL=https://prod-project.supabase.co

```

You'd need separate scripts for dev/staging/prod.

### 3. Team Collaboration

- Different team members have different credentials
- CI/CD systems use service principals
- You don't want to share personal keys

### Alternative: Use Environment Variables (If Needed)

**You can automate it securely:**

```bash
# Add to end of azure-container-setup.sh:

if [ -n "$SUPABASE_URL" ]; then
    echo "🔐 Setting secrets from environment variables..."
    az containerapp secret set \
      --name $APP_NAME \
      --secrets \
        supabase-url="$SUPABASE_URL" \
        database-url="$DATABASE_URL"
    echo "✅ Secrets configured"
else
    echo "⚠️  Set secrets manually with: az containerapp secret set ..."
fi

```

**Then run:**

```bash
# Export secrets (not committed to Git!)
export SUPABASE_URL="https://..."
export DATABASE_URL="postgresql+asyncpg://..."

# Run script
bash azure-container-setup.sh

```

### Q: Make a CI/CD file that handles secrets per container?

**A:** ✅ Created! See `.github/workflows/deploy-container-apps.yml`

**GitHub Actions workflow features:**

- ✅ Triggers on push to `main` or `production` branch
- ✅ Builds Docker image with commit SHA tag
- ✅ Pushes to Azure Container Registry
- ✅ Sets secrets from GitHub Secrets (secure!)
- ✅ Deploys Backend API container
- ✅ Deploys Celery Worker container
- ✅ Runs health check
- ✅ Shows deployment summary

**Secrets are secure:**

```yaml
# Workflow file (safe to commit)
env:
  SUPABASE_URL: ${{ secrets.SUPABASE_URL }}  # Reference only
  DATABASE_URL: ${{ secrets.DATABASE_URL }}   # Not actual value

```

**Security guarantees:**

- ✅ Encrypted at rest in GitHub
- ✅ Never visible in logs (masked)
- ✅ Not in Git history
- ✅ Only accessible during workflow execution

**The workflow file contains no actual secrets** - only references like `${{ secrets.NAME }}`, so it's safe to commit.

---

## Deployment Comparison

### App Service vs Container Apps

| Aspect | App Service | Container Apps |
| --- | --- | --- |
| **Architecture** | Single container | 3 separate containers |
| **Redis** | Process in startup script | Managed container |
| **Celery** | Background process | Dedicated container |
| **Scaling** | Vertical only | Independent per service |
| **Networking** | Localhost (`127.0.0.1`) | Internal DNS names |
| **Cost** | $13/month | $75-465/month |
| **Dockerfile** | Not used | Required |
| **Startup Script** | `startup-azure.sh` | Not needed |
| **Complexity** | Simple | More complex |
| **Production Ready** | Basic | Advanced |

### Cost Breakdown

**App Service B1:**

- **Cost:** $13/month
- **Specs:** Single container, limited resources
- **Scaling:** Manual vertical scaling only
- **Best for:** MVPs, small projects

**Container Apps:**

- **Cost:** $75-465/month (depends on usage)
- **Specs:** 3 containers with independent scaling
- **Scaling:** Auto-scaling based on load
- **Best for:** Production workloads, scalability needed

---

## Complete Deployment Workflow

### Option 1: Manual Deployment (One-Time)

```bash
# Step 1: Prerequisites
az login
docker --version

# Step 2: Run deployment script
bash azure-container-setup.sh
# Wait 10-15 minutes

# Step 3: Set secrets
az containerapp secret set --name pixcrawler-api ...
az containerapp secret set --name pixcrawler-celery ...

# Step 4: Test
curl https://your-app.azurecontainerapps.io/api/v1/health/

```

### Option 2: Automated CI/CD (Continuous)

```bash
# Step 1: Add secrets to GitHub
# Repository → Settings → Secrets and variables → Actions
# Add: AZURE_CREDENTIALS, SUPABASE_URL, DATABASE_URL, etc.

# Step 2: Push code
git add .
git commit -m "Deploy to Container Apps"
git push origin main

# Step 3: Watch GitHub Actions
# GitHub → Actions tab → See live deployment

# Automatic deployment on every push!

```

---

## What You Already Have

### ✅ No Changes Needed

**Your existing Docker setup works perfectly:**

- ✅ `backend/Dockerfile` - Multi-stage build with UV workspace support
- ✅ `backend/docker-compose.yml` - Local development environment
- ✅ Redis client packages already installed (`redis>=5.0.0`)
- ✅ Celery already configured (`celery>=5.3.0`)
- ✅ No new packages needed
- ✅ No code changes required

**Local development unchanged:**

```bash
# Still works exactly as before
docker-compose up

```

---

## Key Takeaways

### 1. **Architecture Separation**

- FastAPI, Redis, and Celery run in separate containers
- Communicate via internal DNS (not localhost)
- Independent scaling for each service

### 2. **No New Packages Needed**

- Redis runs as official `redis:7-alpine` image
- Your backend already has Redis client (`redis>=5.0.0`)
- No need for `redis-core` package

### 3. **YAML is Documentation Only**

- `azure-container-apps.yaml` is NOT used by Azure
- Actual deployment uses Azure CLI commands
- Think of YAML as architecture reference

### 4. **Idempotent Deployment**

- Script safe to run multiple times
- Handles existing resources gracefully
- Updates containers with new images

### 5. **Secrets Management**

- Never put secrets in scripts or Git
- Use Azure CLI commands after deployment
- Or use GitHub Actions with GitHub Secrets

### 6. **CI/CD Automation**

- GitHub Actions workflow handles everything
- Secrets stored securely in GitHub
- Automatic deployment on push to main

### 7. **No Code Changes**

- Your existing Dockerfile works perfectly
- Docker Compose still used for local dev
- Only deployment method changes

---

## Deployment Checklist

### Prerequisites

- [ ]  Azure CLI installed and logged in
- [ ]  Docker installed and running
- [ ]  Project at root directory

### Initial Deployment

- [ ]  Run `bash azure-container-setup.sh`
- [ ]  Wait 10-15 minutes for deployment
- [ ]  Set secrets via Azure CLI
- [ ]  Test health endpoint

### CI/CD Setup (Optional but Recommended)

- [ ]  Add 7 secrets to GitHub repository
- [ ]  Review `.github/workflows/deploy-container-apps.yml`
- [ ]  Push to main branch to trigger deployment
- [ ]  Monitor GitHub Actions tab

### Verification

- [ ]  Backend API accessible via HTTPS
- [ ]  Redis responding on internal network
- [ ]  Celery worker processing tasks
- [ ]  Health checks passing
- [ ]  Auto-scaling configured

---

## Summary

**The migration to Container Apps is streamlined:**

1. **Run one script:** `bash azure-container-setup.sh`
2. **Set secrets once:** Via Azure CLI commands
3. **Optional CI/CD:** Push to deploy automatically

**Everything else is automated:**

- ✅ Container registry creation
- ✅ Image building and pushing
- ✅ Network configuration
- ✅ Auto-scaling setup
- ✅ Health checks

**No extra packages or code changes needed** - your existing setup works perfectly with Container Apps! 🚀