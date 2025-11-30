# Local vs Cloud-Native Solutions

## Overview

This guide explains the limitations of psutil on cloud systems and recommends appropriate monitoring strategies for Azure deployments.

## psutil Accuracy on Cloud Systems

### Comparison Table

| Metric | Local | Azure/AWS | Notes |
| --- | --- | --- | --- |
| CPU Usage | ✅ Accurate | ⚠️ Virtual CPU | Reports VM/container CPU, not physical |
| Memory | ✅ Accurate | ⚠️ Container limits | May not respect container memory limits |
| Disk Space | ✅ Accurate | ⚠️ Temp storage | Reports mounted volume, not quota |
| Network | ✅ Accurate | ✅ Accurate | Network I/O works well |
| Process Info | ✅ Accurate | ✅ Accurate | Process-level metrics work |

### Cloud-Specific Issues

**1. Container Memory Limits (Docker/Kubernetes)**

```python
import psutil

# psutil reports: 32GB (host machine)
# Actual limit: 2GB (container limit)
psutil.virtual_memory().total  # ❌ Wrong!

```

**Solution**: Read from `/sys/fs/cgroup/memory/memory.limit_in_bytes`

**2. Azure Temp Storage**

```python
# psutil reports disk space of mounted volume
# But Azure has quota limits not visible to OS
psutil.disk_usage('/tmp')  # May show 100GB
# Actual quota: 10GB

```

**3. Ephemeral Storage Limitations**

- Azure Functions: Limited temp storage (~500MB)
- AWS Lambda: 512MB-10GB /tmp
- psutil won't know these limits

## Recommended Solution: Configuration-Based Approach

### Configuration Settings

```python
# backend/core/config.py
class ResourceSettings(BaseSettings):
    """Resource management settings."""

    # Environment detection
    environment: str = Field(default="local")

    # Chunk processing limits
    max_concurrent_chunks: int = Field(default=35, ge=1, le=100)

    # Storage limits (MB)
    max_temp_storage_mb: int = Field(
        default=8000,  # 8GB for Azure (10GB limit with 2GB margin)
    )

    chunk_size_images: int = Field(default=500)
    estimated_image_size_mb: float = Field(default=0.5)  # 500KB average

    @property
    def max_chunks_by_storage(self) -> int:
        """Calculate max chunks based on storage capacity."""
        max_images = self.max_temp_storage_mb / self.estimated_image_size_mb
        return int(max_images / self.chunk_size_images)

    @property
    def effective_max_chunks(self) -> int:
        """Get effective max chunks (smaller of config and storage)."""
        return min(self.max_concurrent_chunks, self.max_chunks_by_storage)

```

### Resource Monitor Implementation

```python
# backend/services/resource_monitor.py
import os
from pathlib import Path

class ResourceMonitor:
    """Monitor resources with Azure-specific handling."""

    def __init__(self, settings: ResourceSettings):
        self.settings = settings
        self.is_azure = self._detect_azure()
        self.temp_dir = Path(os.getenv('TEMP', '/tmp'))

    def _detect_azure(self) -> bool:
        """Detect if running on Azure."""
        return bool(
            os.getenv('WEBSITE_INSTANCE_ID') or  # Azure App Service
            os.getenv('FUNCTIONS_WORKER_RUNTIME')  # Azure Functions
        )

    def get_temp_storage_usage_mb(self) -> float:
        """Get actual temp storage usage by counting our files."""
        total_size = 0
        try:
            for file in self.temp_dir.glob('**/*.jpg'):
                total_size += file.stat().st_size
            for file in self.temp_dir.glob('**/*.png'):
                total_size += file.stat().st_size
        except Exception:
            pass

        return total_size / (1024**2)

    def get_available_storage_mb(self) -> float:
        """Get available storage based on our limits."""
        used = self.get_temp_storage_usage_mb()
        return self.settings.max_temp_storage_mb - used

    def can_start_chunk(self) -> bool:
        """Check if we can start a new chunk."""
        # Check storage capacity
        required_mb = self.settings.chunk_size_images * self.settings.estimated_image_size_mb
        available_mb = self.get_available_storage_mb()

        if available_mb < required_mb:
            return False

        # Check active chunks (from database/Redis)
        active_chunks = self._get_active_chunk_count()
        if active_chunks >= self.settings.effective_max_chunks:
            return False

        return True

```

