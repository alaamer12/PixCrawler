# Resource Monitoring Service

## Module Overview
The **Resource Monitoring Service** is a lightweight, standalone microservice within the **BackSprout** project (part of PixCrawler). Its primary objective is to monitor system health (disk, memory) and application-specific metrics (active processing chunks) to ensure stability and prevent resource exhaustion.

It operates in two modes:
- **Local**: Uses `psutil` to monitor the local machine.
- **Azure**: Queries Azure Monitor via REST API for cloud metrics.

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

## Installation & Dependencies

The service requires Python 3.10+ and the following dependencies:

```bash
pip install psutil requests python-dotenv fastapi uvicorn pydantic pydantic-settings sqlalchemy asyncpg
```

### Environment Setup
Create a `.env` file in the project root (or set environment variables):

```ini
# Core
PIXCRAWLER_MODE=local                  # "local" or "azure"
PIXCRAWLER_POLL_INTERVAL_SECONDS=60    # Polling frequency

# Database (Optional - defaults to backend config or localhost)
PIXCRAWLER_DB_URL=postgresql+asyncpg://user:pass@localhost:5432/pixcrawler

# Azure (Required if MODE=azure)
AZURE_CLIENT_ID=...
AZURE_CLIENT_SECRET=...
AZURE_TENANT_ID=...
PIXCRAWLER_AZURE_RESOURCE_ID=/subscriptions/.../resourceGroups/.../providers/...
```

## Configuration

Configuration is managed via `config.py`. You can override defaults using environment variables.

| Setting | Env Variable | Default | Description |
|---------|--------------|---------|-------------|
| Mode | `PIXCRAWLER_MODE` | `local` | Operation mode (`local` or `azure`). |
| Poll Interval | `PIXCRAWLER_POLL_INTERVAL_SECONDS` | `60` | Seconds between metric checks. |
| Disk Warn | `PIXCRAWLER_DISK_THRESHOLD_WARN` | `80.0` | Warning threshold for disk usage (%). |
| Disk Alert | `PIXCRAWLER_DISK_THRESHOLD_ALERT` | `90.0` | Alert threshold for disk usage (%). |
| Memory Warn | `PIXCRAWLER_MEMORY_THRESHOLD_WARN` | `80.0` | Warning threshold for memory usage (%). |
| Memory Alert | `PIXCRAWLER_MEMORY_THRESHOLD_ALERT` | `90.0` | Alert threshold for memory usage (%). |
| Chunk Warn | `PIXCRAWLER_CHUNK_THRESHOLD_WARN` | `35` | Warning threshold for active chunks. |
| Chunk Alert | `PIXCRAWLER_CHUNK_THRESHOLD_ALERT` | `40` | Alert threshold for active chunks. |

## How It Works

1.  **Polling Loop**: `service_runner.py` runs a background task that wakes up every `POLL_INTERVAL_SECONDS`.
2.  **Metric Collection**:
    *   **Local**: Calls `monitoring_local.py` to get disk/memory % via `psutil`.
    *   **Azure**: Calls `monitoring_azure.py` to query Azure Monitor API.
    *   **Chunks**: Calls `chunk_tracker.py` to query the database for chunks with `status='processing'`.
3.  **Threshold Evaluation**: `threshold_manager.py` compares metrics against configured limits.
4.  **Alerting**: If thresholds are breached, `alerting.py` logs warnings or errors.
5.  **State Update**: The latest metrics and statuses are stored in memory and exposed via the API.

## Running the Service

### Local Development
Run the service module from the project root:

```bash
python -m backsprout.resource_monitoring.service_runner
```

The service will start on `http://0.0.0.0:8000`.

### Production
The service is designed to run as a sidecar or standalone container. Ensure environment variables are injected securely.

## Testing

### Local Testing
1.  Start the service locally.
2.  Check the health endpoint:
    ```bash
    curl http://localhost:8000/health
    ```
3.  Check metrics:
    ```bash
    curl http://localhost:8000/metrics
    ```
    Response:
    ```json
    {
      "metrics": {
        "disk_pct": 45.2,
        "memory_pct": 62.1,
        "active_chunks": 12
      },
      "statuses": {
        "disk": "OK",
        "memory": "OK",
        "chunks": "OK",
        "overall": "OK"
      },
      "last_updated": "2023-10-27T10:00:00.123456"
    }
    ```

### Simulating Alerts
To test alerting, temporarily lower the thresholds in `.env`:
```ini
PIXCRAWLER_MEMORY_THRESHOLD_WARN=10.0
```
Restart the service and check the logs for `RESOURCE WARNING` messages.

## Notes / Next Steps

*   **Azure Permissions**: Ensure the Managed Identity or Service Principal has `Monitoring Reader` role on the target resource.
*   **Database Access**: The service attempts to use the project's existing `backend` models. If the `backend` package is not installed or configured, it falls back to raw SQL using `PIXCRAWLER_DB_URL`.
*   **Integration**: Configure your external monitoring system (e.g., Prometheus, Datadog) to scrape the `/metrics` endpoint or parse the structured logs.
