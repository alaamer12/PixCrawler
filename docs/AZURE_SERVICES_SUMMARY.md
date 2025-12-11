# Azure Services Configuration Summary

This document provides a comprehensive overview of Azure services integration in PixCrawler, including configuration, code structure, and deployment guidelines.

## Overview

PixCrawler integrates with the following Azure services:

1. **Azure Blob Storage** - Dataset storage with hot/cool/archive tiers
2. **Azure Application Insights** - Application performance monitoring
3. **Azure App Service** - Backend hosting (Linux container)
4. **Azure Static Web Apps** - Frontend hosting (optional, alternative to Vercel)

---

## Configuration Architecture

### Settings Structure

All Azure settings are organized in a modular, composable structure:

```
backend/core/settings/
├── azure.py              # Azure-specific settings (NEW)
│   ├── AzureBlobSettings
│   ├── AzureAppServiceSettings
│   ├── AzureStaticWebAppSettings
│   ├── AzureMonitorSettings
│   └── AzureSettings (composition)
├── base.py               # Includes azure: AzureSettings
├── storage.py            # Storage provider settings
└── __init__.py           # Exports all settings
```

### Environment Variables

All Azure configuration is done via environment variables with prefixes:

- `AZURE_BLOB_*` - Blob Storage settings
- `AZURE_APP_SERVICE_*` - App Service settings
- `AZURE_STATIC_WEB_APP_*` - Static Web Apps settings
- `AZURE_MONITOR_*` - Application Insights settings

See `.env.example.azure` for complete reference.

---

## Code Structure

### 1. Azure Settings (`backend/core/settings/azure.py`)

**Purpose**: Centralized Azure configuration with validation

**Features**:
- Pydantic-based settings with validation
- Environment variable prefixes for organization
- Connection string or account name/key support
- Lifecycle management configuration
- Access tier enums (Hot/Cool/Archive)
- Comprehensive validation rules

**Key Classes**:
```python
from backend.core.settings import AzureSettings, AzureBlobSettings

settings = get_settings()

# Access Azure settings
blob_config = settings.azure.blob
monitor_config = settings.azure.monitor

# Get connection string
connection_string = blob_config.get_connection_string()
```

### 2. Azure Blob Storage (`backend/storage/azure_blob.py`)

**Purpose**: Production-grade Blob Storage provider

**Features**:
- Optional dependency with graceful fallback
- Access tier management (Hot/Cool/Archive)
- SAS token generation
- Retry logic with exponential backoff
- Progress tracking for large uploads
- Metadata and tags support
- Archive rehydration handling

**Usage**:
```python
from backend.storage.factory import get_storage_provider

provider = get_storage_provider(settings.storage)

# Upload with tier
provider.upload(
    file_path="dataset.zip",
    destination_path="datasets/job_123/dataset.zip",
    tier="hot",
    metadata={"job_id": "123"},
    tags={"project": "pixcrawler"}
)

# Generate download URL
url = provider.generate_presigned_url(
    file_path="datasets/job_123/dataset.zip",
    expires_in=3600  # 1 hour
)

# Change tier for cost optimization
provider.set_blob_tier("datasets/old_job/dataset.zip", "archive")
```

### 3. Azure Monitor (`backend/core/monitoring/`)

**Purpose**: Application Insights integration

**Files**:
- `azure_monitor.py` - Monitor client implementation
- `__init__.py` - Exports and setup functions

**Features**:
- Custom events tracking
- Custom metrics tracking
- Exception tracking
- Request/response tracking
- Dependency tracking (DB, Redis, HTTP)
- Sampling for cost optimization

**Usage**:
```python
from backend.core.monitoring import setup_azure_monitor

monitor = setup_azure_monitor(
    connection_string=settings.azure.monitor.get_connection_string(),
    sampling_rate=1.0
)

# Track custom event
monitor.track_event("job_completed", {"job_id": "123"})

# Track metric
monitor.track_metric("images_processed", 1000)

# Track exception
try:
    # ... code ...
except Exception as e:
    monitor.track_exception(e, {"job_id": "123"})
```

### 4. Azure Monitor Middleware (`backend/core/middleware/azure_monitor.py`)

**Purpose**: Automatic request tracking

**Features**:
- Automatic HTTP request/response tracking
- Duration measurement
- Correlation ID propagation
- Exception tracking
- Configurable path exclusions

**Usage**:
```python
from backend.core.middleware import AzureMonitorMiddleware

app.add_middleware(
    AzureMonitorMiddleware,
    monitor_client=monitor,
    exclude_paths=["/health", "/metrics"]
)
```

### 5. Azure Integration Helper (`backend/core/azure_integration.py`)

**Purpose**: Simplified Azure services integration

**Functions**:
- `setup_azure_monitor_middleware()` - Setup monitoring with middleware
- `initialize_azure_services()` - Initialize all Azure services
- `check_azure_services_health()` - Health checks for Azure services

**Usage**:
```python
from backend.core.azure_integration import (
    setup_azure_monitor_middleware,
    initialize_azure_services,
)

# Initialize services
azure_status = initialize_azure_services(settings)

# Setup monitoring
monitor = setup_azure_monitor_middleware(app, settings)
```

