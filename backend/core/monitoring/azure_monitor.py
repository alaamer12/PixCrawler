"""Azure Application Insights integration for PixCrawler.

This module provides comprehensive Azure Monitor integration including:
- Application Insights telemetry
- Custom metrics and events
- Request/dependency tracking
- Exception logging
- Performance monitoring

Classes:
    AzureMonitorClient: Azure Application Insights client
    TelemetryProcessor: Custom telemetry processor

Features:
    - Automatic request/response tracking
    - Dependency call tracking (DB, Redis, HTTP)
    - Exception and error tracking
    - Custom events and metrics
    - Sampling for cost optimization
    - Correlation ID tracking
"""

import logging
from typing import Optional, Dict, Any, Callable
from datetime import datetime
import sys

from utility.logging_config import get_logger

__all__ = ['AzureMonitorClient', 'AZURE_MONITOR_AVAILABLE', 'setup_azure_monitor']

logger = get_logger(__name__)

# Try to import Azure Monitor SDK
try:
    from opencensus.ext.azure.log_exporter import AzureLogHandler
    from opencensus.ext.azure.trace_exporter import AzureExporter
    from opencensus.trace.samplers import ProbabilitySampler
    from opencensus.trace import config_integration
    from opencensus.trace.tracer import Tracer
    from opencensus.ext.azure import metrics_exporter
    from opencensus.stats import aggregation as aggregation_module
    from opencensus.stats import measure as measure_module
    from opencensus.stats import stats as stats_module
    from opencensus.stats import view as view_module
    from opencensus.tags import tag_map as tag_map_module
    
    AZURE_MONITOR_AVAILABLE = True
except ImportError:
    AZURE_MONITOR_AVAILABLE = False
    logger.warning(
        "Azure Monitor SDK not installed. "
        "Install with: pip install opencensus-ext-azure"
    )


