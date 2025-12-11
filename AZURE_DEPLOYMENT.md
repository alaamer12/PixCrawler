# PixCrawler Azure Deployment Guide

## 🚀 **Complete Azure Deployment Setup**

This guide covers deploying PixCrawler to Azure with blob storage for datasets.

### 📋 **Prerequisites**

1. **Azure CLI** installed and authenticated
2. **Python 3.11+** with required packages
3. **Bun/Node.js** for frontend build
4. **Azure Subscription** with appropriate permissions

### 🔧 **Installation**

```bash
# Install Azure CLI (if not installed)
# Windows: winget install Microsoft.AzureCLI
# macOS: brew install azure-cli
# Linux: curl -sL https://aka.ms/InstallAzureCLI | sudo bash

# Install Python dependencies for deployment script
pip install azure-identity azure-mgmt-resource azure-mgmt-web azure-mgmt-storage azure-mgmt-monitor rich pydantic pydantic-settings

# Login to Azure
az login
```

### ⚙️ **Configuration**

1. **Copy and configure Azure environment file:**
```bash
cp .env.example.azure .env.azure
```

2. **Update `.env.azure` with your details:**
```bash
# Required: Get from Azure Portal → Subscriptions
AZURE_SUBSCRIPTION_ID=your-subscription-id-here

# Optional: Customize resource names
RESOURCE_GROUP=pixcrawler-rg
BACKEND_APP_NAME=pixcrawler-backend
FRONTEND_APP_NAME=pixcrawler-frontend
STORAGE_ACCOUNT_NAME=pixcrawlerstorage
```

### 🏗️ **Infrastructure Deployment**

```bash
# Deploy Azure infrastructure
python deploy-azure.py
```

This creates:
- ✅ **Resource Group**: `pixcrawler-rg`
- ✅ **App Service**: Backend API hosting
- ✅ **Storage Account**: Blob storage for datasets
- ✅ **Static Web App**: Frontend hosting
- ✅ **Blob Container**: `pixcrawler-datasets`
- ✅ **Application Insights**: Monitoring (optional)

### 📦 **Application Deployment**

#### Backend Deployment

```bash
# Option 1: Azure CLI (Recommended)
az webapp deploy \
  --resource-group pixcrawler-rg \
  --name pixcrawler-backend \
  --src-path . \
  --type zip

# Option 2: GitHub Actions (CI/CD)
# Configure GitHub repository secrets:
# - AZURE_WEBAPP_PUBLISH_PROFILE
# - AZURE_SUBSCRIPTION_ID
```

#### Frontend Deployment

```bash
# Build frontend
cd frontend
bun install
bun run build

# Deploy to Azure Static Web Apps
npx @azure/static-web-apps-cli deploy \
  --app-location . \
  --output-location .next \
  --resource-group pixcrawler-rg \
  --app-name pixcrawler-frontend
```

### 🔐 **Environment Variables Configuration**

Configure in **Azure Portal → App Service → Configuration → Application Settings**:

#### Required Variables
```bash
ENVIRONMENT=production
PIXCRAWLER_ENVIRONMENT=production
STORAGE_PROVIDER=azure

# Azure Blob Storage
AZURE_BLOB_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
AZURE_BLOB_ACCOUNT_NAME=pixcrawlerstorage
AZURE_BLOB_CONTAINER_NAME=pixcrawler-datasets
AZURE_BLOB_DEFAULT_TIER=hot

# Supabase (from Supabase Dashboard)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
DATABASE_URL=postgresql+asyncpg://postgres:password@db.your-project.supabase.co:5432/postgres

# Redis (local in App Service)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

### 🎯 **Key Features**

#### Azure Blob Storage Integration
- **Hot Tier**: Immediate access for new datasets
- **Cool Tier**: Cost optimization for older datasets
- **Archive Tier**: Long-term storage (90+ days)
- **SAS Tokens**: Secure download URLs
- **Lifecycle Management**: Automatic tier transitions

#### Professional Deployment
- **Backend Only**: Excludes frontend directory (`.deployignore`)
- **Frontend Only**: Excludes backend code (`frontend/.deployignore`)
- **Environment Separation**: Production vs development configs
- **Security**: Private blob containers with SAS token access

#### Simple Flow + Azure Integration
```python
# Automatic Azure upload after dataset completion
POST /api/v1/simple-flow/{flow_id}/upload-azure

# Response includes:
{
  "success": true,
  "uploaded_files": 150,
  "blob_prefix": "datasets/flow_abc123",
  "download_url": "https://storage.blob.core.windows.net/...",
  "manifest_url": "https://storage.blob.core.windows.net/.../manifest.json"
}
```

### 📊 **Cost Optimization**

#### Storage Tiers
- **Hot**: $0.018/GB/month - Active datasets
- **Cool**: $0.010/GB/month - 44% savings, 30-day minimum
- **Archive**: $0.001/GB/month - 94% savings, 180-day minimum

#### Recommended Strategy
1. Upload to **Hot** tier for immediate access
2. Move to **Cool** after 30 days (lifecycle policy)
3. Move to **Archive** after 90 days
4. Delete after 7 years for compliance

### 🔍 **Monitoring & Debugging**

#### Application Insights
```bash
# View logs in Azure Portal
az monitor app-insights query \
  --app pixcrawler-backend \
  --analytics-query "requests | limit 50"
```

#### Storage Monitoring
```bash
# Check blob storage usage
az storage blob list \
  --account-name pixcrawlerstorage \
  --container-name pixcrawler-datasets
```

### 🚨 **Troubleshooting**

#### Common Issues

1. **Deployment Fails**
   - Check `.deployignore` excludes frontend for backend
   - Verify Azure CLI authentication: `az account show`

2. **Storage Access Denied**
   - Verify connection string in environment variables
   - Check blob container permissions

3. **Frontend Build Fails**
   - Ensure Bun is installed: `bun --version`
   - Check Node.js version: `node --version` (>=18.0.0)

4. **Backend Startup Fails**
   - Check Application Insights logs
   - Verify all environment variables are set
   - Test Supabase connection

### 📋 **Deployment Checklist**

- [ ] Azure CLI installed and authenticated
- [ ] `.env.azure` configured with subscription ID
- [ ] Infrastructure deployed: `python deploy-azure.py`
- [ ] Backend deployed to App Service
- [ ] Frontend built and deployed to Static Web Apps
- [ ] Environment variables configured in Azure Portal
- [ ] Supabase connection tested
- [ ] Blob storage access verified
- [ ] Simple Flow system tested with Azure upload
- [ ] Monitoring and alerts configured

### 🎉 **Success Indicators**

- ✅ **Backend API**: `https://pixcrawler-backend.azurewebsites.net/docs`
- ✅ **Frontend**: `https://pixcrawler-frontend.azurestaticapps.net`
- ✅ **Storage**: Datasets uploaded to Azure Blob Storage
- ✅ **Monitoring**: Application Insights collecting telemetry
- ✅ **Simple Flow**: Creates datasets and uploads to Azure automatically

The deployment is **production-ready** with professional Azure integration! 🚀