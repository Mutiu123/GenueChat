"""GenueChat -- FastAPI application entry point.

Assembles middleware, exception handlers, routes, Prometheus metrics,
and database lifecycle hooks into a production-ready ASGI application.
"""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from src.config import get_settings
from src.database import get_database
from src.exceptions import register_exception_handlers
from src.middleware import setup_middleware
from src.monitoring import setup_logging

settings = get_settings()
setup_logging()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Application lifespan (startup / shutdown)
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown lifecycle events."""
    logger.info(
        "Starting %s v%s [%s]",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.ENVIRONMENT.value,
    )
    db = get_database()
    try:
        await db.connect()
    except Exception:
        logger.warning("MongoDB unavailable -- running without database")
    yield
    await db.close()
    logger.info("Shutdown complete")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Enterprise RAG chatbot API with JWT authentication, "
        "Prometheus monitoring, and document Q&A capabilities."
    ),
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

# Middleware & error handlers
setup_middleware(app)
register_exception_handlers(app)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

from src.routes.health import router as health_router  # noqa: E402
from src.routes.auth import router as auth_router  # noqa: E402
from src.routes.chat import router as chat_router  # noqa: E402

app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")

# ---------------------------------------------------------------------------
# Prometheus metrics endpoint
# ---------------------------------------------------------------------------

try:
    from prometheus_client import make_asgi_app as _make_metrics_app

    if settings.PROMETHEUS_ENABLED:
        metrics_app = _make_metrics_app()
        app.mount("/metrics", metrics_app)
except ImportError:
    logger.info("prometheus_client not installed -- /metrics disabled")


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------


@app.get("/", tags=["Root"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


# ---------------------------------------------------------------------------
# Custom OpenAPI schema
# ---------------------------------------------------------------------------


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=app.description,
        routes=app.routes,
    )
    schema["info"]["x-logo"] = {"url": "https://example.com/logo.png"}
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Run with uvicorn when executed directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.is_development,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=not settings.is_production,
    )
