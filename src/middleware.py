"""FastAPI middleware: request tracking, performance metrics, CORS setup."""

import time
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from src.config import get_settings
from src.monitoring import (
    ACTIVE_REQUESTS,
    METRICS_AVAILABLE,
    REQUEST_COUNT,
    REQUEST_LATENCY,
)

settings = get_settings()


# ---------------------------------------------------------------------------
# Request ID Middleware
# ---------------------------------------------------------------------------


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to every request/response."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


# ---------------------------------------------------------------------------
# Metrics Middleware
# ---------------------------------------------------------------------------


class MetricsMiddleware(BaseHTTPMiddleware):
    """Record Prometheus metrics for every HTTP request."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if not METRICS_AVAILABLE:
            return await call_next(request)

        ACTIVE_REQUESTS.inc()
        start = time.perf_counter()
        response: Response = Response(status_code=500)
        try:
            response = await call_next(request)
        finally:
            elapsed = time.perf_counter() - start
            endpoint = request.url.path
            method = request.method
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status_code=response.status_code,
            ).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(elapsed)
            ACTIVE_REQUESTS.dec()
        return response


# ---------------------------------------------------------------------------
# Helper to wire all middleware onto the app
# ---------------------------------------------------------------------------


def setup_middleware(app: FastAPI) -> None:
    """Register all middleware on the FastAPI application."""
    # CORS -- must be added first so preflight responses work
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(RequestIDMiddleware)