class AzureMonitorClient:
    """Production-grade Azure Application Insights client.
    
    Provides comprehensive telemetry tracking for FastAPI applications
    with automatic instrumentation and custom event tracking.
    
    Attributes:
        connection_string: Application Insights connection string
        sampling_rate: Telemetry sampling rate (0.0-1.0)
        enabled: Whether monitoring is enabled
        tracer: OpenCensus tracer instance
        stats_recorder: Stats recorder for metrics
    """
    
    def __init__(
        self,
        connection_string: str,
        sampling_rate: float = 1.0,
        log_level: str = "WARNING",
        track_dependencies: bool = True,
        track_requests: bool = True,
        track_exceptions: bool = True,
    ) -> None:
        """Initialize Azure Monitor client.
        
        Args:
            connection_string: Application Insights connection string
            sampling_rate: Telemetry sampling rate (0.0-1.0)
            log_level: Minimum log level to send
            track_dependencies: Track dependency calls
            track_requests: Track HTTP requests
            track_exceptions: Track exceptions
            
        Raises:
            ImportError: If Azure Monitor SDK is not installed
            ValueError: If connection string is invalid
        """
        if not AZURE_MONITOR_AVAILABLE:
            raise ImportError(
                "Azure Monitor SDK not installed. "
                "Install with: pip install opencensus-ext-azure"
            )
        
        if not connection_string:
            raise ValueError("Connection string cannot be empty")
        
        if not 0.0 <= sampling_rate <= 1.0:
            raise ValueError("Sampling rate must be between 0.0 and 1.0")
        
        self.connection_string = connection_string
        self.sampling_rate = sampling_rate
        self.enabled = True
        
        try:
            # Setup trace exporter
            self.trace_exporter = AzureExporter(
                connection_string=connection_string
            )
            
            # Setup tracer with sampling
            sampler = ProbabilitySampler(rate=sampling_rate)
            self.tracer = Tracer(
                exporter=self.trace_exporter,
                sampler=sampler
            )
            
            # Setup metrics exporter
            self.metrics_exporter = metrics_exporter.new_metrics_exporter(
                connection_string=connection_string
            )
            
            # Setup stats recorder
            self.stats = stats_module.stats
            self.view_manager = self.stats.view_manager
            self.stats_recorder = self.stats.stats_recorder
            
            # Configure integrations
            if track_dependencies:
                config_integration.trace_integrations(['requests', 'sqlalchemy'])
            
            if track_requests:
                config_integration.trace_integrations(['fastapi'])
            
            # Setup logging handler
            log_handler = AzureLogHandler(connection_string=connection_string)
            log_handler.setLevel(getattr(logging, log_level.upper()))
            
            # Add to root logger
            root_logger = logging.getLogger()
            root_logger.addHandler(log_handler)
            
            logger.info(
                f"Initialized Azure Monitor: sampling={sampling_rate}, "
                f"log_level={log_level}"
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize Azure Monitor: {e}")
            self.enabled = False
            raise
    
    def track_event(
        self,
        name: str,
        properties: Optional[Dict[str, Any]] = None,
        measurements: Optional[Dict[str, float]] = None,
    ) -> None:
        """Track a custom event.
        
        Args:
            name: Event name
            properties: Event properties (string key-value pairs)
            measurements: Event measurements (numeric key-value pairs)
        """
        if not self.enabled:
            return
        
        try:
            with self.tracer.span(name=name) as span:
                if properties:
                    for key, value in properties.items():
                        span.add_attribute(key, str(value))
                
                if measurements:
                    for key, value in measurements.items():
                        span.add_attribute(f"measurement.{key}", value)
            
            logger.debug(f"Tracked event: {name}")
            
        except Exception as e:
            logger.error(f"Failed to track event {name}: {e}")
    
    def track_metric(
        self,
        name: str,
        value: float,
        properties: Optional[Dict[str, str]] = None,
    ) -> None:
        """Track a custom metric.
        
        Args:
            name: Metric name
            value: Metric value
            properties: Metric properties (tags)
        """
        if not self.enabled:
            return
        
        try:
            # Create measure
            measure = measure_module.MeasureFloat(
                name=name,
                description=f"Custom metric: {name}",
                unit="1"
            )
            
            # Create view
            view = view_module.View(
                name=f"{name}_view",
                description=f"View for {name}",
                columns=[],
                measure=measure,
                aggregation=aggregation_module.LastValueAggregation()
            )
            
            # Register view
            self.view_manager.register_view(view)
            
            # Record measurement
            mmap = self.stats_recorder.new_measurement_map()
            tmap = tag_map_module.TagMap()
            
            if properties:
                for key, value in properties.items():
                    tmap.insert(key, value)
            
            mmap.measure_float_put(measure, value)
            mmap.record(tmap)
            
            logger.debug(f"Tracked metric: {name}={value}")
            
        except Exception as e:
            logger.error(f"Failed to track metric {name}: {e}")
    
    def track_exception(
        self,
        exception: Exception,
        properties: Optional[Dict[str, Any]] = None,
        measurements: Optional[Dict[str, float]] = None,
    ) -> None:
        """Track an exception.
        
        Args:
            exception: Exception instance
            properties: Exception properties
            measurements: Exception measurements
        """
        if not self.enabled:
            return
        
        try:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            
            with self.tracer.span(name="exception") as span:
                span.add_attribute("exception.type", type(exception).__name__)
                span.add_attribute("exception.message", str(exception))
                
                if properties:
                    for key, value in properties.items():
                        span.add_attribute(key, str(value))
                
                if measurements:
                    for key, value in measurements.items():
                        span.add_attribute(f"measurement.{key}", value)
            
            logger.debug(f"Tracked exception: {type(exception).__name__}")
            
        except Exception as e:
            logger.error(f"Failed to track exception: {e}")
    
    def track_request(
        self,
        name: str,
        url: str,
        duration: float,
        response_code: int,
        success: bool,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Track an HTTP request.
        
        Args:
            name: Request name
            url: Request URL
            duration: Request duration in seconds
            response_code: HTTP response code
            success: Whether request was successful
            properties: Request properties
        """
        if not self.enabled:
            return
        
        try:
            with self.tracer.span(name=name) as span:
                span.add_attribute("http.url", url)
                span.add_attribute("http.status_code", response_code)
                span.add_attribute("http.duration", duration)
                span.add_attribute("http.success", success)
                
                if properties:
                    for key, value in properties.items():
                        span.add_attribute(key, str(value))
            
            logger.debug(f"Tracked request: {name} ({response_code})")
            
        except Exception as e:
            logger.error(f"Failed to track request {name}: {e}")
    
    def track_dependency(
        self,
        name: str,
        dependency_type: str,
        target: str,
        duration: float,
        success: bool,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Track a dependency call.
        
        Args:
            name: Dependency name
            dependency_type: Type (SQL, HTTP, Redis, etc.)
            target: Dependency target (server, endpoint)
            duration: Call duration in seconds
            success: Whether call was successful
            properties: Dependency properties
        """
        if not self.enabled:
            return
        
        try:
            with self.tracer.span(name=name) as span:
                span.add_attribute("dependency.type", dependency_type)
                span.add_attribute("dependency.target", target)
                span.add_attribute("dependency.duration", duration)
                span.add_attribute("dependency.success", success)
                
                if properties:
                    for key, value in properties.items():
                        span.add_attribute(key, str(value))
            
            logger.debug(f"Tracked dependency: {name} ({dependency_type})")
            
        except Exception as e:
            logger.error(f"Failed to track dependency {name}: {e}")
    
    def flush(self) -> None:
        """Flush all pending telemetry."""
        if not self.enabled:
            return
        
        try:
            self.tracer.exporter.export(self.tracer.span_context)
            logger.debug("Flushed Azure Monitor telemetry")
        except Exception as e:
            logger.error(f"Failed to flush telemetry: {e}")


def setup_azure_monitor(
    connection_string: str,
    sampling_rate: float = 1.0,
    log_level: str = "WARNING",
    track_dependencies: bool = True,
    track_requests: bool = True,
    track_exceptions: bool = True,
) -> Optional[AzureMonitorClient]:
    """Setup Azure Monitor for the application.
    
    Args:
        connection_string: Application Insights connection string
        sampling_rate: Telemetry sampling rate (0.0-1.0)
        log_level: Minimum log level to send
        track_dependencies: Track dependency calls
        track_requests: Track HTTP requests
        track_exceptions: Track exceptions
        
    Returns:
        AzureMonitorClient instance or None if setup fails
    """
    if not AZURE_MONITOR_AVAILABLE:
        logger.warning("Azure Monitor SDK not available, skipping setup")
        return None
    
    if not connection_string:
        logger.warning("No Azure Monitor connection string provided, skipping setup")
        return None
    
    try:
        client = AzureMonitorClient(
            connection_string=connection_string,
            sampling_rate=sampling_rate,
            log_level=log_level,
            track_dependencies=track_dependencies,
            track_requests=track_requests,
            track_exceptions=track_exceptions,
        )
        logger.info("Azure Monitor setup completed successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to setup Azure Monitor: {e}")
        return None