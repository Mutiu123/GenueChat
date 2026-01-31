"""Prometheus metrics, structured JSON logging, and audit helpers."""

import json
import logging
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.config import get_settings

settings = get_settings()

# ---------------------------------------------------------------------------
# Structured JSON Logging
# ---------------------------------------------------------------------------


class JSONFormatter(logging.Formatter):
    """Custom formatter that emits structured JSON log lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, default=str)


def setup_logging() -> None:
    """Configure root logger with structured JSON output."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    # Remove existing handlers to avoid duplicate output
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root.addHandler(handler)
    # Quieten noisy third-party loggers
    for name in ("uvicorn.access", "motor", "pymongo"):
        logging.getLogger(name).setLevel(logging.WARNING)


# ---------------------------------------------------------------------------
# Prometheus Metrics
# ---------------------------------------------------------------------------

try:
    from prometheus_client import Counter, Gauge, Histogram, Info

    REQUEST_COUNT = Counter(
        f"{settings.METRICS_PREFIX}_http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status_code"],
    )
    REQUEST_LATENCY = Histogram(
        f"{settings.METRICS_PREFIX}_http_request_duration_seconds",
        "HTTP request latency in seconds",
        ["method", "endpoint"],
        buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    )
    ACTIVE_REQUESTS = Gauge(
        f"{settings.METRICS_PREFIX}_active_requests",
        "Number of in-flight requests",
    )
    CHAT_PREDICTIONS = Counter(
        f"{settings.METRICS_PREFIX}_chat_predictions_total",
        "Total chat predictions made",
        ["source"],
    )
    CHAT_LATENCY = Histogram(
        f"{settings.METRICS_PREFIX}_chat_prediction_duration_seconds",
        "Chat prediction latency",
        ["source"],
        buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
    )
    DOCUMENT_UPLOADS = Counter(
        f"{settings.METRICS_PREFIX}_document_uploads_total",
        "Total document uploads",
    )
    DOCUMENT_PROCESSING_TIME = Histogram(
        f"{settings.METRICS_PREFIX}_document_processing_seconds",
        "Time to process uploaded documents",
        buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
    )
    DB_OPERATIONS = Counter(
        f"{settings.METRICS_PREFIX}_db_operations_total",
        "Total database operations",
        ["operation", "collection"],
    )
    AUTH_EVENTS = Counter(
        f"{settings.METRICS_PREFIX}_auth_events_total",
        "Authentication events",
        ["event"],
    )
    ERROR_COUNT = Counter(
        f"{settings.METRICS_PREFIX}_errors_total",
        "Total errors by type",
        ["error_type"],
    )
    APP_INFO = Info(
        f"{settings.METRICS_PREFIX}_app",
        "Application metadata",
    )
    APP_INFO.info(
        {
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT.value,
        }
    )
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False


# ---------------------------------------------------------------------------
# Audit Logging Helper
# ---------------------------------------------------------------------------


audit_logger = logging.getLogger("genuechat.audit")


def log_audit_event(
    event_type: str,
    *,
    request_id: Optional[str] = None,
    user: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> None:
    """Write a structured audit log entry."""
    entry = {
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "user": user,
        "payload": payload or {},
    }
    audit_logger.info(json.dumps(entry, default=str))


def log_prediction_audit(
    *,
    request_id: Optional[str] = None,
    question: str,
    answer: str,
    model: str,
    processing_time_ms: float,
    source: str = "chat",
) -> None:
    """Audit-log a prediction event and bump Prometheus counters."""
    log_audit_event(
        "prediction",
        request_id=request_id,
        payload={
            "question": question[:200],
            "answer_length": len(answer),
            "model": model,
            "processing_time_ms": processing_time_ms,
            "source": source,
        },
    )
    if METRICS_AVAILABLE:
        CHAT_PREDICTIONS.labels(source=source).inc()
        CHAT_LATENCY.labels(source=source).observe(processing_time_ms / 1000)