### Environment-Specific Configuration

```bash
# .env.local
PIXCRAWLER_ENVIRONMENT=local
PIXCRAWLER_MAX_CONCURRENT_CHUNKS=35
PIXCRAWLER_MAX_TEMP_STORAGE_MB=20000  # 20GB on local

# .env.azure (Azure App Service)
PIXCRAWLER_ENVIRONMENT=azure
PIXCRAWLER_MAX_CONCURRENT_CHUNKS=35
PIXCRAWLER_MAX_TEMP_STORAGE_MB=8000   # 8GB (safe margin)

# Azure Functions (if migrating later)
PIXCRAWLER_ENVIRONMENT=azure_functions
PIXCRAWLER_MAX_CONCURRENT_CHUNKS=10
PIXCRAWLER_MAX_TEMP_STORAGE_MB=400    # 400MB (safe margin)

```

## Azure Native Monitoring Tools

### 1. OpenCensus (Application Insights SDK) - Recommended

**Purpose**: Push telemetry data to Azure for monitoring and alerting

**Installation**:

```bash
pip install opencensus-ext-azure

```

**Implementation**:

```python
from opencensus.ext.azure.metrics_exporter import new_metrics_exporter
from opencensus.stats import aggregation, measure, stats, view

class AzureMonitoring:
    """Azure monitoring with OpenCensus."""

    def __init__(self):
        connection_string = os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')
        if not connection_string:
            return

        self.stats = stats.stats
        self.view_manager = self.stats.view_manager
        self.stats_recorder = self.stats.stats_recorder

        # Define metrics
        self.active_chunks = measure.MeasureInt(
            "active_chunks",
            "Active processing chunks",
            "chunks"
        )

        self.temp_storage = measure.MeasureFloat(
            "temp_storage_mb",
            "Temp storage usage",
            "MB"
        )

        self.failed_chunks = measure.MeasureInt(
            "failed_chunks",
            "Failed chunks count",
            "chunks"
        )

        # Register views
        self._register_views()

        # Setup exporter
        exporter = new_metrics_exporter(connection_string=connection_string)
        self.view_manager.register_exporter(exporter)

    def _register_views(self):
        """Register metric views."""
        views = [
            view.View(
                "active_chunks_view",
                "Active chunks",
                [],
                self.active_chunks,
                aggregation.LastValueAggregation()
            ),
            view.View(
                "temp_storage_view",
                "Temp storage",
                [],
                self.temp_storage,
                aggregation.LastValueAggregation()
            ),
            view.View(
                "failed_chunks_view",
                "Failed chunks",
                [],
                self.failed_chunks,
                aggregation.CountAggregation()
            )
        ]

        for v in views:
            self.view_manager.register_view(v)

    def track_active_chunks(self, count: int):
        """Track active chunk count."""
        mmap = self.stats_recorder.new_measurement_map()
        mmap.measure_int_put(self.active_chunks, count)
        mmap.record()

    def track_storage_usage(self, mb: float):
        """Track storage usage."""
        mmap = self.stats_recorder.new_measurement_map()
        mmap.measure_float_put(self.temp_storage, mb)
        mmap.record()

    def track_chunk_failed(self):
        """Track chunk failure."""
        mmap = self.stats_recorder.new_measurement_map()
        mmap.measure_int_put(self.failed_chunks, 1)
        mmap.record()

```

**Pros**:

- ✅ Easy integration - Just add to your code
- ✅ Low latency - Fire-and-forget, doesn't block your code
- ✅ Rich features - Traces, dependencies, exceptions, custom metrics
- ✅ Automatic collection - HTTP requests, database calls
- ✅ No Azure credentials needed - Just connection string
- ✅ Works everywhere - Local, Azure, AWS

**Cons**:

- ❌ Push only - Can't query current state in code
- ❌ Delayed visibility - 1-2 min delay before metrics appear
- ❌ Not for real-time decisions - Only for monitoring

