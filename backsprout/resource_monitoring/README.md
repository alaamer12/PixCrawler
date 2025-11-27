# Resource Monitoring Service

## Module Overview
The **Resource Monitoring Service** is a production-ready microservice designed to ensure the stability of the PixCrawler platform. It continuously monitors system resources (disk, memory) and application-specific metrics (active processing chunks) to prevent resource exhaustion and ensure smooth operation.

It supports two operational modes:
- **Local**: Uses `psutil` for direct system monitoring.
- **Azure**: Integrates with Azure Monitor via REST API to retrieve cloud metrics.

## Folder Structure and Files

| File | Description |
|------|-------------|
| `__init__.py` | Package initialization. |
| `config.py` | Configuration management using Pydantic Settings. Handles env vars and defaults. |
| `service_runner.py` | Main entry point. Runs the polling loop and the FastAPI metrics endpoint. |
| `monitoring_local.py` | Implementation for local system monitoring (disk/memory) using `psutil`. |
| `monitoring_azure.py` | Implementation for Azure Monitor integration (REST API with auth fallback). |
| `chunk_tracker.py` | Logic to count active chunks from the database (ORM with SQL fallback). |
| `threshold_manager.py` | Evaluates current metrics against configured warning/alert thresholds. |
| `alerting.py` | Handles logging of alerts and warnings to the project logger. |
| `metrics_endpoint.py` | FastAPI application exposing `/metrics` and `/health` endpoints. |

## Production-Ready Action Plan

To deploy this service in a production environment:

1.  **Environment Configuration**: Ensure all required environment variables (especially for Azure and Database) are securely injected.
2.  **Deployment Strategy**: Deploy as a sidecar container alongside the main backend or as a standalone service in Azure App Service/Functions.
3.  **Monitoring Integration**: Configure your centralized logging system (e.g., Azure Application Insights, ELK Stack) to ingest logs from this service.
4.  **Alerting Rules**: Set up external alerts based on the `/metrics` endpoint or specific log patterns (`RESOURCE ALERT`).

## Verification Steps

### Local Verification
1.  **Install Dependencies**:
    ```bash
    pip install psutil requests python-dotenv fastapi uvicorn pydantic pydantic-settings sqlalchemy asyncpg
    ```
2.  **Run Service**:
    ```bash
    python -m backsprout.resource_monitoring.service_runner
    ```
3.  **Check Health**:
    ```bash
    curl http://localhost:8000/health
    # Output: {"status": "healthy"}
    ```
4.  **Check Metrics**:
    ```bash
    curl http://localhost:8000/metrics
    ```

### Azure Verification
1.  Set `PIXCRAWLER_MODE=azure`.
2.  Set `PIXCRAWLER_AZURE_RESOURCE_ID` and ensure the environment has a Managed Identity with `Monitoring Reader` permissions.
3.  Run the service and verify logs show successful metric queries.

## Threshold Testing Instructions

To verify the alerting logic without waiting for a real disaster:

1.  **Modify Thresholds**: Temporarily lower the thresholds in your `.env` file or environment variables.
    ```ini
    PIXCRAWLER_MEMORY_THRESHOLD_WARN=10.0
    PIXCRAWLER_MEMORY_THRESHOLD_ALERT=20.0
    ```
2.  **Restart Service**: The service picks up new config on restart.
3.  **Observe Logs**: You should see `RESOURCE WARNING` or `RESOURCE ALERT` logs immediately if your system usage is above these low values.
4.  **Verify Endpoint**: Check `/metrics` and confirm the `statuses` dictionary reflects `WARN` or `ALERT`.

## Logging and Monitoring

The service uses the standard Python `logging` module with the namespace `PixCrawler.resource_monitoring`.

**Log Format**:
```text
RESOURCE [LEVEL] [TIMESTAMP] - [METRIC]: [VALUE] (Status: [STATUS])
```

**Example**:
```text
RESOURCE ALERT [2023-10-27T14:30:00.123] - MEMORY: 95.5 (Status: ALERT)
```

**Metrics Endpoint**:
`GET /metrics` returns a JSON object containing:
- `metrics`: Raw values (e.g., `memory_pct`, `active_chunks`).
- `statuses`: Evaluated status for each metric (`OK`, `WARN`, `ALERT`).
- `last_updated`: Timestamp of the last poll.

## Deployment Instructions

### Docker
The service can be containerized using a standard Python image. Ensure the `backsprout` directory is in the `PYTHONPATH`.

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "-m", "backsprout.resource_monitoring.service_runner"]
```

### Azure
Deploy as a background worker or sidecar. Ensure the Managed Identity is assigned to the resource.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PIXCRAWLER_MODE` | `local` | `local` or `azure` |
| `PIXCRAWLER_POLL_INTERVAL_SECONDS` | `60` | Polling frequency in seconds |
| `PIXCRAWLER_DB_URL` | (Backend Config) | Database connection string |
| `PIXCRAWLER_DISK_THRESHOLD_WARN` | `80.0` | Disk warning threshold (%) |
| `PIXCRAWLER_DISK_THRESHOLD_ALERT` | `90.0` | Disk alert threshold (%) |
| `PIXCRAWLER_MEMORY_THRESHOLD_WARN` | `80.0` | Memory warning threshold (%) |
| `PIXCRAWLER_MEMORY_THRESHOLD_ALERT` | `90.0` | Memory alert threshold (%) |
| `PIXCRAWLER_CHUNK_THRESHOLD_WARN` | `35` | Active chunks warning threshold |
| `PIXCRAWLER_CHUNK_THRESHOLD_ALERT` | `40` | Active chunks alert threshold |
| `AZURE_CLIENT_ID` | `None` | Service Principal Client ID (Fallback) |
| `AZURE_CLIENT_SECRET` | `None` | Service Principal Secret (Fallback) |
| `AZURE_TENANT_ID` | `None` | Service Principal Tenant ID (Fallback) |
| `PIXCRAWLER_AZURE_RESOURCE_ID` | `None` | Azure Resource ID to monitor |

## Feedback & Fixes Applied

During the final review, the following improvements and fixes were applied to ensure production readiness:

1.  **Azure Metrics Parsing**: Implemented robust JSON parsing for Azure Monitor responses to correctly extract metric values (handling `average` and `total` aggregations).
2.  **Signal Handling**: Simplified `service_runner.py` to leverage Uvicorn's built-in signal handling for graceful shutdowns.
3.  **Metric Key Standardization**: Standardized internal metric keys (e.g., using `memory_pct` consistently) to ensure `threshold_manager.py` correctly evaluates all metrics.
4.  **Import Robustness**: Enhanced `chunk_tracker.py` to gracefully handle *any* exception during backend model import (including Pydantic validation errors), ensuring the service falls back to raw SQL reliability.
5.  **Configuration Flexibility**: Added `AZURE_METRIC_NAMES` to `config.py` to allow customization of queried Azure metrics without code changes.
6.  **Code Cleanup**: Removed redundant code in the polling loop.
