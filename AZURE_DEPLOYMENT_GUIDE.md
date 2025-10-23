# Azure Deployment Guide - PixCrawler Backend

## 📋 Prerequisites

- Azure account with active subscription
- Supabase project (for PostgreSQL database)
- GitHub repository connected to Azure

## 🚀 Deployment Steps

### Step 1: Create Azure App Service

**Via Azure Portal:**

1. Go to https://portal.azure.com
2. Click "Create a resource" → "Web App"
3. Configure:
   - **Resource Group:** Create new or use existing
   - **Name:** `pixcrawler-backend` (must be globally unique)
   - **Publish:** Code
   - **Runtime stack:** Python 3.11
   - **Operating System:** Linux
   - **Region:** Choose closest to your users
   - **Pricing Plan:** Basic B1 ($13/month) or higher
4. Click "Review + Create" → "Create"

**Via Azure CLI:**

```bash
# Create resource group
az group create --name pixcrawler-rg --location francecentral

# Create App Service plan
az appservice plan create \
  --name pixcrawler-plan \
  --resource-group pixcrawler-rg \
  --sku B1 \
  --is-linux

# Create Web App
az webapp create \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg \
  --plan pixcrawler-plan \
  --runtime "PYTHON:3.11"
```

### Step 2: Configure Deployment

**Connect to GitHub:**

1. Go to your App Service → **Deployment** → **Deployment Center**
2. **Source:** GitHub
3. Authorize GitHub access
4. Select:
   - **Organization:** Your GitHub username
   - **Repository:** PixCrawler
   - **Branch:** main (or your production branch)
5. Click **Save**

Azure will automatically create `.github/workflows/main_pixcrawler-backend.yml`

### Step 3: Configure Startup Command

1. Go to **Configuration** → **General settings**
2. **Startup Command:** `/home/site/wwwroot/startup-azure.sh`
3. Click **Save**

### Step 4: Set Environment Variables

Go to **Configuration** → **Application settings** and add:

**Required Settings:**

```bash
# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Supabase (Get from Supabase Dashboard)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
SUPABASE_ANON_KEY=eyJhbGc...

# Database (Supabase PostgreSQL)
DATABASE_URL=postgresql+asyncpg://postgres:password@db.your-project.supabase.co:5432/postgres

# CORS (Your frontend URL)
ALLOWED_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000

# Redis (Local)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Storage
STORAGE_PROVIDER=local
STORAGE_LOCAL_STORAGE_PATH=/tmp/pixcrawler-storage
```

Click **Save** after adding all variables.

### Step 5: Deploy

**Option A: Push to GitHub (Automatic)**

```bash
git add .
git commit -m "Configure Azure deployment"
git push origin main
```

GitHub Actions will automatically deploy to Azure.

**Option B: Manual Deploy via Azure CLI**

```bash
az webapp up \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg \
  --runtime "PYTHON:3.11"
```

### Step 6: Monitor Deployment

1. **GitHub Actions:** Check https://github.com/your-username/PixCrawler/actions
2. **Azure Logs:** App Service → **Monitoring** → **Log stream**
3. **Deployment Center:** Check deployment status

Wait 5-10 minutes for:
- Dependencies to install (UV workspace)
- Redis to start
- Celery worker to start
- Gunicorn to start

### Step 7: Test Deployment

**Health Check:**

```bash
curl https://pixcrawler-backend.azurewebsites.net/api/v1/health/
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-23T...",
  "version": "1.0.0"
}
```

**API Documentation:**

Visit: `https://pixcrawler-backend.azurewebsites.net/docs`

## 🔧 Architecture

```
Azure App Service (Single Container)
├── Python 3.11
├── UV (package manager)
├── Redis (localhost:6379)
├── Celery Worker (background)
└── Gunicorn + FastAPI (foreground)
    └── Backend API (backend.main:app)
```

## 📊 What Gets Deployed

- **Entry Point:** `backend/main.py`
- **Startup Script:** `startup-azure.sh`
- **Dependencies:** Installed via UV workspace
- **Packages:**
  - `backend/` (FastAPI API)
  - `builder/` (Image crawler)
  - `logging_config/` (Loguru)
  - `celery_core/` (Task queue)
  - `validator/` (Image validation)

## 🔍 Troubleshooting

### Issue: App not starting

**Check logs:**
```bash
az webapp log tail --name pixcrawler-backend --resource-group pixcrawler-rg
```

**Common causes:**
- Missing environment variables
- Invalid Supabase credentials
- Redis failed to start
- UV sync failed

### Issue: 404 on first request

**Solution:** Cold start - wait 2-3 minutes and retry.

**Prevention:** Use UptimeRobot to ping `/api/v1/health/` every 5 minutes.

### Issue: Redis connection failed

**Check:** Redis should start automatically in `startup-azure.sh`

**Verify:**
```bash
# SSH into container
az webapp ssh --name pixcrawler-backend --resource-group pixcrawler-rg

# Check Redis
redis-cli ping
```

### Issue: Celery worker not running

**Check logs:** Look for "Celery worker started" in log stream

**Verify:**
```bash
# SSH into container
ps aux | grep celery
```

## 💾 Storage Notes

**Ephemeral Storage:**
- Local files in `/tmp/` are lost on restart
- Use Azure Blob Storage for persistent data

**To enable Azure Blob Storage:**

1. Create Azure Storage Account
2. Create container: `pixcrawler-storage`
3. Update environment variables:
   ```bash
   STORAGE_PROVIDER=azure
   STORAGE_AZURE_CONNECTION_STRING=...
   STORAGE_AZURE_CONTAINER_NAME=pixcrawler-storage
   ```

## 🔐 Security Checklist

- ✅ Set `DEBUG=false` in production
- ✅ Use strong Supabase service role key
- ✅ Configure CORS with specific origins (not `*`)
- ✅ Enable HTTPS (automatic on Azure)
- ✅ Set `ENVIRONMENT=production`
- ✅ Review allowed hosts

## 📈 Scaling

**Vertical Scaling (More resources):**
- Upgrade to Standard S1 or Premium P1V3
- Enable "Always On" to prevent cold starts

**Horizontal Scaling (More instances):**
- Not recommended with local Redis
- Migrate to Azure Container Apps first

## 🎯 Next Steps

1. ✅ Deploy backend to Azure
2. ⏭️ Deploy frontend to Vercel/Azure Static Web Apps
3. ⏭️ Configure custom domain
4. ⏭️ Set up monitoring (Application Insights)
5. ⏭️ Migrate to Azure Container Apps (for scaling)

## 📞 Support

- **Azure Docs:** https://docs.microsoft.com/azure/app-service/
- **PixCrawler Issues:** https://github.com/your-username/PixCrawler/issues
