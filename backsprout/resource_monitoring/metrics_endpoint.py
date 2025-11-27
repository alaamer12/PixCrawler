import datetime
from fastapi import FastAPI
from typing import Dict, Any

app = FastAPI(title="Resource Monitoring Service")

# In-memory state
current_state: Dict[str, Any] = {
    "metrics": {},
    "statuses": {},
    "last_updated": None
}

def update_state(metrics: Dict[str, Any], statuses: Dict[str, str]):
    """Update the shared state."""
    current_state["metrics"] = metrics
    current_state["statuses"] = statuses
    current_state["last_updated"] = datetime.datetime.now().isoformat()

@app.get("/metrics")
async def get_metrics():
    """Return the latest computed metrics and statuses."""
    return current_state

@app.get("/health")
async def health_check():
    """Simple health check."""
    return {"status": "healthy"}
