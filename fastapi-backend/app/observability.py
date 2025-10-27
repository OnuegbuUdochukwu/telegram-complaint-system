"""Observability module for logging, metrics, and error tracking."""

import logging
import json
import sys
import os
from typing import Any, Dict
from datetime import datetime
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
import time

# Prometheus metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'Duration of HTTP requests in seconds',
    ['method', 'endpoint']
)

active_complaints = Gauge(
    'active_complaints_total',
    'Total number of active complaints',
    ['status']
)

active_websocket_connections = Gauge(
    'websocket_connections_active',
    'Number of active WebSocket connections',
    ['role']
)


def setup_logging() -> None:
    """Configure structured JSON logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Configure root logger to output JSON
    class JSONFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            log_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }
            
            # Add exception info if present
            if record.exc_info:
                log_data['exception'] = self.formatException(record.exc_info)
            
            # Add extra fields if present
            if hasattr(record, 'extra'):
                log_data.update(record.extra)
            
            return json.dumps(log_data)
    
    # Replace default formatter with JSON formatter
    for handler in logging.getLogger().handlers:
        handler.setFormatter(JSONFormatter())
    
    # Configure specific loggers
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)
    
    logger.info("Structured JSON logging configured")


def init_sentry() -> None:
    """Initialize Sentry error tracking."""
    try:
        sentry_dsn = os.getenv("SENTRY_DSN")
        environment = os.getenv("ENVIRONMENT", "development")
        
        if sentry_dsn:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
            
            sentry_sdk.init(
                dsn=sentry_dsn,
                environment=environment,
                integrations=[
                    FastApiIntegration(),
                    SqlalchemyIntegration(),
                ],
                traces_sample_rate=0.1,
                profiles_sample_rate=0.1,
            )
            logging.info("Sentry initialized successfully", extra={"dsn": sentry_dsn[:20] + "..."})
        else:
            logging.info("Sentry DSN not configured, skipping initialization")
    except ImportError:
        logging.warning("sentry-sdk not installed, skipping Sentry initialization")
    except Exception as e:
        logging.error(f"Failed to initialize Sentry: {e}")


def setup_metrics_middleware(app):
    """Add Prometheus metrics middleware to FastAPI app."""
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Record metrics
        duration = time.time() - start_time
        
        # Extract endpoint (simplified to route path)
        endpoint = request.url.path
        method = request.method
        status = response.status_code
        
        # Record metrics
        http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
        
        return response


def metrics_endpoint(request: Request) -> Response:
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


def get_health_check() -> Dict[str, Any]:
    """Get health check information including metrics."""
    try:
        # Try to get connection count from WebSocket manager
        from .websocket_manager import manager
        connection_count = manager.get_connection_count()
        connections_by_role = manager.get_connections_by_role()
    except Exception:
        connection_count = 0
        connections_by_role = {}
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "websocket_connections": connection_count,
        "websocket_by_role": connections_by_role
    }

