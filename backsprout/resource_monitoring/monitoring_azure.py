import os
import time
import logging
import requests
from typing import Optional, List, Dict, Any
from .config import settings

logger = logging.getLogger(__name__)

def _get_token() -> Optional[str]:
    """
    Get Azure access token.
    Tries Managed Identity (IMDS) first, then Service Principal env vars.
    """
    # Try Managed Identity
    try:
        # IMDS endpoint
        resp = requests.get(
            "http://169.254.169.254/metadata/identity/oauth2/token",
            params={"api-version": "2018-02-01", "resource": "https://management.azure.com/"},
            headers={"Metadata": "true"},
            timeout=2
        )
        if resp.status_code == 200:
            return resp.json().get("access_token")
    except requests.RequestException:
        pass # Not on Azure or IMDS not available

    # Fallback to Env Vars
    client_id = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")
    tenant_id = os.getenv("AZURE_TENANT_ID")

    if client_id and client_secret and tenant_id:
        try:
            url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/token"
            data = {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "resource": "https://management.azure.com/"
            }
            resp = requests.post(url, data=data, timeout=5)
            if resp.status_code == 200:
                return resp.json().get("access_token")
            else:
                logger.error(f"Failed to get token from SP: {resp.text}")
        except Exception as e:
            logger.error(f"Error getting token from SP: {e}")
    
    return None

def query_metrics(resource_id: str, metric_names: List[str], timespan: str = "PT5M") -> Optional[Dict[str, float]]:
    """
    Query Azure Monitor metrics and return a dictionary of {metric_name: value}.
    """
    if not resource_id:
        logger.error("No Azure Resource ID provided.")
        return None

    token = _get_token()
    if not token:
        logger.error("Could not obtain Azure access token.")
        return None

    url = f"https://management.azure.com{resource_id}/providers/microsoft.insights/metrics"
    params = {
        "api-version": "2018-01-01",
        "metricnames": ",".join(metric_names),
        "timespan": timespan,
        "aggregation": "Average,Total"
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }

    retries = 3
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                parsed_metrics = {}
                
                # Parse Azure Monitor Response
                # Structure: value -> [ { name: { value: "MetricName" }, timeseries: [ { data: [ { average: 123.4, total: ... } ] } ] } ]
                if "value" in data:
                    for item in data["value"]:
                        metric_name = item.get("name", {}).get("value")
                        if not metric_name:
                            continue
                            
                        timeseries = item.get("timeseries", [])
                        if timeseries and timeseries[0].get("data"):
                            # Get the last data point
                            latest_data = timeseries[0]["data"][-1]
                            # Prefer Average, then Total, then whatever is available
                            val = latest_data.get("average")
                            if val is None:
                                val = latest_data.get("total")
                            
                            if val is not None:
                                parsed_metrics[metric_name] = float(val)
                
                return parsed_metrics
                
            elif resp.status_code == 429: # Rate limit
                time.sleep(2 ** attempt)
                continue
            else:
                logger.error(f"Azure Metric Query Failed: {resp.status_code} - {resp.text}")
                return None
        except requests.RequestException as e:
            logger.error(f"Azure Metric Query Error (Attempt {attempt+1}): {e}")
            time.sleep(2 ** attempt)
    
    return None