### 2. Azure Monitor REST API

**Purpose**: Query Azure resource metrics programmatically

**Installation**:

```bash
pip install azure-mgmt-monitor azure-identity

```

**Implementation**:

```python
from azure.identity import DefaultAzureCredential
from azure.mgmt.monitor import MonitorManagementClient

class AzureResourceMonitor:
    """Query Azure resource metrics."""

    def __init__(self, subscription_id: str, resource_group: str, app_name: str):
        credential = DefaultAzureCredential()
        self.client = MonitorManagementClient(credential, subscription_id)
        self.resource_id = (
            f"/subscriptions/{subscription_id}"
            f"/resourceGroups/{resource_group}"
            f"/providers/Microsoft.Web/sites/{app_name}"
        )

    def get_cpu_percentage(self) -> float:
        """Get CPU percentage from Azure."""
        metrics = self.client.metrics.list(
            self.resource_id,
            metricnames='CpuPercentage',
            timespan='PT1M'  # Last 1 minute
        )
        # Parse and return latest value

    def get_memory_percentage(self) -> float:
        """Get memory percentage from Azure."""
        metrics = self.client.metrics.list(
            self.resource_id,
            metricnames='MemoryPercentage',
            timespan='PT1M'
        )

    def get_filesystem_usage(self) -> float:
        """Get filesystem usage from Azure."""
        metrics = self.client.metrics.list(
            self.resource_id,
            metricnames='FileSystemUsage',
            timespan='PT1M'
        )

```

**Pros**:

- ✅ Pull metrics - Query current state on-demand
- ✅ Accurate - Azure's view of your resources
- ✅ Real quotas - Respects Azure limits
- ✅ Historical data - Query past metrics

**Cons**:

- ❌ Latency - 1-5 seconds per API call
- ❌ Rate limits - Max 1500 requests/hour per subscription
- ❌ Complexity - Requires authentication, resource IDs
- ❌ Azure-only - Won't work on local/AWS
- ❌ Not for real-time orchestration - Too slow

## Comparison: OpenCensus vs Azure Monitor REST API

| Feature | OpenCensus | Azure Monitor API |
| --- | --- | --- |
| **Send metrics** | ✅ Yes | ❌ No |
| **Query metrics** | ❌ No | ✅ Yes |
| **Real-time decisions** | ❌ No | ⚠️ Slow (1-2s) |
| **Monitoring/Dashboards** | ✅ Yes | ✅ Yes |
| **Latency** | Low (async) | High (1-5s) |
| **Works offline** | ✅ Yes | ❌ No |
| **Authentication needed** | ❌ No | ✅ Yes |

## Setting Up Azure Alerts

### In Azure Portal

```
Application Insights → Alerts → New Alert Rule

Condition:
- Metric: customMetrics/active_chunks
- Operator: Greater than
- Threshold: 35
- Evaluation frequency: Every 5 minutes

Actions:
- Send email to: admin@yourcompany.com
- Send SMS to: +1234567890
- Trigger webhook: <https://your-slack-webhook>
- Run Azure Function: auto_scale_workers()

```

### Alert Examples

**Alert 1: Too many active chunks**

- Metric: `customMetrics/active_chunks`
- Condition: `> 35`
- Action: Email + Slack webhook

**Alert 2: Storage critical**

- Metric: `customMetrics/temp_storage_mb`
- Condition: `> 9000`
- Action: SMS + auto-cleanup script

**Alert 3: High failure rate**

- Metric: `customMetrics/failed_chunks`
- Condition: `> 5 in 10 minutes`
- Action: Page on-call engineer

## Recommended Architecture: Hybrid Approach

### Complete Implementation

