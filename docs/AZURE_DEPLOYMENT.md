# Azure Deployment Guide for PixCrawler

This guide provides comprehensive instructions for deploying PixCrawler to Microsoft Azure, including all required services and configurations.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Azure Services Architecture](#azure-services-architecture)
- [Step-by-Step Deployment](#step-by-step-deployment)
- [Configuration](#configuration)
- [Monitoring and Observability](#monitoring-and-observability)
- [Cost Optimization](#cost-optimization)
- [Troubleshooting](#troubleshooting)

---

## Overview

PixCrawler uses the following Azure services:

- **Azure App Service**: Hosts the FastAPI backend with Gunicorn + Uvicorn
- **Azure Blob Storage**: Stores generated datasets with hot/cool/archive tiers
- **Azure Application Insights**: Monitors application performance and errors
- **Azure Static Web Apps** (Optional): Alternative to Vercel for Next.js frontend

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Azure Cloud                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │   Azure App Service (Linux Container)                │   │
│  │   ┌────────────────────────────────────────────────┐ │   │
│  │   │  FastAPI Backend                               │ │   │
│  │   │  - Gunicorn (4 workers)                        │ │   │
│  │   │  - Redis (localhost:6379)                      │ │   │
│  │   │  - Celery Worker (background)                  │ │   │
│  │   └────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────┘   │
│                            ↕                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │   Azure Blob Storage                                 │   │
│  │   - Hot Tier: Immediate access (ZIP archives)       │   │
│  │   - Cool Tier: 30-day minimum (cost optimized)      │   │
│  │   - Archive Tier: 180-day minimum (long-term)       │   │
│  └──────────────────────────────────────────────────────┘   │
│                            ↕                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │   Azure Application Insights                         │   │
│  │   - Request/response tracking                        │   │
│  │   - Dependency monitoring (DB, Redis, HTTP)          │   │
│  │   - Exception logging                                │   │
│  │   - Custom metrics and events                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                   External Services                          │
├─────────────────────────────────────────────────────────────┤
│  - Supabase (PostgreSQL + Auth)                             │
│  - Vercel (Next.js Frontend) or Azure Static Web Apps       │
└─────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Required Accounts

1. **Azure Account**: [Sign up](https://azure.microsoft.com/free/)
2. **Supabase Account**: [Sign up](https://supabase.com/)
3. **GitHub Account**: For CI/CD deployment

### Required Tools

```bash
# Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login to Azure
az login

# Set default subscription
az account set --subscription "YOUR_SUBSCRIPTION_ID"
```

### Local Development Setup

```bash
# Install Python dependencies
uv sync

# Install Azure SDK (optional dependencies)
uv pip install azure-storage-blob opencensus-ext-azure

# Copy environment template
cp .env.example.azure .env

# Update .env with your Azure credentials
```

---

## Azure Services Architecture

### 1. Azure App Service

**Purpose**: Hosts the FastAPI backend application

**Features**:
- Linux container with Python 3.11+
- Built-in Redis for Celery task queue
- Automatic scaling and load balancing
- Continuous deployment from GitHub
- Application logging to Azure Monitor

**Recommended SKU**:
- **Development**: B1 (Basic) - $13/month
- **Production**: P1V2 (Premium) - $73/month
- **High Traffic**: P2V2 (Premium) - $146/month

### 2. Azure Blob Storage

**Purpose**: Stores generated image datasets

**Features**:
- Hot tier for immediate access (ZIP archives)
- Cool tier for cost optimization (30-day minimum)
- Archive tier for long-term storage (180-day minimum)
- Lifecycle management policies
- SAS token generation for secure downloads

**Cost Structure**:
- Hot: $0.018/GB/month
- Cool: $0.010/GB/month (44% savings)
- Archive: $0.001/GB/month (94% savings)

### 3. Azure Application Insights

**Purpose**: Application performance monitoring

**Features**:
- Request/response tracking
- Dependency monitoring (DB, Redis, HTTP)
- Exception and error logging
- Custom metrics and events
- Live metrics stream
- Application map and performance profiler

**Cost**: First 5GB/month free, then $2.30/GB

### 4. Azure Static Web Apps (Optional)

**Purpose**: Alternative to Vercel for Next.js frontend

**Features**:
- Global CDN distribution
- Automatic HTTPS
- Custom domains
- GitHub Actions integration
- Free tier available

**Cost**:
- Free: 100GB bandwidth/month
- Standard: $9/month + $0.20/GB

---

## Step-by-Step Deployment

### Step 1: Create Resource Group

```bash
# Create resource group
az group create \
  --name pixcrawler-rg \
  --location eastus

# Verify creation
az group show --name pixcrawler-rg
```

### Step 2: Create Storage Account

```bash
# Create storage account
az storage account create \
  --name pixcrawlerstorage \
  --resource-group pixcrawler-rg \
  --location eastus \
  --sku Standard_LRS \
  --kind StorageV2 \
  --access-tier Hot

# Get connection string
az storage account show-connection-string \
  --name pixcrawlerstorage \
  --resource-group pixcrawler-rg \
  --output tsv

# Create blob container
az storage container create \
  --name pixcrawler-datasets \
  --account-name pixcrawlerstorage \
  --public-access off
```

**Save the connection string** - you'll need it for environment variables.

### Step 3: Create Application Insights

```bash
# Create Application Insights
az monitor app-insights component create \
  --app pixcrawler-insights \
  --location eastus \
  --resource-group pixcrawler-rg \
  --application-type web

# Get connection string
az monitor app-insights component show \
  --app pixcrawler-insights \
  --resource-group pixcrawler-rg \
  --query connectionString \
  --output tsv
```

**Save the connection string** - you'll need it for monitoring.

### Step 4: Create App Service Plan

```bash
# Create App Service Plan (Linux)
az appservice plan create \
  --name pixcrawler-plan \
  --resource-group pixcrawler-rg \
  --location eastus \
  --is-linux \
  --sku B1

# For production, use Premium tier
# az appservice plan create \
#   --name pixcrawler-plan \
#   --resource-group pixcrawler-rg \
#   --location eastus \
#   --is-linux \
#   --sku P1V2
```

### Step 5: Create Web App

```bash
# Create Web App
az webapp create \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg \
  --plan pixcrawler-plan \
  --runtime "PYTHON:3.11"

# Enable application logging
az webapp log config \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg \
  --application-logging filesystem \
  --level information

# Enable detailed error messages
az webapp config set \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg \
  --detailed-error-logging-enabled true
```

### Step 6: Configure Environment Variables

```bash
# Set application settings (environment variables)
az webapp config appsettings set \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg \
  --settings \
    ENVIRONMENT=production \
    DEBUG=false \
    LOG_LEVEL=INFO \
    SUPABASE_URL="https://your-project.supabase.co" \
    SUPABASE_SERVICE_ROLE_KEY="your-service-role-key" \
    SUPABASE_ANON_KEY="your-anon-key" \
    DATABASE_URL="postgresql+asyncpg://..." \
    REDIS_URL="redis://localhost:6379/0" \
    CELERY_BROKER_URL="redis://localhost:6379/1" \
    CELERY_RESULT_BACKEND="redis://localhost:6379/2" \
    STORAGE_PROVIDER=azure \
    AZURE_BLOB_CONNECTION_STRING="DefaultEndpointsProtocol=https;..." \
    AZURE_BLOB_CONTAINER_NAME=pixcrawler-datasets \
    AZURE_BLOB_DEFAULT_TIER=hot \
    AZURE_BLOB_ENABLE_ARCHIVE=true \
    AZURE_MONITOR_ENABLED=true \
    AZURE_MONITOR_CONNECTION_STRING="InstrumentationKey=..." \
    ALLOWED_ORIGINS="https://your-frontend.vercel.app"
```

**Alternative**: Set environment variables via Azure Portal:
1. Go to Azure Portal → App Services → pixcrawler-backend
2. Settings → Configuration → Application settings
3. Click "New application setting" for each variable
4. Click "Save" when done

### Step 7: Configure Startup Command

```bash
# Set startup command
az webapp config set \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg \
  --startup-file "bash startup-azure.sh"
```

The `startup-azure.sh` script:
1. Installs UV package manager
2. Installs Python dependencies
3. Starts Redis server
4. Starts Celery worker in background
5. Starts Gunicorn with Uvicorn workers

### Step 8: Deploy Application

#### Option A: Deploy from Local Machine

```bash
# Build and deploy
cd /path/to/pixcrawler
az webapp up \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg \
  --runtime "PYTHON:3.11"
```

#### Option B: Deploy from GitHub (Recommended)

```bash
# Configure GitHub deployment
az webapp deployment source config \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg \
  --repo-url https://github.com/YOUR_USERNAME/pixcrawler \
  --branch main \
  --manual-integration

# Or use GitHub Actions (see .github/workflows/azure-deploy.yml)
```

### Step 9: Verify Deployment

```bash
# Check deployment status
az webapp show \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg \
  --query state

# View logs
az webapp log tail \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg

# Test API
curl https://pixcrawler-backend.azurewebsites.net/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-08T12:00:00Z",
  "services": {
    "database": {"status": "healthy"},
    "redis": {"status": "healthy"},
    "celery": {"status": "healthy"}
  }
}
```

---

## Configuration

### Environment Variables Reference

See `.env.example.azure` for complete list. Key variables:

#### Application Settings
```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

#### Supabase (Required)
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
```

#### Database (Required)
```bash
DATABASE_URL=postgresql+asyncpg://postgres:password@db.your-project.supabase.co:5432/postgres
```

#### Azure Blob Storage (Required)
```bash
STORAGE_PROVIDER=azure
AZURE_BLOB_CONNECTION_STRING=DefaultEndpointsProtocol=https;...
AZURE_BLOB_CONTAINER_NAME=pixcrawler-datasets
AZURE_BLOB_DEFAULT_TIER=hot
AZURE_BLOB_ENABLE_ARCHIVE=true
```

#### Azure Application Insights (Recommended)
```bash
AZURE_MONITOR_ENABLED=true
AZURE_MONITOR_CONNECTION_STRING=InstrumentationKey=...
AZURE_MONITOR_SAMPLING_RATE=1.0
```

### Lifecycle Management Policies

Configure automatic tier transitions for cost optimization:

```bash
# Enable lifecycle management
AZURE_BLOB_LIFECYCLE_ENABLED=true
AZURE_BLOB_LIFECYCLE_COOL_AFTER_DAYS=30
AZURE_BLOB_LIFECYCLE_ARCHIVE_AFTER_DAYS=90
AZURE_BLOB_LIFECYCLE_DELETE_AFTER_DAYS=2555
```

**Policy Behavior**:
1. Upload to Hot tier (immediate access)
2. Move to Cool tier after 30 days (44% cost savings)
3. Move to Archive tier after 90 days (94% cost savings)
4. Delete after 7 years (2555 days) for compliance

---

## Monitoring and Observability

### Azure Application Insights

#### View Logs

```bash
# Stream live logs
az webapp log tail \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg

# Download logs
az webapp log download \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg \
  --log-file logs.zip
```

#### Query Logs (Azure Portal)

1. Go to Application Insights → Logs
2. Use Kusto Query Language (KQL):

```kql
// View all requests in last hour
requests
| where timestamp > ago(1h)
| project timestamp, name, url, resultCode, duration
| order by timestamp desc

// View failed requests
requests
| where success == false
| project timestamp, name, url, resultCode, duration
| order by timestamp desc

// View exceptions
exceptions
| where timestamp > ago(1h)
| project timestamp, type, outerMessage, innermostMessage
| order by timestamp desc

// View custom events
customEvents
| where name == "job_completed"
| project timestamp, name, customDimensions
| order by timestamp desc
```

#### Custom Metrics

The application tracks custom metrics:

```python
from backend.core.monitoring import setup_azure_monitor

monitor = setup_azure_monitor(
    connection_string=settings.azure.monitor.get_connection_string(),
    sampling_rate=settings.azure.monitor.sampling_rate
)

# Track custom events
monitor.track_event("job_started", {"job_id": "123", "keywords": "laptop"})

# Track custom metrics
monitor.track_metric("images_processed", 1000, {"job_id": "123"})

# Track exceptions
try:
    # ... code ...
except Exception as e:
    monitor.track_exception(e, {"job_id": "123"})
```

### Performance Monitoring

#### Application Map

View dependencies and performance:
1. Azure Portal → Application Insights → Application Map
2. See visual representation of:
   - API endpoints
   - Database calls
   - Redis operations
   - External HTTP calls

#### Live Metrics

Real-time monitoring:
1. Azure Portal → Application Insights → Live Metrics
2. View:
   - Incoming requests per second
   - Failed requests
   - Server response time
   - Server CPU/Memory usage

---

## Cost Optimization

### Estimated Monthly Costs

#### Development Environment
- App Service (B1): $13/month
- Blob Storage (10GB Hot): $0.18/month
- Application Insights (1GB): Free
- **Total**: ~$13/month

#### Production Environment (Low Traffic)
- App Service (P1V2): $73/month
- Blob Storage (100GB Hot → Cool): $1.80/month → $1.00/month
- Application Insights (5GB): Free
- **Total**: ~$75/month

#### Production Environment (High Traffic)
- App Service (P2V2): $146/month
- Blob Storage (1TB with lifecycle): $18/month → $10/month → $1/month
- Application Insights (20GB): $34.50/month
- **Total**: ~$192/month

### Cost Optimization Strategies

#### 1. Blob Storage Lifecycle Management

Enable automatic tier transitions:

```bash
AZURE_BLOB_LIFECYCLE_ENABLED=true
AZURE_BLOB_LIFECYCLE_COOL_AFTER_DAYS=30
AZURE_BLOB_LIFECYCLE_ARCHIVE_AFTER_DAYS=90
```

**Savings**: Up to 94% on storage costs for archived data

#### 2. Application Insights Sampling

Reduce telemetry volume:

```bash
AZURE_MONITOR_SAMPLING_RATE=0.1  # 10% sampling
```

**Savings**: 90% reduction in Application Insights costs

#### 3. App Service Scaling

Use auto-scaling rules:

```bash
# Scale up during business hours
az monitor autoscale create \
  --resource-group pixcrawler-rg \
  --resource pixcrawler-plan \
  --resource-type Microsoft.Web/serverfarms \
  --name autoscale-rules \
  --min-count 1 \
  --max-count 3 \
  --count 1

# Add scale-out rule (CPU > 70%)
az monitor autoscale rule create \
  --resource-group pixcrawler-rg \
  --autoscale-name autoscale-rules \
  --condition "Percentage CPU > 70 avg 5m" \
  --scale out 1
```

#### 4. Reserved Instances

Save up to 72% with 1-year or 3-year commitments:

```bash
# Purchase reserved instance
az reservations reservation-order purchase \
  --reservation-order-id ORDER_ID \
  --sku P1V2 \
  --location eastus \
  --term P1Y  # 1 year
```

---

## Troubleshooting

### Common Issues

#### 1. Application Won't Start

**Symptoms**: 503 Service Unavailable

**Solutions**:
```bash
# Check logs
az webapp log tail --name pixcrawler-backend --resource-group pixcrawler-rg

# Verify startup script
az webapp config show --name pixcrawler-backend --resource-group pixcrawler-rg --query startupCommand

# Restart app
az webapp restart --name pixcrawler-backend --resource-group pixcrawler-rg
```

#### 2. Database Connection Fails

**Symptoms**: "Connection refused" or "Timeout"

**Solutions**:
```bash
# Verify DATABASE_URL is correct
az webapp config appsettings list --name pixcrawler-backend --resource-group pixcrawler-rg | grep DATABASE_URL

# Test connection from App Service
az webapp ssh --name pixcrawler-backend --resource-group pixcrawler-rg
# Inside SSH session:
python -c "import asyncpg; print('OK')"
```

#### 3. Blob Storage Access Denied

**Symptoms**: "AuthorizationPermissionMismatch"

**Solutions**:
```bash
# Verify connection string
az storage account show-connection-string --name pixcrawlerstorage --resource-group pixcrawler-rg

# Check container exists
az storage container list --account-name pixcrawlerstorage

# Verify container permissions
az storage container show --name pixcrawler-datasets --account-name pixcrawlerstorage
```

#### 4. High Memory Usage

**Symptoms**: App restarts frequently, 502 errors

**Solutions**:
```bash
# Check memory usage
az webapp show --name pixcrawler-backend --resource-group pixcrawler-rg --query "siteConfig.alwaysOn"

# Reduce Gunicorn workers
az webapp config set --name pixcrawler-backend --resource-group pixcrawler-rg --startup-file "bash startup-azure.sh"
# Edit startup-azure.sh: WORKERS=2 (instead of 4)

# Upgrade to larger SKU
az appservice plan update --name pixcrawler-plan --resource-group pixcrawler-rg --sku P1V2
```

#### 5. Celery Tasks Not Processing

**Symptoms**: Jobs stuck in "pending" status

**Solutions**:
```bash
# Check Redis is running
az webapp ssh --name pixcrawler-backend --resource-group pixcrawler-rg
# Inside SSH session:
redis-cli ping  # Should return "PONG"

# Check Celery worker logs
tail -f /tmp/celery-worker.log

# Restart Celery worker
pkill -f celery
celery -A celery_core.app worker --loglevel=info &
```

### Debug Mode

Enable debug logging temporarily:

```bash
az webapp config appsettings set \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg \
  --settings LOG_LEVEL=DEBUG

# View logs
az webapp log tail --name pixcrawler-backend --resource-group pixcrawler-rg

# Disable debug mode
az webapp config appsettings set \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg \
  --settings LOG_LEVEL=INFO
```

---

## Migration from Azure App Service to Azure Container Apps

If you need to migrate to Container Apps for better scalability:

### Why Container Apps?

- **Better scaling**: Scale to zero, scale based on HTTP traffic or queue length
- **Lower cost**: Pay only for what you use
- **Microservices**: Deploy multiple containers
- **Dapr integration**: Built-in service mesh

### Migration Steps

1. **Create Container Registry**:
```bash
az acr create \
  --name pixcrawlerregistry \
  --resource-group pixcrawler-rg \
  --sku Basic \
  --admin-enabled true
```

2. **Build and Push Docker Image**:
```bash
# Build image
docker build -t pixcrawler-backend:latest .

# Tag image
docker tag pixcrawler-backend:latest pixcrawlerregistry.azurecr.io/pixcrawler-backend:latest

# Login to ACR
az acr login --name pixcrawlerregistry

# Push image
docker push pixcrawlerregistry.azurecr.io/pixcrawler-backend:latest
```

3. **Create Container App Environment**:
```bash
az containerapp env create \
  --name pixcrawler-env \
  --resource-group pixcrawler-rg \
  --location eastus
```

4. **Deploy Container App**:
```bash
az containerapp create \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg \
  --environment pixcrawler-env \
  --image pixcrawlerregistry.azurecr.io/pixcrawler-backend:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 10 \
  --cpu 1.0 \
  --memory 2.0Gi \
  --env-vars \
    ENVIRONMENT=production \
    DEBUG=false \
    # ... (all other environment variables)
```

5. **Update DNS**:
```bash
# Get Container App URL
az containerapp show \
  --name pixcrawler-backend \
  --resource-group pixcrawler-rg \
  --query properties.configuration.ingress.fqdn
```

---

## Additional Resources

- [Azure App Service Documentation](https://docs.microsoft.com/azure/app-service/)
- [Azure Blob Storage Documentation](https://docs.microsoft.com/azure/storage/blobs/)
- [Azure Application Insights Documentation](https://docs.microsoft.com/azure/azure-monitor/app/app-insights-overview)
- [Azure Container Apps Documentation](https://docs.microsoft.com/azure/container-apps/)
- [PixCrawler Architecture Documentation](./architecture.md)
- [API Documentation](./API_DOCUMENTATION.md)

---

## Support

For deployment issues:
1. Check [Troubleshooting](#troubleshooting) section
2. Review Azure logs: `az webapp log tail`
3. Open GitHub issue: [pixcrawler/issues](https://github.com/pixcrawler/pixcrawler/issues)
4. Contact support: support@pixcrawler.com
