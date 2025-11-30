# Cloud Applications

## Table of Contents

1. [psutil Accuracy on Cloud Systems](Cloud%20Applications%2029e461aa270580c0b2d3e114f97287d2.md)
2. [Azure-Specific Solutions](Cloud%20Applications%2029e461aa270580c0b2d3e114f97287d2.md)
3. [Azure Monitoring Tools Comparison](Cloud%20Applications%2029e461aa270580c0b2d3e114f97287d2.md)
4. [OpenCensus Implementation](Cloud%20Applications%2029e461aa270580c0b2d3e114f97287d2.md)
5. [Azure Alerts Configuration](Cloud%20Applications%2029e461aa270580c0b2d3e114f97287d2.md)

---

## psutil Accuracy on Cloud Systems {#psutil-accuracy}

### Overview

**Short Answer:** Partially accurate with important caveats.

### What psutil Reports on Cloud

| Metric | Local | Azure/AWS | Notes |
| --- | --- | --- | --- |
| CPU Usage | ✅ Accurate | ⚠️ Virtual CPU | Reports VM/container CPU, not physical |
| Memory | ✅ Accurate | ⚠️ Container limits | May not respect container memory limits |
| Disk Space | ✅ Accurate | ⚠️ Temp storage | Reports mounted volume, not quota |
| Network | ✅ Accurate | ✅ Accurate | Network I/O works well |
| Process Info | ✅ Accurate | ✅ Accurate | Process-level metrics work |

### Cloud-Specific Issues

### 1. Container Memory Limits (Docker/Kubernetes)

```python
import psutil

# psutil reports: 32GB (host machine)
# Actual limit: 2GB (container limit)
psutil.virtual_memory().total  # ❌ Wrong!

```

**Solution:** Read from `/sys/fs/cgroup/memory/memory.limit_in_bytes`

### 2. Azure Temp Storage

```python
# psutil reports disk space of mounted volume
# But Azure has quota limits not visible to OS
psutil.disk_usage('/tmp')  # May show 100GB, actual quota: 10GB

```

**Solution:** Use Azure SDK to check storage quotas

### 3. Ephemeral Storage Limits

- **Azure Functions:** Limited temp storage (~500MB)
- **AWS Lambda:** 512MB-10GB /tmp
- psutil won't know these limits

### Recommendation: Don't Rely on psutil for Cloud

Use **configuration-based limits** instead:

```python
# Configuration-based limits (works everywhere)
MAX_CONCURRENT_CHUNKS = 35
MAX_TEMP_STORAGE_MB = 8000  # 8GB (safety margin from 10GB limit)
CHUNK_SIZE_IMAGES = 500
ESTIMATED_IMAGE_SIZE_MB = 0.5  # 500KB avg

# Calculate capacity
max_images_in_temp = MAX_TEMP_STORAGE_MB / ESTIMATED_IMAGE_SIZE_MB
max_chunks_by_storage = int(max_images_in_temp / CHUNK_SIZE_IMAGES)

# Use the smaller limit
actual_max_chunks = min(MAX_CONCURRENT_CHUNKS, max_chunks_by_storage)

```

**Benefits:**

- ✅ Works on local, Azure, AWS
- ✅ Configurable per environment
- ✅ No dependency on psutil accuracy
- ✅ Safe with error margins

---

## Azure-Specific Solutions {#azure-solutions}

### 1. Configuration-Based Resource Management

```python
# backend/core/config.py
from pydantic import BaseSettings, Field

class ResourceSettings(BaseSettings):
    """Resource management settings."""

    # Environment detection
    environment: str = Field(default="local", description="Deployment environment")

    # Chunk processing limits
    max_concurrent_chunks: int = Field(
        default=35,
        ge=1,
        le=100,
        description="Maximum concurrent chunks to process"
    )

    # Storage limits (MB)
    max_temp_storage_mb: int = Field(
        default=8000,  # 8GB for Azure (10GB limit with 2GB margin)
        description="Maximum temp storage in MB"
    )

    chunk_size_images: int = Field(default=500, description="Images per chunk")
    estimated_image_size_mb: float = Field(default=0.5, description="Estimated average image size in MB")

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

### 2. Azure-Aware Resource Monitor

```python
# backend/services/resource_monitor.py
import os
from pathlib import Path
from typing import Optional

class ResourceMonitor:
    """Monitor resources with Azure-specific handling."""

    def __init__(self, settings: ResourceSettings):
        self.settings = settings
        self.is_azure = self._detect_azure()
        self.temp_dir = Path(os.getenv('TEMP', '/tmp'))

    def _detect_azure(self) -> bool:
        """Detect if running on Azure."""
        return bool(
            os.getenv('WEBSITE_INSTANCE_ID') or      # Azure App Service
            os.getenv('FUNCTIONS_WORKER_RUNTIME')    # Azure Functions
        )

    def get_temp_storage_usage_mb(self) -> float:
        """Get actual temp storage usage by counting our files."""
        total_size = 0
        try:
            # Count only our image files
            for file in self.temp_dir.glob('**/*.jpg'):
                total_size += file.stat().st_size
            for file in self.temp_dir.glob('**/*.png'):
                total_size += file.stat().st_size
        except Exception:
            pass

        return total_size / (1024**2)  # Convert to MB

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

    def _get_active_chunk_count(self) -> int:
        """Get count of currently processing chunks from database."""
        # Query database for chunks with status='processing'
        pass

