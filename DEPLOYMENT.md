# PixCrawler Deployment Guide

This guide provides step-by-step instructions for deploying PixCrawler to production environments. The application consists of three main components: Backend (FastAPI), Frontend (Next.js), and Workers (Celery).

## Table of Contents

- [Prerequisites](#prerequisites)
- [Development Deployment](#development-deployment)
- [Production Deployment](#production-deployment)
  - [Backend to Azure App Service](#backend-deployment-azure-app-service)
  - [Frontend to Vercel](#frontend-deployment-vercel)
  - [Frontend to Azure Static Web Apps](#frontend-deployment-azure-static-web-apps)
  - [Celery Workers](#celery-workers-deployment)
- [Database Setup](#database-setup)
- [Environment Variables](#environment-variables)
- [Health Checks and Monitoring](#health-checks-and-monitoring)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Accounts and Services

1. **Supabase Account**
   - Create project at [supabase.com](https://supabase.com)
   - Note your project URL and API keys
   - Set up database schema

2. **Azure Account** (for backend and optional frontend)
   - Active Azure subscription
   - Azure CLI installed locally
   - Resource group created

3. **Vercel Account** (alternative for frontend)
   - Account at [vercel.com](https://vercel.com)
   - Vercel CLI installed (optional)

4. **Redis Instance**
   - Development: Local Redis server
   - Production: Azure Cache for Redis or managed Redis service

### Required Tools

- **Python**: 3.11 or higher
- **Node.js**: 18.0 or higher
- **Bun**: Latest version (for frontend)
- **UV**: Python package manager
- **Azure CLI**: For Azure deployments
- **Git**: Version control

---

## Development Deployment

### Quick Start with Startup Scripts

The easiest way to run the full stack locally:

```bash
# Unix/Linux/Mac
./scripts/start-dev.sh

# Windows PowerShell
.\scripts\start-dev.ps1

# Windows Command Prompt
.\scripts\start-dev.cmd
```

These scripts will:
1. Check for required dependencies
2. Validate environment configuration
3. Start Redis (if not running)
4. Start backend server
5. Start frontend development server
6. Start Celery worker

### Manual Development Setup

If you prefer to start services individually:

#### 1. Set Up Environment Variables

```bash
# Root level
cp .env.example .env
# Edit .env with your Supabase credentials

# Backend
cp backend/.env.example backend/.env
# Edit backend/.env with configuration

# Frontend
cp frontend/.env.example frontend/.env
# Edit frontend/.env with configuration
```

See [CONFIGURATION.md](./CONFIGURATION.md) for detailed variable documentation.

#### 2. Install Dependencies

```bash
# Backend (Python with UV)
uv sync

# Frontend (Bun)
cd frontend
bun install
```

#### 3. Set Up Database

```bash
cd frontend

# Create RLS policies and auth triggers
bun run db:setup

# Run migrations
bun run db:migrate

# Optional: Seed with sample data
bun run db:seed
```

#### 4. Start Services

**Terminal 1: Redis**
```bash
redis-server
```

**Terminal 2: Backend**
```bash
cd backend
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 3: Frontend**
```bash
cd frontend
bun dev
```

**Terminal 4: Celery Worker**
```bash
celery -A celery_core.app worker --loglevel=info
```

**Terminal 5: Celery Beat (Optional - for scheduled tasks)**
```bash
celery -A celery_core.app beat --loglevel=info
```

#### 5. Verify Installation

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

---

## Production Deployment

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Production                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │   Frontend   │      │   Backend    │      │  Workers  │ │
│  │   (Vercel/   │─────▶│   (Azure     │◀────▶│ (Celery)  │ │
│  │    Azure)    │      │  App Service)│      │           │ │
│  └──────────────┘      └──────────────┘      └───────────┘ │
│         │                      │                     │       │
│         │                      │                     │       │
│         ▼                      ▼                     ▼       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Supabase PostgreSQL                      │  │
│  │         (Shared Database + Auth)                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │    Redis     │      │    Azure     │                    │
│  │   (Cache +   │      │   Storage    │                    │
│  │   Limiter)   │      │  (Datasets)  │                    │
│  └──────────────┘      └──────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Backend Deployment (Azure App Service)

### Step 1: Prepare Azure Resources

```bash
# Login to Azure
az login

# Create resource group (if not exists)
az group create --name pixcrawler-rg --location eastus

# Create App Service Plan (Linux)
az appservice plan create \
  --name pixcrawler-plan \
  --resource-group pixcrawler-rg \
  --is-linux \
  --sku B2

# Create Web App
az webapp create \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg \
  --plan pixcrawler-plan \
  --runtime "PYTHON:3.11"
```

### Step 2: Configure Environment Variables

Set all required environment variables in Azure Portal or via CLI:

```bash
az webapp config appsettings set \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg \
  --settings \
    ENVIRONMENT=production \
    DEBUG=false \
    HOST=0.0.0.0 \
    PORT=8000 \
    LOG_LEVEL=INFO \
    SUPABASE_URL="https://your-project.supabase.co" \
    SUPABASE_SERVICE_ROLE_KEY="your-service-role-key" \
    SUPABASE_ANON_KEY="your-anon-key" \
    DATABASE_URL="postgresql+asyncpg://postgres:password@db.your-project.supabase.co:5432/postgres" \
    DATABASE_POOL_SIZE=10 \
    DATABASE_MAX_OVERFLOW=20 \
    DATABASE_POOL_PRE_PING=true \
    DATABASE_ECHO=false \
    CACHE_ENABLED=true \
    CACHE_REDIS_HOST=localhost \
    CACHE_REDIS_PORT=6379 \
    CACHE_REDIS_DB=0 \
    LIMITER_ENABLED=true \
    LIMITER_REDIS_HOST=localhost \
    LIMITER_REDIS_PORT=6379 \
    LIMITER_REDIS_DB=1 \
    CELERY_BROKER_URL="redis://localhost:6379/0" \
    CELERY_RESULT_BACKEND="redis://localhost:6379/0" \
    STORAGE_PROVIDER=azure \
    STORAGE_AZURE_CONNECTION_STRING="your-azure-connection-string" \
    STORAGE_AZURE_CONTAINER_NAME=pixcrawler-datasets \
    ALLOWED_ORIGINS="https://pixcrawler.com,https://app.pixcrawler.com"
```

### Step 3: Configure Startup Script

The backend includes a startup script at `scripts/startup-azure.sh` that:
- Installs UV package manager
- Installs Python dependencies
- Starts Redis server (embedded)
- Starts Celery worker in background
- Starts FastAPI with Gunicorn

Configure it in Azure:

```bash
az webapp config set \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg \
  --startup-file "scripts/startup-azure.sh"
```

### Step 4: Deploy Code

**Option A: Deploy from Local Git**

```bash
# Configure deployment source
az webapp deployment source config-local-git \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg

# Get deployment URL
az webapp deployment list-publishing-credentials \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg \
  --query scmUri \
  --output tsv

# Add Azure remote and push
git remote add azure <deployment-url>
git push azure main
```

**Option B: Deploy from GitHub**

```bash
az webapp deployment source config \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg \
  --repo-url https://github.com/yourusername/pixcrawler \
  --branch main \
  --manual-integration
```

**Option C: Deploy ZIP**

```bash
# Create deployment package
cd backend
zip -r ../backend.zip . -x "*.pyc" -x "__pycache__/*" -x ".venv/*"

# Deploy
az webapp deployment source config-zip \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg \
  --src ../backend.zip
```

### Step 5: Verify Deployment

```bash
# Check deployment status
az webapp show \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg \
  --query state

# Test health endpoint
curl https://pixcrawler-backend.azurewebsites.net/health

# View logs
az webapp log tail \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg
```

### Step 6: Configure Custom Domain (Optional)

```bash
# Add custom domain
az webapp config hostname add \
  --webapp-name pixcrawler-backend \
  --resource-group pixcrawler-rg \
  --hostname api.pixcrawler.com

# Enable HTTPS
az webapp config ssl bind \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg \
  --certificate-thumbprint <thumbprint> \
  --ssl-type SNI
```

---

## Frontend Deployment (Vercel)

### Step 1: Install Vercel CLI (Optional)

```bash
npm install -g vercel
```

### Step 2: Configure Environment Variables

Create a `.env.production` file or set variables in Vercel Dashboard:

```bash
# Required
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_URL=https://pixcrawler-backend.azurewebsites.net
NEXT_PUBLIC_APP_URL=https://pixcrawler.com
NODE_ENV=production

# Optional: Stripe
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Optional: Resend
RESEND_API_KEY=re_...
CONTACT_EMAIL=contact@pixcrawler.com
FROM_EMAIL=noreply@pixcrawler.com
```

### Step 3: Deploy via Vercel Dashboard

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your Git repository
3. Configure project:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `bun run build`
   - **Output Directory**: `.next`
   - **Install Command**: `bun install`
4. Add environment variables from Step 2
5. Click "Deploy"

### Step 4: Deploy via CLI

```bash
cd frontend

# Login to Vercel
vercel login

# Deploy to production
vercel --prod

# Or link and deploy
vercel link
vercel --prod
```

### Step 5: Configure Custom Domain

1. Go to Project Settings → Domains
2. Add your custom domain (e.g., `pixcrawler.com`)
3. Configure DNS records as instructed
4. Wait for SSL certificate provisioning

### Step 6: Verify Deployment

- Visit your production URL
- Check browser console for errors
- Test authentication flow
- Verify API connectivity

---

## Frontend Deployment (Azure Static Web Apps)

### Step 1: Create Static Web App

```bash
az staticwebapp create \
  --name pixcrawler-frontend \
  --resource-group pixcrawler-rg \
  --source https://github.com/yourusername/pixcrawler \
  --location eastus2 \
  --branch main \
  --app-location "frontend" \
  --output-location ".next" \
  --login-with-github
```

### Step 2: Configure Build Settings

Create or update `.github/workflows/azure-static-web-apps.yml`:

```yaml
name: Azure Static Web Apps CI/CD

on:
  push:
    branches:
      - main
  pull_request:
    types: [opened, synchronize, reopened, closed]
    branches:
      - main

jobs:
  build_and_deploy_job:
    runs-on: ubuntu-latest
    name: Build and Deploy Job
    steps:
      - uses: actions/checkout@v3
        with:
          submodules: true

      - name: Setup Bun
        uses: oven-sh/setup-bun@v1
        with:
          bun-version: latest

      - name: Build And Deploy
        id: builddeploy
        uses: Azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN }}
          repo_token: ${{ secrets.GITHUB_TOKEN }}
          action: "upload"
          app_location: "frontend"
          output_location: ".next"
          app_build_command: "bun run build"
        env:
          NEXT_PUBLIC_SUPABASE_URL: ${{ secrets.NEXT_PUBLIC_SUPABASE_URL }}
          NEXT_PUBLIC_SUPABASE_ANON_KEY: ${{ secrets.NEXT_PUBLIC_SUPABASE_ANON_KEY }}
          NEXT_PUBLIC_API_URL: ${{ secrets.NEXT_PUBLIC_API_URL }}
          NEXT_PUBLIC_APP_URL: ${{ secrets.NEXT_PUBLIC_APP_URL }}
```

### Step 3: Configure Environment Variables

```bash
az staticwebapp appsettings set \
  --name pixcrawler-frontend \
  --resource-group pixcrawler-rg \
  --setting-names \
    NEXT_PUBLIC_SUPABASE_URL="https://your-project.supabase.co" \
    NEXT_PUBLIC_SUPABASE_ANON_KEY="your-anon-key" \
    NEXT_PUBLIC_API_URL="https://pixcrawler-backend.azurewebsites.net" \
    NEXT_PUBLIC_APP_URL="https://pixcrawler.com"
```

### Step 4: Configure Static Web App

The `frontend/staticwebapp.config.json` file is already configured with:
- API proxy routes
- SPA fallback routing
- Security headers
- CORS configuration

### Step 5: Verify Deployment

```bash
# Get default hostname
az staticwebapp show \
  --name pixcrawler-frontend \
  --resource-group pixcrawler-rg \
  --query defaultHostname

# Visit the URL and test
```

---

## Celery Workers Deployment

### Option 1: Azure Container Instances

```bash
# Create container instance
az container create \
  --name pixcrawler-worker \
  --resource-group pixcrawler-rg \
  --image python:3.11 \
  --command-line "celery -A celery_core.app worker --loglevel=info" \
  --environment-variables \
    CELERY_BROKER_URL="redis://your-redis:6379/0" \
    CELERY_RESULT_BACKEND="redis://your-redis:6379/0" \
    DATABASE_URL="postgresql+asyncpg://..." \
    SUPABASE_URL="https://your-project.supabase.co" \
    SUPABASE_SERVICE_ROLE_KEY="your-key" \
  --cpu 2 \
  --memory 4
```

### Option 2: Azure Virtual Machine

```bash
# Create VM
az vm create \
  --name pixcrawler-worker-vm \
  --resource-group pixcrawler-rg \
  --image UbuntuLTS \
  --size Standard_B2s \
  --admin-username azureuser \
  --generate-ssh-keys

# SSH into VM
ssh azureuser@<vm-ip>

# Install dependencies
sudo apt update
sudo apt install -y python3.11 python3-pip redis-server git

# Clone repository
git clone https://github.com/yourusername/pixcrawler.git
cd pixcrawler

# Install UV and dependencies
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync

# Create systemd service
sudo nano /etc/systemd/system/celery-worker.service
```

**Systemd service file**:
```ini
[Unit]
Description=Celery Worker for PixCrawler
After=network.target redis.service

[Service]
Type=forking
User=azureuser
Group=azureuser
WorkingDirectory=/home/azureuser/pixcrawler
Environment="PATH=/home/azureuser/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/azureuser/.local/bin/uv run celery -A celery_core.app worker --loglevel=info --detach
ExecStop=/home/azureuser/.local/bin/uv run celery -A celery_core.app control shutdown
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable celery-worker
sudo systemctl start celery-worker
sudo systemctl status celery-worker
```

### Option 3: Docker Container

```dockerfile
# Dockerfile.worker
FROM python:3.11-slim

WORKDIR /app

# Install UV
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY backend ./backend
COPY builder ./builder
COPY celery_core ./celery_core
COPY utility ./utility
COPY validator ./validator

# Install dependencies
RUN uv sync --no-dev

# Run worker
CMD ["uv", "run", "celery", "-A", "celery_core.app", "worker", "--loglevel=info"]
```

```bash
# Build and run
docker build -f Dockerfile.worker -t pixcrawler-worker .
docker run -d \
  --name pixcrawler-worker \
  -e CELERY_BROKER_URL="redis://redis:6379/0" \
  -e DATABASE_URL="postgresql+asyncpg://..." \
  pixcrawler-worker
```

---

## Database Setup

### Supabase Configuration

1. **Create Supabase Project**
   - Go to [supabase.com](https://supabase.com)
   - Create new project
   - Note project URL and API keys

2. **Run Database Migrations**
   ```bash
   cd frontend
   bun run db:setup    # Create RLS policies
   bun run db:migrate  # Apply schema migrations
   ```

3. **Configure Row Level Security (RLS)**
   
   RLS policies are automatically created by `db:setup` script. Verify in Supabase Dashboard:
   - Go to Authentication → Policies
   - Ensure policies exist for all tables
   - Test with different user roles

4. **Set Up Auth Triggers**
   
   The `db:setup` script creates a trigger to automatically create user profiles:
   ```sql
   CREATE OR REPLACE FUNCTION public.handle_new_user()
   RETURNS trigger AS $$
   BEGIN
     INSERT INTO public.profiles (id, email, full_name)
     VALUES (new.id, new.email, new.raw_user_meta_data->>'full_name');
     RETURN new;
   END;
   $$ LANGUAGE plpgsql SECURITY DEFINER;
   ```

5. **Configure Connection Pooling**
   
   In Supabase Dashboard → Settings → Database:
   - Enable connection pooling
   - Use transaction mode for backend
   - Set pool size to 10-20 connections

---

## Environment Variables

### Backend Environment Variables Checklist

- [ ] `ENVIRONMENT=production`
- [ ] `DEBUG=false`
- [ ] `HOST=0.0.0.0`
- [ ] `PORT=8000`
- [ ] `LOG_LEVEL=INFO`
- [ ] `SUPABASE_URL`
- [ ] `SUPABASE_SERVICE_ROLE_KEY`
- [ ] `SUPABASE_ANON_KEY`
- [ ] `DATABASE_URL`
- [ ] `DATABASE_POOL_SIZE=10`
- [ ] `DATABASE_MAX_OVERFLOW=20`
- [ ] `CACHE_ENABLED=true`
- [ ] `CACHE_REDIS_HOST`
- [ ] `LIMITER_ENABLED=true`
- [ ] `LIMITER_REDIS_HOST`
- [ ] `CELERY_BROKER_URL`
- [ ] `CELERY_RESULT_BACKEND`
- [ ] `STORAGE_PROVIDER=azure`
- [ ] `STORAGE_AZURE_CONNECTION_STRING`
- [ ] `ALLOWED_ORIGINS`

### Frontend Environment Variables Checklist

- [ ] `NEXT_PUBLIC_SUPABASE_URL`
- [ ] `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- [ ] `NEXT_PUBLIC_API_URL`
- [ ] `NEXT_PUBLIC_APP_URL`
- [ ] `NODE_ENV=production`
- [ ] `STRIPE_SECRET_KEY` (if using payments)
- [ ] `RESEND_API_KEY` (if using email)

---

## Health Checks and Monitoring

### Backend Health Check

```bash
# Basic health check
curl https://your-backend.azurewebsites.net/health

# Expected response
{
  "status": "healthy",
  "timestamp": "2025-11-30T12:00:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "celery": "healthy"
  }
}
```

### Configure Azure Monitor

```bash
# Enable Application Insights
az monitor app-insights component create \
  --app pixcrawler-backend-insights \
  --location eastus \
  --resource-group pixcrawler-rg \
  --application-type web

# Link to Web App
az webapp config appsettings set \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg \
  --settings APPLICATIONINSIGHTS_CONNECTION_STRING="<connection-string>"
```

### Set Up Alerts

```bash
# Create alert for high error rate
az monitor metrics alert create \
  --name high-error-rate \
  --resource-group pixcrawler-rg \
  --scopes /subscriptions/<sub-id>/resourceGroups/pixcrawler-rg/providers/Microsoft.Web/sites/pixcrawler-backend \
  --condition "avg requests/failed > 10" \
  --window-size 5m \
  --evaluation-frequency 1m
```

---

## Troubleshooting

### Backend Issues

#### Application Won't Start

**Symptoms**: App Service shows "Application Error"

**Solutions**:
1. Check startup logs:
   ```bash
   az webapp log tail --name pixcrawler-backend --resource-group pixcrawler-rg
   ```

2. Verify environment variables are set correctly

3. Check `startup-azure.sh` script permissions:
   ```bash
   chmod +x scripts/startup-azure.sh
   ```

4. Test locally with production settings:
   ```bash
   ENVIRONMENT=production uvicorn backend.main:app
   ```

#### Database Connection Errors

**Symptoms**: "Could not connect to database"

**Solutions**:
1. Verify DATABASE_URL format:
   ```
   postgresql+asyncpg://postgres:password@db.project.supabase.co:5432/postgres
   ```

2. Check Supabase connection limits in dashboard

3. Reduce pool size if hitting limits:
   ```bash
   DATABASE_POOL_SIZE=5
   DATABASE_MAX_OVERFLOW=10
   ```

4. Enable connection pre-ping:
   ```bash
   DATABASE_POOL_PRE_PING=true
   ```

#### Redis Connection Errors

**Symptoms**: "Redis connection refused"

**Solutions**:
1. Verify Redis is running in App Service:
   ```bash
   az webapp ssh --name pixcrawler-backend --resource-group pixcrawler-rg
   ps aux | grep redis
   ```

2. Check Redis configuration:
   ```bash
   CACHE_REDIS_HOST=localhost
   CACHE_REDIS_PORT=6379
   ```

3. For production, use Azure Cache for Redis:
   ```bash
   az redis create \
     --name pixcrawler-redis \
     --resource-group pixcrawler-rg \
     --location eastus \
     --sku Basic \
     --vm-size c0
   ```

### Frontend Issues

#### Build Failures

**Symptoms**: Vercel build fails

**Solutions**:
1. Check build logs in Vercel dashboard

2. Verify all environment variables are set

3. Test build locally:
   ```bash
   cd frontend
   bun run build
   ```

4. Check for TypeScript errors:
   ```bash
   bun run type-check
   ```

#### API Connection Errors

**Symptoms**: "Failed to fetch" or CORS errors

**Solutions**:
1. Verify `NEXT_PUBLIC_API_URL` points to correct backend

2. Check CORS configuration in backend:
   ```bash
   ALLOWED_ORIGINS=https://your-frontend.vercel.app
   ```

3. Test API endpoint directly:
   ```bash
   curl https://your-backend.azurewebsites.net/health
   ```

#### Authentication Issues

**Symptoms**: Users can't log in

**Solutions**:
1. Verify Supabase credentials:
   ```bash
   NEXT_PUBLIC_SUPABASE_URL=https://project.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
   ```

2. Check redirect URLs in Supabase Dashboard:
   - Go to Authentication → URL Configuration
   - Add production URL to allowed redirects

3. Verify RLS policies are set up:
   ```bash
   cd frontend
   bun run db:setup
   ```

### Worker Issues

#### Tasks Not Processing

**Symptoms**: Jobs stuck in pending state

**Solutions**:
1. Check if worker is running:
   ```bash
   celery -A celery_core.app inspect active
   ```

2. Verify broker connection:
   ```bash
   celery -A celery_core.app inspect ping
   ```

3. Check worker logs:
   ```bash
   celery -A celery_core.app events
   ```

4. Restart worker:
   ```bash
   sudo systemctl restart celery-worker
   ```

#### High Memory Usage

**Symptoms**: Worker crashes or OOM errors

**Solutions**:
1. Reduce worker concurrency:
   ```bash
   CELERY_WORKER_CONCURRENCY=2
   ```

2. Enable worker autoscaling:
   ```bash
   celery -A celery_core.app worker --autoscale=10,3
   ```

3. Set task time limits:
   ```bash
   CELERY_TASK_TIME_LIMIT=1800
   ```

4. Increase VM/container memory

---

## Post-Deployment Checklist

- [ ] Backend health check returns 200
- [ ] Frontend loads without errors
- [ ] User can sign up and log in
- [ ] User can create a project
- [ ] User can start a crawl job
- [ ] Celery worker processes tasks
- [ ] Images are downloaded and stored
- [ ] Job status updates in real-time
- [ ] Notifications are sent
- [ ] API documentation is accessible
- [ ] Logs are being collected
- [ ] Monitoring alerts are configured
- [ ] Backup strategy is in place
- [ ] SSL certificates are valid
- [ ] Custom domains are configured
- [ ] Environment variables are secured

---

## Rollback Procedure

### Backend Rollback

```bash
# List deployments
az webapp deployment list \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg

# Rollback to previous deployment
az webapp deployment slot swap \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg \
  --slot staging \
  --target-slot production
```

### Frontend Rollback (Vercel)

1. Go to Vercel Dashboard → Deployments
2. Find previous successful deployment
3. Click "..." → "Promote to Production"

### Frontend Rollback (Azure Static Web Apps)

```bash
# Redeploy previous commit
git revert HEAD
git push origin main
```

---

## Support and Resources

- **Configuration Guide**: [CONFIGURATION.md](./CONFIGURATION.md)
- **Architecture Documentation**: [backend/ARCHITECTURE.md](./backend/ARCHITECTURE.md)
- **API Documentation**: https://your-backend.azurewebsites.net/docs
- **Supabase Dashboard**: https://app.supabase.com
- **Azure Portal**: https://portal.azure.com
- **Vercel Dashboard**: https://vercel.com/dashboard

For additional help, contact the development team or open an issue on GitHub.