```python
class ChunkOrchestrator:
    """Orchestrate chunk processing with hybrid monitoring."""

    def __init__(self):
        # For REAL-TIME decisions (hot path)
        self.config = ResourceSettings()
        self.db = Database()  # Source of truth

        # For MONITORING (cold path)
        self.insights = AzureMonitoring()  # Optional
        self.azure_api = None  # Optional, for health checks

    def can_start_chunk(self) -> bool:
        """Real-time decision: Can we start a chunk?"""
        # FAST: Query database (< 10ms)
        active_chunks = self.db.count_active_chunks()

        # FAST: Check config limit
        if active_chunks >= self.config.max_concurrent_chunks:
            return False

        # FAST: Check temp storage (count files)
        temp_usage = self._count_temp_files_mb()
        if temp_usage > self.config.max_temp_storage_mb * 0.8:
            return False

        return True

    def start_chunk(self, chunk_id: str):
        """Start processing a chunk."""
        # 1. Update database (source of truth)
        self.db.execute(
            "UPDATE chunks SET status='processing' WHERE id=?",
            chunk_id
        )

        # 2. Process the chunk
        self._process_chunk(chunk_id)

        # 3. Send telemetry to Azure (non-blocking, optional)
        if self.insights:
            active = self.db.count_active_chunks()
            self.insights.track_active_chunks(active)
            self.insights.track_storage_usage(self._count_temp_files_mb())

    async def health_check(self) -> dict:
        """Periodic health check (every 5 minutes)."""
        # SLOW: Query Azure API (only for health checks)
        if self.azure_api:
            azure_cpu = await self.azure_api.get_cpu_percentage()
            azure_memory = await self.azure_api.get_memory_percentage()

            # Send to insights for alerting
            self.insights.track_metric('azure_cpu', azure_cpu)
            self.insights.track_metric('azure_memory', azure_memory)

        return {
            'active_chunks': self.db.count_active_chunks(),
            'azure_cpu': azure_cpu,
            'azure_memory': azure_memory
        }

```

## Decision Matrix

| Purpose | Tool | Why |
| --- | --- | --- |
| **Real-time orchestration** | Database + Config | Fast (< 10ms) |
| **Monitoring dashboards** | OpenCensus | Easy, automatic |
| **Alerting** | OpenCensus + Azure Alerts | Built-in alerts |
| **Health checks** | Azure Monitor API | Accurate quotas |
| **Debugging** | OpenCensus | Traces, exceptions |
| **Capacity planning** | Azure Monitor API | Historical data |

## Data Flow Architecture

```
┌─────────────────────────────────────────────────┐
│ ORCHESTRATION (Real-time decisions)             │
│                                                  │
│  Database/Redis ←→ Your Code                    │
│  (Query state)      (Make decisions)            │
│                                                  │
│  - Can I start chunk? → Query DB                │
│  - How many active? → Query DB                  │
│  - Storage usage? → Count files                 │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ MONITORING (Observability, not decisions)       │
│                                                  │
│  Your Code → OpenCensus → Azure Insights        │
│  (Send metrics)           (View dashboards)     │
│                                                  │
│  - Track chunk started                          │
│  - Track storage usage                          │
│  - Track errors                                 │
│  - Set up alerts                                │
└─────────────────────────────────────────────────┘

```

## Key Principles

1. **Don't Trust psutil on Azure** - Use configuration-based limits
2. **Track What You Create** - Count your own files for storage
3. **Database as Source of Truth** - Track active chunks in DB/Redis
4. **Conservative Limits** - Use safety margins (8GB instead of 10GB)
5. **Environment-Aware** - Different limits per environment
6. **Use Azure Tools for Monitoring** - Not for orchestration decisions

## Installation Requirements

```bash
# Required (for orchestration)
pip install sqlalchemy asyncpg redis

# Recommended (for monitoring)
pip install opencensus-ext-azure

# Optional (for health checks)
pip install azure-mgmt-monitor azure-identity

```

## Summary

**For orchestration (real-time decisions)**:

- ✅ Use Database/Redis to track active chunks
- ✅ Use configuration-based limits
- ✅ Count your own temp files for storage tracking
- ❌ Don't use psutil on cloud
- ❌ Don't use Azure APIs (too slow)

**For monitoring and alerting**:

- ✅ Use OpenCensus to push metrics
- ✅ View dashboards in Azure Portal
- ✅ Set up alerts in Azure Portal
- ✅ Use Azure Monitor API for periodic health checks (optional)

This approach is portable, accurate, safe, configurable, and works everywhere (local, Azure, AWS).