```

### 3. Environment-Specific Configuration

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
PIXCRAWLER_MAX_CONCURRENT_CHUNKS=10   # Smaller for serverless
PIXCRAWLER_MAX_TEMP_STORAGE_MB=400    # 400MB (safe margin)

```

### Key Principles

1. **Don't Trust psutil on Azure** - Use configuration
2. **Track What You Create** - Count your own files
3. **Database as Source of Truth** - Track active chunks in DB/Redis
4. **Conservative Limits** - Use safety margins (8GB instead of 10GB)
5. **Environment-Aware** - Different limits per environment

---

## Azure Monitoring Tools Comparison {#monitoring-tools}

### Option 1: OpenCensus (Application Insights SDK)

**What it is:** Application-level telemetry library that pushes metrics to Azure.

**Pros:**

- ✅ Easy integration - Just add to your code, auto-collects metrics
- ✅ Low latency - Fire-and-forget, doesn't block your code
- ✅ Rich features - Traces, dependencies, exceptions, custom metrics
- ✅ Automatic collection - HTTP requests, database calls, exceptions
- ✅ No Azure credentials needed - Just connection string
- ✅ Works everywhere - Local, Azure, AWS (sends to Azure Insights)
- ✅ Built-in batching - Efficient metric aggregation

**Cons:**

- ❌ Push only - Can't query current state in code
- ❌ Delayed visibility - 1-2 min delay before metrics appear in portal
- ❌ No real-time decisions - Can't use for orchestration logic
- ❌ Cost - Charges per GB of telemetry data

**Use case:** Monitoring, alerting, debugging - NOT real-time control

### Option 2: Azure Monitor REST API

**What it is:** Query Azure resource metrics programmatically.

**Pros:**

- ✅ Pull metrics - Query current state on-demand
- ✅ Accurate - Azure's view of your resources
- ✅ Real quotas - Respects Azure limits
- ✅ Historical data - Query past metrics
- ✅ Platform metrics - CPU, memory, disk from Azure's perspective

**Cons:**

- ❌ Latency - 1-5 seconds per API call
- ❌ Rate limits - Max 1500 requests/hour per subscription
- ❌ Complexity - Requires authentication, resource IDs
- ❌ Azure-only - Won't work on local/AWS
- ❌ Delayed metrics - 1-2 min lag for some metrics
- ❌ Cost - API calls count toward quota

**Use case:** Dashboards, health checks, capacity planning - NOT real-time orchestration

### Recommendation: Hybrid Approach

**Use BOTH for different purposes:**

| Purpose | Tool | Why |
| --- | --- | --- |
| Real-time orchestration | Database + Config | Fast (< 10ms) |
| Monitoring dashboards | OpenCensus | Easy, automatic |
| Alerting | OpenCensus | Built-in alerts |
| Health checks | Azure Monitor API | Accurate quotas |
| Debugging | OpenCensus | Traces, exceptions |
| Capacity planning | Azure Monitor API | Historical data |

### Architecture Example

```python
class ChunkOrchestrator:
    """Orchestrate chunk processing with hybrid monitoring."""

    def __init__(self):
        # For REAL-TIME decisions (hot path)
        self.config = ResourceSettings()
        self.db = Database()  # Track active chunks

        # For MONITORING (cold path)
        self.insights = OpenCensusMonitor()  # Push telemetry
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
        # Process chunk...

        # ASYNC: Send telemetry (non-blocking)
        self.insights.track_event('chunk_started', {
            'chunk_id': chunk_id,
            'active_chunks': self.db.count_active_chunks(),
            'temp_storage_mb': self._count_temp_files_mb()
        })

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

---

## OpenCensus Implementation {#opencensus-implementation}

### Understanding "Push Only"

OpenCensus is **one-way communication**: Your code → Azure Insights

```python
# ✅ You can SEND metrics
monitor.track_metric('active_chunks', 35)
monitor.track_metric('temp_storage_mb', 4500)

# ❌ You CANNOT query metrics in code
current_chunks = monitor.get_metric('active_chunks')  # No such method!

```

### How Monitoring Works

```
┌──────────────────────────────────────────────────┐
│ YOUR APPLICATION                                 │
│                                                  │
│  def can_start_chunk():                         │
│      # Query database for decision              │
│      active = db.count_active_chunks()          │
│                                                  │
│      # Push to Azure (fire and forget)          │
│      insights.track_metric('active_chunks', active) │
│                                                  │
│      return active < 35                         │
└──────────────────────────────────────────────────┘
                    │
                    │ (push metrics)
                    ↓
