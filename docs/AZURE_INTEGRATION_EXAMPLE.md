# Azure Integration Example for PixCrawler

This document provides code examples for integrating Azure services into the PixCrawler FastAPI backend.

## Table of Contents

- [Basic Integration](#basic-integration)
- [Application Startup](#application-startup)
- [Health Checks](#health-checks)
- [Custom Metrics](#custom-metrics)
- [Error Tracking](#error-tracking)
- [Storage Operations](#storage-operations)

---

## Basic Integration

### Update main.py

Add Azure Monitor middleware to your FastAPI application:

```python
"""
PixCrawler Backend API Server with Azure Integration
"""
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.v1.router import api_router
from backend.core.config import get_settings
from backend.core.azure_integration import (
    setup_azure_monitor_middleware,
    initialize_azure_services,
    check_azure_services_health,
)
from backend.core.monitoring import AzureMonitorClient
from utility.logging_config import get_logger

logger = get_logger(__name__)

# Global Azure Monitor client
azure_monitor: AzureMonitorClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager with Azure integration."""
    global azure_monitor
    
    logger.info("[*] Starting PixCrawler backend...")
    
    # Get settings
    settings = get_settings()
    
    # Initialize Azure services
    azure_status = initialize_azure_services(settings)
    
    # Setup Azure Monitor middleware
    azure_monitor = setup_azure_monitor_middleware(app, settings)
    
    # Track startup event
    if azure_monitor:
        azure_monitor.track_event(
            "application_started",
            properties={
                "environment": settings.environment,
                "azure_blob_enabled": azure_status["blob_storage"]["enabled"],
                "azure_insights_enabled": azure_status["application_insights"]["enabled"],
                "running_in_azure": azure_status["app_service"]["detected"],
            }
        )
    
    # Perform health checks
    azure_health = await check_azure_services_health(settings)
    logger.info(f"Azure services health: {azure_health}")
    
    logger.info("[+] Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("[*] Shutting down application...")
    
    # Track shutdown event
    if azure_monitor:
        azure_monitor.track_event("application_stopped")
        azure_monitor.flush()
    
    logger.info("[+] Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="PixCrawler API",
        description="Automated image dataset builder",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.security.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API router
    app.include_router(api_router, prefix="/api/v1")
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
```

---

## Application Startup

### Lifespan Events with Azure Tracking

```python
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from backend.core.azure_integration import (
    setup_azure_monitor_middleware,
    initialize_azure_services,
)
from backend.core.monitoring import AzureMonitorClient

azure_monitor: AzureMonitorClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan with comprehensive Azure integration."""
    global azure_monitor
    
    settings = get_settings()
    
    # Initialize Azure services
    azure_status = initialize_azure_services(settings)
    
    # Setup monitoring
    azure_monitor = setup_azure_monitor_middleware(app, settings)
    
    # Track startup metrics
    if azure_monitor:
        azure_monitor.track_metric(
            "application_startup_time",
            value=startup_duration,
            properties={"environment": settings.environment}
        )
    
    yield
    
    # Cleanup
    if azure_monitor:
        azure_monitor.flush()
```

---

## Health Checks

### Enhanced Health Endpoint with Azure Status

```python
from fastapi import APIRouter, Depends
from typing import Dict, Any

from backend.core.config import get_settings, Settings
from backend.core.azure_integration import check_azure_services_health

router = APIRouter()


@router.get("/health")
async def health_check(
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Comprehensive health check including Azure services.
    
    Returns:
        Health status of all services including Azure
    """
    # Check Azure services
    azure_health = await check_azure_services_health(settings)
    
    # Build response
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "database": await check_database_health(),
            "redis": await check_redis_health(),
            "celery": await check_celery_health(),
            "azure": azure_health,
        }
    }
    
    # Determine overall status
    all_healthy = all(
        service.get("healthy", False)
        for service_group in health_status["services"].values()
        if isinstance(service_group, dict)
        for service in (service_group.values() if isinstance(service_group, dict) else [service_group])
    )
    
    health_status["status"] = "healthy" if all_healthy else "degraded"
    
    return health_status
```

---

## Custom Metrics

### Track Business Metrics

```python
from backend.main import azure_monitor


async def process_crawl_job(job_id: int):
    """Process crawl job with Azure metrics tracking."""
    
    start_time = time.time()
    
    try:
        # Process job
        result = await crawl_images(job_id)
        
        # Track success metrics
        if azure_monitor:
            azure_monitor.track_metric(
                "images_processed",
                value=result.images_count,
                properties={
                    "job_id": str(job_id),
                    "status": "success",
                }
            )
            
            azure_monitor.track_event(
                "job_completed",
                properties={
                    "job_id": str(job_id),
                    "images_count": result.images_count,
                    "duration_seconds": time.time() - start_time,
                },
                measurements={
                    "images_processed": result.images_count,
                    "duration": time.time() - start_time,
                }
            )
        
        return result
        
    except Exception as e:
        # Track failure metrics
        if azure_monitor:
            azure_monitor.track_exception(
                exception=e,
                properties={
                    "job_id": str(job_id),
                    "error_type": type(e).__name__,
                }
            )
        raise
```

### Track Storage Operations

```python
async def upload_dataset(file_path: str, destination: str):
    """Upload dataset with Azure metrics."""
    
    start_time = time.time()
    file_size = Path(file_path).stat().st_size
    
    try:
        # Upload file
        provider = get_storage_provider()
        provider.upload(file_path, destination)
        
        # Track metrics
        if azure_monitor:
            azure_monitor.track_metric(
                "storage_upload_size_mb",
                value=file_size / 1024 / 1024,
                properties={
                    "destination": destination,
                    "tier": "hot",
                }
            )
            
            azure_monitor.track_dependency(
                name="azure_blob_upload",
                dependency_type="Azure Blob",
                target=destination,
                duration=time.time() - start_time,
                success=True,
                properties={
                    "file_size_mb": file_size / 1024 / 1024,
                }
            )
        
    except Exception as e:
        # Track failure
        if azure_monitor:
            azure_monitor.track_dependency(
                name="azure_blob_upload",
                dependency_type="Azure Blob",
                target=destination,
                duration=time.time() - start_time,
                success=False,
                properties={
                    "error": str(e),
                }
            )
        raise
```

---

## Error Tracking

### Automatic Exception Tracking

The Azure Monitor middleware automatically tracks exceptions, but you can add custom properties:

```python
from fastapi import HTTPException

from backend.main import azure_monitor


async def get_user_profile(user_id: str):
    """Get user profile with enhanced error tracking."""
    
    try:
        profile = await db.get_profile(user_id)
        
        if not profile:
            # Track custom event for not found
            if azure_monitor:
                azure_monitor.track_event(
                    "profile_not_found",
                    properties={
                        "user_id": user_id,
                        "endpoint": "/api/v1/users/profile",
                    }
                )
            
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return profile
        
    except HTTPException:
        raise
        
    except Exception as e:
        # Track unexpected errors with context
        if azure_monitor:
            azure_monitor.track_exception(
                exception=e,
                properties={
                    "user_id": user_id,
                    "operation": "get_user_profile",
                    "error_type": type(e).__name__,
                }
            )
        raise
```

### Track Rate Limit Violations

```python
from fastapi import Request
from fastapi_limiter.depends import RateLimiter

from backend.main import azure_monitor


async def rate_limit_callback(request: Request, response: Response, pexpire: int):
    """Callback when rate limit is exceeded."""
    
    # Track rate limit violation
    if azure_monitor:
        azure_monitor.track_event(
            "rate_limit_exceeded",
            properties={
                "path": request.url.path,
                "method": request.method,
                "client_ip": request.client.host,
                "expires_in_seconds": pexpire,
            }
        )
    
    raise HTTPException(
        status_code=429,
        detail="Too many requests"
    )
```

---

## Storage Operations

### Azure Blob Storage with Monitoring

```python
from backend.storage.factory import get_storage_provider
from backend.core.config import get_settings
from backend.main import azure_monitor


async def create_dataset_archive(job_id: int, images: list):
    """Create dataset archive with comprehensive monitoring."""
    
    settings = get_settings()
    provider = get_storage_provider(settings.storage)
    
    # Track operation start
    start_time = time.time()
    
    try:
        # Create ZIP archive
        archive_path = f"/tmp/dataset_{job_id}.zip"
        create_zip_archive(images, archive_path)
        
        # Upload to Azure Blob Storage
        destination = f"datasets/job_{job_id}/dataset.zip"
        
        if azure_monitor:
            azure_monitor.track_event(
                "dataset_upload_started",
                properties={
                    "job_id": str(job_id),
                    "image_count": len(images),
                    "destination": destination,
                }
            )
        
        # Upload with tier specification
        provider.upload(
            file_path=archive_path,
            destination_path=destination,
            tier="hot",  # Immediate access
            metadata={
                "job_id": str(job_id),
                "image_count": str(len(images)),
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            tags={
                "project": "pixcrawler",
                "type": "dataset",
                "job_id": str(job_id),
            }
        )
        
        # Generate SAS URL
        download_url = provider.generate_presigned_url(
            file_path=destination,
            expires_in=3600,  # 1 hour
        )
        
        # Track success
        duration = time.time() - start_time
        file_size = Path(archive_path).stat().st_size
        
        if azure_monitor:
            azure_monitor.track_event(
                "dataset_upload_completed",
                properties={
                    "job_id": str(job_id),
                    "destination": destination,
                    "tier": "hot",
                },
                measurements={
                    "duration_seconds": duration,
                    "file_size_mb": file_size / 1024 / 1024,
                    "image_count": len(images),
                }
            )
            
            azure_monitor.track_metric(
                "dataset_size_mb",
                value=file_size / 1024 / 1024,
                properties={
                    "job_id": str(job_id),
                    "tier": "hot",
                }
            )
        
        return {
            "download_url": download_url,
            "file_size": file_size,
            "duration": duration,
        }
        
    except Exception as e:
        # Track failure
        if azure_monitor:
            azure_monitor.track_exception(
                exception=e,
                properties={
                    "job_id": str(job_id),
                    "operation": "create_dataset_archive",
                }
            )
        raise
    
    finally:
        # Cleanup temp file
        if Path(archive_path).exists():
            Path(archive_path).unlink()
```

### Lifecycle Management Example

```python
async def archive_old_datasets():
    """Move old datasets to archive tier for cost optimization."""
    
    settings = get_settings()
    provider = get_storage_provider(settings.storage)
    
    # List all datasets
    datasets = provider.list_files(prefix="datasets/", include_metadata=True)
    
    archived_count = 0
    
    for dataset in datasets:
        # Check if older than 90 days
        age_days = (datetime.now(timezone.utc) - dataset["modified"]).days
        
        if age_days > 90 and dataset["tier"] != "Archive":
            try:
                # Move to archive tier
                provider.set_blob_tier(dataset["name"], "Archive")
                
                archived_count += 1
                
                # Track metric
                if azure_monitor:
                    azure_monitor.track_event(
                        "dataset_archived",
                        properties={
                            "dataset": dataset["name"],
                            "age_days": age_days,
                            "size_mb": dataset["size"] / 1024 / 1024,
                        }
                    )
                
            except Exception as e:
                logger.error(f"Failed to archive {dataset['name']}: {e}")
                
                if azure_monitor:
                    azure_monitor.track_exception(
                        exception=e,
                        properties={
                            "dataset": dataset["name"],
                            "operation": "archive_dataset",
                        }
                    )
    
    # Track summary metric
    if azure_monitor:
        azure_monitor.track_metric(
            "datasets_archived",
            value=archived_count,
        )
    
    return archived_count
```

---

## Query Azure Monitor Data

### Using Azure Portal

1. Go to Application Insights → Logs
2. Use Kusto Query Language (KQL):

```kql
// View custom events
customEvents
| where name == "job_completed"
| project timestamp, name, customDimensions
| order by timestamp desc

// View custom metrics
customMetrics
| where name == "images_processed"
| summarize avg(value), max(value), min(value) by bin(timestamp, 1h)
| order by timestamp desc

// View exceptions
exceptions
| where timestamp > ago(1h)
| project timestamp, type, outerMessage, customDimensions
| order by timestamp desc

// View dependencies (storage operations)
dependencies
| where type == "Azure Blob"
| project timestamp, name, target, duration, success
| order by timestamp desc
```

### Using Python SDK

```python
from azure.monitor.query import LogsQueryClient
from azure.identity import DefaultAzureCredential

# Create client
credential = DefaultAzureCredential()
client = LogsQueryClient(credential)

# Query logs
query = """
customEvents
| where name == "job_completed"
| where timestamp > ago(24h)
| summarize count() by bin(timestamp, 1h)
"""

response = client.query_workspace(
    workspace_id="YOUR_WORKSPACE_ID",
    query=query,
    timespan=timedelta(days=1)
)

for table in response.tables:
    for row in table.rows:
        print(row)
```

---

## Best Practices

### 1. Use Sampling in Production

```python
# In .env or Azure Portal
AZURE_MONITOR_SAMPLING_RATE=0.1  # 10% sampling for cost optimization
```

### 2. Add Correlation IDs

```python
# Middleware automatically adds X-Correlation-ID header
# Use it in logs and metrics for request tracing

if azure_monitor:
    azure_monitor.track_event(
        "operation_completed",
        properties={
            "correlation_id": request.state.correlation_id,
            "operation": "process_job",
        }
    )
```

### 3. Track Business KPIs

```python
# Track important business metrics
if azure_monitor:
    azure_monitor.track_metric("daily_active_users", user_count)
    azure_monitor.track_metric("revenue_usd", revenue)
    azure_monitor.track_metric("conversion_rate", rate)
```

### 4. Use Custom Dimensions

```python
# Add context to all events
if azure_monitor:
    azure_monitor.track_event(
        "user_action",
        properties={
            "user_id": user.id,
            "user_tier": user.subscription_tier,
            "action": "create_job",
            "environment": settings.environment,
        }
    )
```

---

## Troubleshooting

### Monitor Not Tracking Events

1. Check connection string is valid
2. Verify SDK is installed: `pip list | grep opencensus`
3. Check sampling rate (might be filtering events)
4. Wait 2-5 minutes for data to appear in Azure Portal

### High Costs

1. Reduce sampling rate: `AZURE_MONITOR_SAMPLING_RATE=0.1`
2. Exclude noisy endpoints from tracking
3. Use custom metrics sparingly
4. Review Application Insights pricing tier

### Missing Dependencies

```bash
# Install Azure Monitor SDK
pip install opencensus-ext-azure

# Or with UV
uv pip install opencensus-ext-azure
```

---

## Additional Resources

- [Azure Application Insights Documentation](https://docs.microsoft.com/azure/azure-monitor/app/app-insights-overview)
- [OpenCensus Python Documentation](https://opencensus.io/python/)
- [Kusto Query Language (KQL) Reference](https://docs.microsoft.com/azure/data-explorer/kusto/query/)
- [PixCrawler Azure Deployment Guide](./AZURE_DEPLOYMENT.md)