---

## Deployment Configuration

### 1. Environment Variables (.env.example.azure)

Comprehensive template with:
- Application settings
- Supabase configuration
- Database configuration
- Redis configuration
- Azure Blob Storage (all options)
- Azure App Service settings
- Azure Static Web Apps (optional)
- Azure Application Insights
- Cost optimization notes

### 2. Startup Script (startup-azure.sh)

Handles:
1. UV package manager installation
2. Python dependencies installation
3. Redis server startup
4. Celery worker startup (background)
5. Gunicorn + Uvicorn startup (foreground)

### 3. Deployment Guide (docs/AZURE_DEPLOYMENT.md)

Complete step-by-step guide including:
- Prerequisites and tools
- Resource group creation
- Storage account setup
- Application Insights setup
- App Service creation
- Environment variable configuration
- Deployment options (local, GitHub)
- Monitoring and observability
- Cost optimization strategies
- Troubleshooting guide
- Migration to Container Apps

### 4. Integration Examples (docs/AZURE_INTEGRATION_EXAMPLE.md)

Code examples for:
- Basic integration in main.py
- Application startup with Azure
- Enhanced health checks
- Custom metrics tracking
- Error tracking
- Storage operations
- Lifecycle management
- Querying Azure Monitor data

---

## Dependencies

### Required (Production)

```toml
[project.dependencies]
azure-storage-blob = ">=12.19.0"  # Blob Storage
```

### Optional (Monitoring)

```toml
[project.optional-dependencies.azure]
opencensus-ext-azure = ">=1.1.0"  # Application Insights
opencensus-ext-fastapi = ">=0.1.0"  # FastAPI integration
opencensus-ext-requests = ">=0.8.0"  # HTTP tracking
opencensus-ext-sqlalchemy = ">=0.1.0"  # DB tracking
```

### Installation

```bash
# Install required dependencies
uv sync

# Install Azure monitoring (optional)
uv pip install "pixcrawler-backend[azure]"

# Or install manually
uv pip install opencensus-ext-azure opencensus-ext-fastapi
```

---

## Feature Flags

### Enable/Disable Azure Services

```bash
# Blob Storage
STORAGE_PROVIDER=azure  # or "local"

# Application Insights
AZURE_MONITOR_ENABLED=true  # or false

# Archive Tier
AZURE_BLOB_ENABLE_ARCHIVE=true  # or false

# Lifecycle Management
AZURE_BLOB_LIFECYCLE_ENABLED=true  # or false
```

### Graceful Degradation

All Azure services are optional and degrade gracefully:

1. **Blob Storage**: Falls back to local filesystem if unavailable
2. **Application Insights**: Application continues without monitoring
3. **Archive Tier**: Falls back to standard blob operations

---

## Cost Optimization

### 1. Blob Storage Lifecycle Management

**Configuration**:
```bash
AZURE_BLOB_LIFECYCLE_ENABLED=true
AZURE_BLOB_LIFECYCLE_COOL_AFTER_DAYS=30
AZURE_BLOB_LIFECYCLE_ARCHIVE_AFTER_DAYS=90
AZURE_BLOB_LIFECYCLE_DELETE_AFTER_DAYS=2555
```

**Savings**:
- Hot → Cool: 44% cost reduction
- Hot → Archive: 94% cost reduction

### 2. Application Insights Sampling

**Configuration**:
```bash
AZURE_MONITOR_SAMPLING_RATE=0.1  # 10% sampling
```

**Savings**:
- 90% reduction in telemetry costs
- Maintains statistical accuracy

### 3. App Service Scaling

**Options**:
- Auto-scaling based on CPU/memory
- Scale down during off-hours
- Reserved instances (up to 72% savings)

---

## Monitoring and Observability

### Application Insights Features

1. **Automatic Tracking**:
   - HTTP requests/responses
   - Database queries
   - Redis operations
   - External HTTP calls

2. **Custom Tracking**:
   - Business events (job_completed, user_signup)
   - Business metrics (images_processed, revenue)
   - Custom exceptions with context

3. **Dashboards**:
   - Application Map (dependencies visualization)
   - Live Metrics (real-time monitoring)
   - Performance Profiler
   - Failure Analysis

### Query Examples (KQL)

```kql
// View job completion events
customEvents
| where name == "job_completed"
| project timestamp, customDimensions.job_id, customDimensions.images_count
| order by timestamp desc

// View average images processed per hour
customMetrics
| where name == "images_processed"
| summarize avg(value) by bin(timestamp, 1h)

// View failed requests
requests
| where success == false
| project timestamp, name, resultCode, duration
| order by timestamp desc
```

---

## Security Best Practices

### 1. Connection Strings

- Store in Azure Key Vault (production)
- Use environment variables (never hardcode)
- Rotate regularly (90 days recommended)

### 2. SAS Tokens

- Short expiry (1 hour default)
- Minimal permissions (read-only when possible)
- Regenerate for each download

### 3. Access Tiers

- Private containers (no public access)
- Use SAS tokens for downloads
- Enable Azure AD authentication (optional)

### 4. Monitoring