┌──────────────────────────────────────────────────┐
│ AZURE APPLICATION INSIGHTS                       │
│                                                  │
│  Stores metrics, creates graphs, triggers alerts│
└──────────────────────────────────────────────────┘
                    │
                    │ (view/query)
                    ↓
┌──────────────────────────────────────────────────┐
│ AZURE PORTAL (You view here)                     │
│                                                  │
│  📊 Graph: active_chunks over time              │
│  🔔 Alert: active_chunks > 35                   │
│  📈 Dashboard: System health                    │
└──────────────────────────────────────────────────┘

```

### Complete Implementation

```python
# backend/services/monitoring.py
from opencensus.ext.azure.metrics_exporter import new_metrics_exporter
from opencensus.stats import aggregation, measure, stats, view
import os

class AzureMonitoring:
    """Azure monitoring with OpenCensus."""

    def __init__(self):
        connection_string = os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')
        if not connection_string:
            return  # Skip if not configured

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

### Usage in Orchestrator

```python
monitoring = AzureMonitoring()

def start_chunk(chunk_id: str):
    # Process chunk...

    # Track metrics
    active = db.count_active_chunks()
    monitoring.track_active_chunks(active)
    monitoring.track_storage_usage(get_temp_storage_mb())

```

---

## Azure Alerts Configuration {#azure-alerts}

### Overview

Metrics pushed via OpenCensus automatically become available for Azure Alerts in the portal.

### Setting Up Alerts in Azure Portal

**Step 1:** Navigate to Application Insights → Alerts → New Alert Rule

**Step 2:** Configure alert conditions:

```
Alert 1: Too Many Active Chunks
├── Signal: customMetrics/active_chunks
├── Condition: Greater than 35
├── Evaluation frequency: Every 5 minutes
└── Actions: Email + Slack webhook

Alert 2: Storage Critical
├── Signal: customMetrics/temp_storage_mb
├── Condition: Greater than 9000
├── Evaluation frequency: Every 5 minutes
└── Actions: SMS + auto-cleanup script

Alert 3: High Failure Rate
├── Signal: customMetrics/failed_chunks
├── Condition: Greater than 5 in 10 minutes
├── Evaluation frequency: Every 10 minutes
└── Actions: Page on-call engineer

```

### Available Actions

1. **Notifications:**
    - Email
    - SMS
    - Push notifications
    - Slack/Teams webhooks
2. **Auto-remediation:**
    - Scale up workers
    - Pause new job submissions
    - Clear temp storage
    - Restart services
3. **Escalation:**
    - Alert → Wait 10 min → Escalate to manager
    - Alert → Try auto-fix → If fails, page on-call

### Programmatic Alert Creation

```python
from azure.mgmt.monitor import MonitorManagementClient
from azure.mgmt.monitor.models import *

def create_alert_rule():
    """Create alert when active_chunks > 35."""

    alert_rule = AlertRuleResource(
        location='global',
        alert_rule_resource_name='high-chunk-count',
        description='Alert when active chunks exceed limit',
        is_enabled=True,
        condition=ThresholdRuleCondition(
            data_source=RuleMetricDataSource(
                metric_name='active_chunks'
            ),
            operator='GreaterThan',
            threshold=35,
            window_size='PT5M'  # 5 minutes
        ),
        actions=[
            RuleEmailAction(
                send_to_service_owners=True,
                custom_emails=['admin@company.com']
            )
        ]
    )

```

---

## Summary & Recommendations

### For Orchestration System

**Required:**

1. **Database (PostgreSQL/Supabase)** - Track chunk status and active count
2. **Configuration-based limits** - Define max chunks and storage limits

**Optional but Recommended:**

1. **OpenCensus** - Monitor and debug via Azure Portal dashboards
2. **Azure Monitor API** - Periodic health checks (every 5-10 minutes)

### Key Takeaways

✅ **Don't rely on psutil for cloud resource limits**

✅ **Use database as source of truth for real-time decisions**

✅ **Use OpenCensus for monitoring, not orchestration**

✅ **Set up Azure Alerts for proactive monitoring**

✅ **Use configuration-based limits with safety margins**

### Data Flow Architecture

```
ORCHESTRATION (Real-time, < 10ms)
└── Database/Redis ←→ Your Code → Decisions

MONITORING (Observability)
└── Your Code → OpenCensus → Azure Insights → Dashboards & Alerts

HEALTH CHECKS (Periodic, every 5-10 min)
└── Azure Monitor API → Your Code → Health status

```

[Tech Stack & Orchestration Tools Guide](Cloud%20Applications/Tech%20Stack%20&%20Orchestration%20Tools%20Guide%2029e461aa27058042a9aee549be105c22.md)

[Logging Strategy](Cloud%20Applications/Logging%20Strategy%2029e461aa27058005b792d1592d3b79c0.md)