- Enable Application Insights in production
- Set up alerts for critical errors
- Review security recommendations regularly

---

## Testing

### Local Development

```bash
# Use local storage provider
STORAGE_PROVIDER=local

# Disable monitoring
AZURE_MONITOR_ENABLED=false

# Run backend
.venv\Scripts\python -m uvicorn backend.main:app --reload
```

### Azure Integration Testing

```bash
# Use Azure Blob Storage
STORAGE_PROVIDER=azure
AZURE_BLOB_CONNECTION_STRING="..."

# Enable monitoring
AZURE_MONITOR_ENABLED=true
AZURE_MONITOR_CONNECTION_STRING="..."

# Run tests
.venv\Scripts\python -m pytest backend/tests/
```

---

## Migration Path

### From Local to Azure

1. **Create Azure Resources**:
   ```bash
   az group create --name pixcrawler-rg --location eastus
   az storage account create --name pixcrawlerstorage --resource-group pixcrawler-rg
   ```

2. **Update Environment Variables**:
   ```bash
   STORAGE_PROVIDER=azure
   AZURE_BLOB_CONNECTION_STRING="..."
   ```

3. **Migrate Existing Data** (optional):
   ```python
   from backend.storage.factory import get_storage_provider
   
   local_provider = LocalStorageProvider()
   azure_provider = AzureBlobStorageProvider(...)
   
   # Copy files
   for file in local_provider.list_files():
       azure_provider.upload(file, file)
   ```

### From Azure App Service to Container Apps

See [AZURE_DEPLOYMENT.md](./AZURE_DEPLOYMENT.md#migration-from-azure-app-service-to-azure-container-apps) for detailed migration guide.

---

## Troubleshooting

### Common Issues

1. **Blob Storage Connection Failed**
   - Verify connection string is correct
   - Check container exists
   - Verify network connectivity

2. **Application Insights Not Tracking**
   - Check connection string is valid
   - Verify SDK is installed
   - Wait 2-5 minutes for data to appear
   - Check sampling rate

3. **High Costs**
   - Enable lifecycle management
   - Reduce sampling rate
   - Use auto-scaling
   - Review Application Insights pricing tier

### Debug Mode

```bash
# Enable debug logging
LOG_LEVEL=DEBUG
AZURE_MONITOR_LOG_LEVEL=DEBUG

# View logs
az webapp log tail --name pixcrawler-backend --resource-group pixcrawler-rg
```

---

## Documentation Index

1. **[AZURE_DEPLOYMENT.md](./AZURE_DEPLOYMENT.md)** - Complete deployment guide
2. **[AZURE_INTEGRATION_EXAMPLE.md](./AZURE_INTEGRATION_EXAMPLE.md)** - Code examples
3. **[API_DOCUMENTATION.md](./API_DOCUMENTATION.md)** - API reference
4. **[architecture.md](./architecture.md)** - System architecture
5. **.env.example.azure** - Environment variables template

---

## Quick Start Checklist

### Development

- [ ] Copy `.env.example` to `.env`
- [ ] Set `STORAGE_PROVIDER=local`
- [ ] Set `AZURE_MONITOR_ENABLED=false`
- [ ] Run `uv sync`
- [ ] Start backend: `.venv\Scripts\python -m uvicorn backend.main:app --reload`

### Production (Azure)

- [ ] Create Azure resources (storage, insights, app service)
- [ ] Copy `.env.example.azure` to Azure Portal → Configuration
- [ ] Update all `YOUR_*` placeholders with actual values
- [ ] Set `STORAGE_PROVIDER=azure`
- [ ] Set `AZURE_MONITOR_ENABLED=true`
- [ ] Deploy application
- [ ] Verify health endpoint: `https://your-app.azurewebsites.net/health`
- [ ] Check Application Insights for telemetry

---

## Support and Resources

- **Azure Documentation**: https://docs.microsoft.com/azure/
- **Application Insights**: https://docs.microsoft.com/azure/azure-monitor/app/
- **Blob Storage**: https://docs.microsoft.com/azure/storage/blobs/
- **GitHub Issues**: https://github.com/pixcrawler/pixcrawler/issues
- **Email Support**: support@pixcrawler.com

---

## Changelog

### 2025-12-08 - Initial Azure Integration

- ✅ Added `AzureSettings` with modular configuration
- ✅ Enhanced `AzureBlobStorageProvider` with production features
- ✅ Implemented `AzureMonitorClient` for Application Insights
- ✅ Created `AzureMonitorMiddleware` for automatic tracking
- ✅ Added `azure_integration.py` helper module
- ✅ Created comprehensive deployment guide
- ✅ Added integration examples and code samples
- ✅ Updated `.env.example.azure` with all variables
- ✅ Added optional Azure dependencies to pyproject.toml
- ✅ Documented cost optimization strategies
- ✅ Added troubleshooting guide

### Future Enhancements

- [ ] Azure Container Apps deployment guide
- [ ] Azure Functions for serverless processing
- [ ] Azure CDN integration
- [ ] Azure Key Vault for secrets management
- [ ] Multi-region deployment guide
- [ ] Disaster recovery procedures
